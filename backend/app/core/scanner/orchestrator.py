"""LangGraph-based Scan Orchestrator.

Replaces the sequential ScanOrchestrator with a StateGraph where an LLM Agent
dynamically decides which tools to invoke and in what order.
"""
import os
import json
import tempfile
import asyncio
from typing import TypedDict, Annotated, List, Optional, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.core.scanner.tools import ALL_TOOLS
from app.core.scanner.semgrep import SemgrepScanner
from app.core.scanner.bandit import BanditScanner
from app.core.scanner.ai_scanner import AIScanner
from app.config import settings


class ScanState(TypedDict):
    """State passed between graph nodes."""
    # Input
    repo_url: str
    language: str
    scan_id: int
    
    # Runtime
    repo_dir: str
    files: List[dict]
    current_file: Optional[dict]
    
    # Messages for LLM
    messages: List[BaseMessage]
    
    # Results accumulation
    all_findings: List[dict]
    tool_calls_log: List[dict]
    
    # Control
    step: int
    max_steps: int
    status: Literal["running", "completed", "failed"]
    error: Optional[str]
    archived_path: str


class LangGraphScanOrchestrator:
    """LLM-driven scan orchestrator using LangGraph."""
    
    def __init__(self):
        self._llm = None
        self._graph = None
        self._checkpointer = None
    
    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=settings.QWEN_MODEL or "qwen-plus",
                base_url=settings.QWEN_BASE_URL,
                api_key=settings.QWEN_API_KEY,
                temperature=0.1,
            ).bind_tools(ALL_TOOLS)
        return self._llm
    
    @property
    def graph(self):
        if self._graph is None:
            self._checkpointer = MemorySaver()
            self._graph = self._build_graph()
        return self._graph
    
    @property
    def checkpointer(self):
        if self._checkpointer is None:
            self._checkpointer = MemorySaver()
        return self._checkpointer
    
    def _build_graph(self) -> StateGraph:
        """Build the StateGraph for scan orchestration."""
        g = StateGraph(ScanState)
        
        # Nodes
        g.add_node("init", self._init_node)
        g.add_node("agent", self._agent_node)
        g.add_node("tools", self._tools_node)
        g.add_node("finalize", self._finalize_node)
        
        # Edges
        g.set_entry_point("init")
        g.add_edge("init", "agent")
        g.add_conditional_edges(
            "agent",
            self._route_after_agent,
            {
                "tools": "tools",
                "finalize": "finalize",
            }
        )
        g.add_edge("tools", "agent")
        g.add_edge("finalize", END)
        
        return g.compile(checkpointer=self.checkpointer)
    
    async def _init_node(self, state: ScanState) -> ScanState:
        """Clone repo and list source files."""
        repo_url = state["repo_url"]
        language = state["language"]
        scan_id = state["scan_id"]
        
        tmpdir = tempfile.mkdtemp(prefix=f"sast_scan_{scan_id}_")
        repo_dir = os.path.join(tmpdir, "repo")
        
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth", "1", repo_url, repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return {**state, "status": "failed", "error": f"Git clone failed: {stderr.decode()}"}
        
        # List files using the tool
        list_tool = next(t for t in ALL_TOOLS if t.name == "list_source_files")
        result = await list_tool.ainvoke({"repo_dir": repo_dir, "language": language})
        files = result.get("files", [])
        
        return {
            **state,
            "repo_dir": repo_dir,
            "files": files,
            "messages": [],
            "all_findings": [],
            "tool_calls_log": [],
            "step": 0,
            "max_steps": 20,
            "status": "running",
        }
    
    async def _agent_node(self, state: ScanState) -> ScanState:
        """LLM Agent decides next action."""
        if state["step"] >= state["max_steps"]:
            return {**state, "status": "completed"}
        
        # Build context
        files_info = "\n".join(
            f"  - {f['rel_path']} ({f['size']} bytes)" for f in state["files"][:15]
        )
        findings_count = len(state["all_findings"])
        by_sev = {}
        for f in state["all_findings"]:
            sev = f.get("severity", "UNKNOWN")
            by_sev[sev] = by_sev.get(sev, 0) + 1
        sev_summary = ", ".join(f"{k}:{v}" for k,v in by_sev.items()) if by_sev else "无"
        
        system_prompt = f"""你是代码安全扫描编排 Agent。任务：扫描 {state['language']} 项目，发现安全漏洞。

=== 当前状态 ===
扫描ID: {state['scan_id']}
仓库: {state['repo_dir']}
源文件数: {len(state['files'])} (显示前15个)
{files_info}

已发现漏洞: {findings_count} 个 ({sev_summary})
步骤: {state['step']}/{state['max_steps']}

=== 可用工具 ===
1. read_file - 读取文件内容
2. semgrep_scan - 多语言模式匹配扫描（快、覆盖面广，推荐优先全量跑）
3. bandit_scan - Python 专用深度扫描（仅 Python 项目）
4. gitleaks_scan - 硬编码密钥/密码/Token 检测（全语言，必跑）
5. trivy_scan - 依赖库 CVE 扫描（npm/pip/maven/go，必跑）
6. ai_scan - LLM 深度分析（贵、慢，仅对高风险文件使用，单次扫描不超过 5 个文件）

=== 策略建议 ===
- 第 1 步：跑 gitleaks_scan（全目录）+ trivy_scan（全目录），快速发现密钥泄露和依赖 CVE
- 第 2 步：对前 10 个文件并行跑 semgrep_scan，建立代码漏洞基线
- 第 3 步：如果是 Python，跑一次 bandit_scan（整个目录）
- 第 4 步：筛选 critical/high 发现的文件，或核心模块（auth、crypto、sql），逐个 ai_scan
- 单次扫描控制在 15 步内，AI 扫描不超过 5 文件

请决定下一步动作，必须调用工具。"""
        
        messages = [SystemMessage(content=system_prompt)]
        if state["messages"]:
            messages.extend(state["messages"][-4:])  # Keep last 4 messages for context
        
        response = await self.llm.ainvoke(messages)
        
        # Log the decision
        tool_calls = response.tool_calls if hasattr(response, "tool_calls") else []
        log_entry = {
            "step": state["step"],
            "timestamp": datetime.utcnow().isoformat(),
            "thinking": response.content if isinstance(response.content, str) else str(response.content),
            "tool_calls": [{"name": tc["name"], "args": tc["args"]} for tc in tool_calls],
        }
        
        return {
            **state,
            "step": state["step"] + 1,
            "messages": state["messages"] + [response],
            "tool_calls_log": state["tool_calls_log"] + [log_entry],
        }
    
    def _route_after_agent(self, state: ScanState) -> str:
        """Route based on whether LLM made tool calls."""
        last_msg = state["messages"][-1] if state["messages"] else None
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            return "tools"
        return "finalize"
    
    async def _tools_node(self, state: ScanState) -> ScanState:
        """Execute tool calls from LLM."""
        last_msg = state["messages"][-1]
        tool_calls = last_msg.tool_calls
        
        tool_messages = []
        new_findings = []
        
        for call in tool_calls:
            tool_name = call["name"]
            args = call["args"]
            call_id = call["id"]
            
            # Inject repo_dir for file operations
            if tool_name in ("read_file", "semgrep_scan") and "repo_dir" in state:
                if "file_path" in args and not os.path.isabs(args["file_path"]):
                    args["file_path"] = os.path.join(state["repo_dir"], args["file_path"])
            if tool_name == "bandit_scan" and "repo_dir" in state:
                args["repo_dir"] = state["repo_dir"]
            
            # Execute tool
            tool_map = {t.name: t for t in ALL_TOOLS}
            if tool_name not in tool_map:
                result = {"error": f"Unknown tool: {tool_name}"}
            else:
                try:
                    result = await tool_map[tool_name].ainvoke(args)
                except Exception as e:
                    result = {"error": str(e), "tool": tool_name}
            
            # Extract findings
            if isinstance(result, dict) and "findings" in result:
                for f in result["findings"]:
                    f["_tool"] = tool_name
                    f["_scan_id"] = state["scan_id"]
                new_findings.extend(result["findings"])
            
            # Create tool message for LLM
            tool_messages.append(ToolMessage(
                content=json.dumps(result, ensure_ascii=False)[:2000],
                tool_call_id=call_id,
                name=tool_name,
            ))
            
            # Update log
            if state["tool_calls_log"]:
                state["tool_calls_log"][-1].setdefault("tool_results", []).append({
                    "tool": tool_name,
                    "args": args,
                    "result_summary": {k: v for k, v in result.items() if k != "findings"},
                })
        
        return {
            **state,
            "messages": state["messages"] + tool_messages,
            "all_findings": state["all_findings"] + new_findings,
        }
    
    async def _finalize_node(self, state: ScanState) -> ScanState:
        """Finalize scan, archive sample code for comparison."""
        repo_dir = state.get("repo_dir")
        archived_path = ""
        if repo_dir and os.path.exists(repo_dir):
            try:
                import shutil
                samples_dir = "/data/ai-sast/samples"
                os.makedirs(samples_dir, exist_ok=True)
                repo_name = state.get("repo_url", "repo").rstrip("/").split("/")[-1].replace(".git", "")
                archived_path = os.path.join(samples_dir, f"scan{state['scan_id']}_{repo_name}")
                if os.path.exists(archived_path):
                    shutil.rmtree(archived_path)
                shutil.move(repo_dir, archived_path)
                shutil.rmtree(os.path.dirname(repo_dir), ignore_errors=True)
            except Exception:
                archived_path = repo_dir
        
        # Deduplicate findings (simple version)
        seen = set()
        unique = []
        for f in state["all_findings"]:
            key = (f.get("path"), f.get("start_line"), f.get("check_id"))
            if key not in seen:
                seen.add(key)
                unique.append(f)
        
        return {
            **state,
            "status": "completed",
            "all_findings": unique,
            "archived_path": archived_path,
        }
    
    async def scan_project(self, repo_url: str, language: str, scan_id: int) -> dict:
        """Run the full scan workflow."""
        config = {"configurable": {"thread_id": f"scan-{scan_id}"}}
        
        initial_state = {
            "repo_url": repo_url,
            "language": language,
            "scan_id": scan_id,
        }
        
        final_state = await self.graph.ainvoke(initial_state, config)
        
        return {
            "findings": final_state.get("all_findings", []),
            "total": len(final_state.get("all_findings", [])),
            "files_scanned": len(final_state.get("files", [])),
            "tool_calls_log": final_state.get("tool_calls_log", []),
            "archived_path": final_state.get("archived_path", ""),
        }
    
    async def scan_code(self, code: str, language: str = "python", file_path: str = "") -> dict:
        """Scan inline code (fallback for non-project scans)."""
        # For inline code, just run semgrep + ai (if python, bandit)
        findings = []
        
        semgrep_results = await _get_semgrep().scan(code, language)
        for r in semgrep_results:
            findings.append({
                "check_id": r.get("check_id", ""),
                "path": file_path or "inline",
                "start_line": r.get("start_line", 0),
                "end_line": r.get("end_line", 0),
                "message": r.get("message", ""),
                "severity": r.get("severity", "WARNING").upper(),
                "source": "semgrep",
            })
        
        if language == "python" and file_path and os.path.exists(file_path):
            bandit_results = await _get_bandit().scan_file(file_path)
            findings.extend(bandit_results)
        
        ai_result = await _get_ai().analyze_code(code, language)
        for v in ai_result.get("vulnerabilities", []):
            findings.append({
                "check_id": v.get("type", ""),
                "path": file_path or "inline",
                "start_line": v.get("line", 0),
                "end_line": v.get("line", 0),
                "message": v.get("description", ""),
                "severity": v.get("severity", "medium").upper(),
                "remediation": v.get("remediation", ""),
                "confidence": v.get("confidence", 50),
                "source": "ai",
            })
        
        return {"findings": findings, "total": len(findings)}


# Backward compatibility: keep the old class name as alias
ScanOrchestrator = LangGraphScanOrchestrator

# Lazy-init for inline code scanning (backward compat)
_semgrep = None
_bandit = None
_ai = None

def _get_semgrep():
    global _semgrep
    if _semgrep is None:
        _semgrep = SemgrepScanner()
    return _semgrep

def _get_bandit():
    global _bandit
    if _bandit is None:
        _bandit = BanditScanner()
    return _bandit

def _get_ai():
    global _ai
    if _ai is None:
        _ai = AIScanner()
    return _ai