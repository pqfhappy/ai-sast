"""LangGraph-based Scan Orchestrator.

Replaces the sequential ScanOrchestrator with a StateGraph where an LLM Agent
dynamically decides which tools to invoke and in what order.
"""
import os
import tempfile
import asyncio
import json
from typing import TypedDict, Annotated, List, Optional, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.core.scanner.tools import ALL_TOOLS, semgrep_scan, bandit_scan, ai_scan, list_source_files, read_file
from app.core.config import settings


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
    
    # Results accumulation
    all_findings: List[dict]
    tool_calls_log: List[dict]
    
    # Control
    step: int
    max_steps: int
    status: Literal["running", "completed", "failed"]
    error: Optional[str]


class ScanAgent:
    """LLM-driven scan agent using LangGraph."""
    
    def __init__(self, scan_id: int):
        self.scan_id = scan_id
        self.llm = ChatOpenAI(
            model=settings.QWEN_MODEL or "qwen-plus",
            base_url=settings.QWEN_BASE_URL,
            api_key=settings.QWEN_API_KEY,
            temperature=0.1,
        ).bind_tools(ALL_TOOLS)
        
        self.graph = self._build_graph()
        self.checkpointer = MemorySaver()
    
    def _build_graph(self) -> StateGraph:
        """Build the StateGraph for scan orchestration."""
        g = StateGraph(ScanState)
        
        # Nodes
        g.add_node("init", self._init_node)
        g.add_node("plan", self._plan_node)
        g.add_node("execute_tool", self._execute_tool_node)
        g.add_node("aggregate", self._aggregate_node)
        g.add_node("finalize", self._finalize_node)
        
        # Edges
        g.set_entry_point("init")
        g.add_edge("init", "plan")
        g.add_conditional_edges(
            "plan",
            self._route_after_plan,
            {
                "execute": "execute_tool",
                "aggregate": "aggregate",
                "finalize": "finalize",
            }
        )
        g.add_edge("execute_tool", "plan")
        g.add_edge("aggregate", "plan")
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
        
        # List files
        result = await list_source_files.ainvoke({"repo_dir": repo_dir, "language": language})
        files = result.get("files", [])
        
        return {
            **state,
            "repo_dir": repo_dir,
            "files": files,
            "all_findings": [],
            "tool_calls_log": [],
            "step": 0,
            "max_steps": 20,
            "status": "running",
        }
    
    async def _plan_node(self, state: ScanState) -> ScanState:
        """LLM decides next action based on current state."""
        if state["step"] >= state["max_steps"]:
            return {**state, "status": "completed"}
        
        # Build context for LLM
        files_info = "\n".join(
            f"  - {f['rel_path']} ({f['size']} bytes)" for f in state["files"][:10]
        )
        findings_summary = f"Total findings so far: {len(state['all_findings'])}"
        if state["all_findings"]:
            by_sev = {}
            for f in state["all_findings"]:
                by_sev[f.get("severity", "UNKNOWN")] = by_sev.get(f.get("severity", "UNKNOWN"), 0) + 1
            findings_summary += f" ({', '.join(f'{k}:{v}' for k,v in by_sev.items())})"
        
        prompt = f"""你是一个代码安全扫描编排 Agent。当前任务：扫描 {state['language']} 项目，发现安全漏洞。

=== 当前状态 ===
扫描ID: {state['scan_id']}
仓库目录: {state['repo_dir']}
源文件数: {len(state['files'])} (显示前10个)
{files_info}

{findings_summary}
步骤: {state['step']}/{state['max_steps']}

=== 可用工具 ===
1. list_source_files - 列出更多文件（已执行）
2. read_file - 读取指定文件内容
3. semgrep_scan - 多语言模式匹配扫描（快、覆盖面广）
4. bandit_scan - Python 专用安全扫描（深）
5. ai_scan - LLM 深度分析（贵、慢、但能发现逻辑漏洞）

=== 策略建议 ===
- 先用 semgrep_scan 快速全量扫描，获取基线
- 对 Python 文件补充 bandit_scan
- 仅对高风险文件（semgrep 发现 critical/high、或核心模块）使用 ai_scan
- 单次扫描控制在 10 个文件内，避免成本失控

请决定下一步动作："""

        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        tool_calls = response.tool_calls if hasattr(response, "tool_calls") else []
        
        # Log the decision
        log_entry = {
            "step": state["step"],
            "timestamp": datetime.utcnow().isoformat(),
            "thinking": response.content if isinstance(response.content, str) else str(response.content),
            "tool_calls": tool_calls,
        }
        
        return {
            **state,
            "step": state["step"] + 1,
            "tool_calls_log": state["tool_calls_log"] + [log_entry],
            "_llm_response": response,
            "_tool_calls": tool_calls,
        }
    
    def _route_after_plan(self, state: ScanState) -> str:
        """Route based on LLM's tool calls."""
        tool_calls = state.get("_tool_calls", [])
        if not tool_calls:
            # No tool calls = LLM thinks we're done
            return "finalize"
        return "execute"
    
    async def _execute_tool_node(self, state: ScanState) -> ScanState:
        """Execute the tool calls from LLM."""
        tool_calls = state.get("_tool_calls", [])
        new_findings = []
        
        for call in tool_calls:
            tool_name = call["name"]
            args = call["args"]
            
            # Inject repo_dir for file operations
            if tool_name in ("read_file", "bandit_scan") and "repo_dir" in state:
                if "file_path" in args and not os.path.isabs(args["file_path"]):
                    args["file_path"] = os.path.join(state["repo_dir"], args["file_path"])
            
            # Execute tool
            tool_map = {t.name: t for t in ALL_TOOLS}
            if tool_name not in tool_map:
                continue
            
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
            
            # Log execution
            state["tool_calls_log"][-1]["tool_results"] = state["tool_calls_log"][-1].get("tool_results", []) + [{
                "tool": tool_name,
                "args": args,
                "result_summary": {k: v for k, v in result.items() if k != "findings"},
            }]
        
        return {
            **state,
            "all_findings": state["all_findings"] + new_findings,
        }
    
    async def _aggregate_node(self, state: ScanState) -> ScanState:
        """Aggregate findings from multiple tools on same file (deduplication placeholder)."""
        # TODO: Implement deduplication logic here
        return state
    
    async def _finalize_node(self, state: ScanState) -> ScanState:
        """Finalize and return results."""
        # Clean up temp directory
        if state.get("repo_dir"):
            import shutil
            try:
                shutil.rmtree(os.path.dirname(state["repo_dir"]), ignore_errors=True)
            except Exception:
                pass
        
        return {
            **state,
            "status": "completed",
            "total": len(state["all_findings"]),
        }
    
    async def run(self, repo_url: str, language: str) -> dict:
        """Run the scan workflow."""
        initial_state: ScanState = {
            "repo_url": repo_url,
            "language": language,
            "scan_id": self.scan_id,
            "repo_dir": "",
            "files": [],
            "current_file": None,
            "all_findings": [],
            "tool_calls_log": [],
            "step": 0,
            "max_steps": 20,
            "status": "running",
            "error": None,
        }
        
        config = {"configurable": {"thread_id": f"scan-{self.scan_id}"}}
        final_state = await self.graph.ainvoke(initial_state, config)
        
        return {
            "findings": final_state.get("all_findings", []),
            "total": final_state.get("total", 0),
            "tool_calls_log": final_state.get("tool_calls_log", []),
            "status": final_state.get("status", "unknown"),
            "error": final_state.get("error"),
        }


async def scan_project_langgraph(repo_url: str, language: str, scan_id: int) -> dict:
    """Entry point for API to use LangGraph orchestrator."""
    agent = ScanAgent(scan_id)
    return await agent.run(repo_url, language)