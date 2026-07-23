"""LangChain Tools wrapping SAST scanners.

Each scanner is exposed as a LangChain tool so the Agent can invoke them dynamically.
"""
import os
import json
import asyncio
from pathlib import Path
from typing import Optional, List
from langchain_core.tools import tool

from app.core.scanner.semgrep import SemgrepScanner
from app.core.scanner.bandit import BanditScanner
from app.core.scanner.ai_scanner import AIScanner

# Lazy-initialize scanner instances (avoid crash at import time if API key missing)
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

# Language -> extensions mapping
EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx", ".ts", ".tsx"],
    "java": [".java"],
    "php": [".php"],
    "go": [".go"],
    "rust": [".rs"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".hpp", ".cc", ".hh"],
}

SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "env", "dist", "build", ".eggs", "target", "vendor"}
MAX_FILES = 50
MAX_CHARS_PER_FILE = 20000


@tool
async def semgrep_scan(repo_dir: str, language: str, file_pattern: Optional[str] = None) -> dict:
    """Run Semgrep scan on a directory or specific file.
    
    Best for: multi-language pattern matching, OWASP Top 10, custom rules.
    Fast and broad coverage. Use first for baseline.
    
    Args:
        repo_dir: Repository root directory
        language: Programming language
        file_pattern: Optional glob pattern (e.g., "**/*.py")
    
    Returns: {"findings": [...], "total": N, "files_scanned": M}
    """
    try:
        # Build command
        cmd = ["semgrep", "--lang", language, "--json"]
        if file_pattern:
            cmd.append(file_pattern)
        else:
            cmd.append(repo_dir)
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode not in (0, 1):  # 1 = findings found
            return {"findings": [], "total": 0, "error": stderr.decode()[:500]}
        
        results = json.loads(stdout) if stdout else {"results": []}
        findings = _parse_semgrep(results, repo_dir)
        
        return {"findings": findings, "total": len(findings), "files_scanned": len(set(f["path"] for f in findings))}
    except FileNotFoundError:
        return {"findings": [], "total": 0, "error": "semgrep not installed"}
    except Exception as e:
        return {"findings": [], "total": 0, "error": str(e)}


@tool
async def bandit_scan(repo_dir: str, file_path: Optional[str] = None) -> dict:
    """Run Bandit security linter on Python files.
    
    Best for: Python-specific issues (hardcoded secrets, shell injection, etc).
    Deep but Python-only. Use after semgrep for Python projects.
    
    Args:
        repo_dir: Repository root (for recursive scan with -r)
        file_path: Optional specific file to scan
    
    Returns: {"findings": [...], "total": N}
    """
    try:
        target = file_path if file_path else repo_dir
        cmd = ["bandit", "-f", "json", "-r", target]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode not in (0, 1):
            return {"findings": [], "total": 0, "error": stderr.decode()[:500]}
        
        results = json.loads(stdout) if stdout else {"results": []}
        findings = _parse_bandit(results)
        
        return {"findings": findings, "total": len(findings)}
    except FileNotFoundError:
        return {"findings": [], "total": 0, "error": "bandit not installed"}
    except Exception as e:
        return {"findings": [], "total": 0, "error": str(e)}


@tool
async def ai_scan(repo_dir: str, file_path: str, language: str, focus: Optional[str] = None) -> dict:
    """Run AI-powered vulnerability analysis on a single file.
    
    Best for: complex logic flaws, business logic vulnerabilities, 
              context-aware analysis that pattern matchers miss.
    Cost: ~$0.01 per file. Use selectively on high-risk files only.
    
    Args:
        repo_dir: Repository root (for context)
        file_path: Relative path to file within repo
        language: Programming language
        focus: Optional hint like "sql injection", "auth bypass", "crypto"
    
    Returns: {"findings": [...], "total": N}
    """
    try:
        full_path = os.path.join(repo_dir, file_path)
        if not os.path.exists(full_path):
            return {"findings": [], "total": 0, "error": f"File not found: {file_path}"}
        
        # Read file with size limit
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read(MAX_CHARS_PER_FILE)
        
        if not code.strip():
            return {"findings": [], "total": 0}
        
        # Build prompt
        focus_hint = f"\n重点关注: {focus}" if focus else ""
        prompt = f"""你是代码安全专家。分析以下 {language} 代码中的安全漏洞。

文件: {file_path}
{focus_hint}

代码:
```{language}
{code}
```

输出 JSON 格式:
{{
  "vulnerabilities": [
    {{
      "type": "漏洞类型",
      "severity": "critical/high/medium/low",
      "line": 行号,
      "description": "漏洞描述",
      "remediation": "修复建议",
      "confidence": 0-100
    }}
  ]
}}
只输出 JSON。"""
        
        result = await _get_ai().analyze_code(code, language)
        
        vulnerabilities = []
        for v in result.get("vulnerabilities", []):
            vulnerabilities.append({
                "check_id": v.get("type", "").lower().replace(" ", "_"),
                "path": file_path,
                "start_line": v.get("line", 0),
                "end_line": v.get("line", 0),
                "message": v.get("description", ""),
                "severity": v.get("severity", "medium").upper(),
                "remediation": v.get("remediation", ""),
                "confidence": v.get("confidence", 50),
                "source": "ai",
            })
        
        return {"findings": vulnerabilities, "total": len(vulnerabilities)}
    except Exception as e:
        return {"findings": [], "total": 0, "error": str(e)}


@tool
def list_source_files(repo_dir: str, language: str, max_files: int = MAX_FILES) -> dict:
    """List source files in a repository for a given language.
    
    Returns: {{"files": [{{"rel_path": "...", "size": 1234, "abs_path": "..."}}, ...], "total": N}}
    """
    exts = EXTENSIONS.get(language.lower(), [])
    files = []
    
    for root, dirs, filenames in os.walk(repo_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for f in filenames:
            if any(f.endswith(e) for e in exts):
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, repo_dir)
                try:
                    size = os.path.getsize(abs_path)
                    files.append({"rel_path": rel_path, "abs_path": abs_path, "size": size})
                except:
                    pass
    
    # Sort by size descending (larger files first, often more important)
    files.sort(key=lambda x: x["size"], reverse=True)
    
    return {"files": files[:max_files], "total": len(files)}


@tool
def read_file(abs_path: str, max_chars: int = MAX_CHARS_PER_FILE) -> dict:
    """Read a source file with size limit.
    
    Returns: {{"content": "...", "truncated": bool, "error": str|null}}
    """
    try:
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_chars + 1)
        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars] + "\n... [truncated]"
        return {"content": content, "truncated": truncated}
    except Exception as e:
        return {"content": "", "truncated": False, "error": str(e)}


def _parse_semgrep(raw: dict, repo_dir: str) -> list[dict]:
    findings = []
    for result in raw.get("results", []):
        path = result.get("path", "")
        # Make path relative to repo_dir
        try:
            path = os.path.relpath(path, repo_dir)
        except:
            pass
        findings.append({
            "check_id": result.get("check_id", ""),
            "path": path,
            "start_line": result.get("start", {}).get("line", 0),
            "end_line": result.get("end", {}).get("line", 0),
            "message": result.get("extra", {}).get("message", ""),
            "severity": result.get("extra", {}).get("severity", "WARNING").upper(),
            "metadata": result.get("extra", {}).get("metadata", {}),
            "source": "semgrep",
        })
    return findings


def _parse_bandit(raw: dict) -> list[dict]:
    findings = []
    for result in raw.get("results", []):
        findings.append({
            "check_id": result.get("test_id", ""),
            "path": result.get("filename", ""),
            "start_line": result.get("line_number", 0),
            "end_line": result.get("line_number", 0),
            "message": result.get("issue_text", ""),
            "severity": result.get("issue_severity", "MEDIUM"),
            "confidence": result.get("issue_confidence", "MEDIUM"),
            "source": "bandit",
        })
    return findings


@tool
async def gitleaks_scan(repo_dir: str) -> dict:
    """Run Gitleaks to detect hardcoded secrets, API keys, passwords, and tokens.
    
    Best for: detecting leaked credentials in code and config files.
    Fast, language-agnostic. Always run on every project.
    
    Args:
        repo_dir: Repository root directory
    
    Returns: {"findings": [...], "total": N}
    """
    try:
        report_path = os.path.join(repo_dir, ".gitleaks-report.json")
        cmd = [
            "gitleaks", "detect",
            "--source", repo_dir,
            "--report-format", "json",
            "--report-path", report_path,
            "--no-git",
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        # Gitleaks returns 1 when leaks found, 0 when clean
        if proc.returncode not in (0, 1):
            return {"findings": [], "total": 0, "error": stderr.decode()[:500]}
        
        findings = []
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                leaks = json.load(f)
            for leak in leaks:
                findings.append({
                    "check_id": leak.get("RuleID", "hardcoded_secret"),
                    "path": leak.get("File", ""),
                    "start_line": leak.get("StartLine", 0),
                    "end_line": leak.get("EndLine", 0),
                    "message": f"Hardcoded secret detected: {leak.get('Description', 'Sensitive information')}",
                    "severity": "HIGH",
                    "confidence": 90,
                    "source": "gitleaks",
                })
            try:
                os.remove(report_path)
            except:
                pass
        
        return {"findings": findings, "total": len(findings)}
    except FileNotFoundError:
        return {"findings": [], "total": 0, "error": "gitleaks not installed"}
    except Exception as e:
        return {"findings": [], "total": 0, "error": str(e)}


@tool
async def trivy_scan(repo_dir: str) -> dict:
    """Run Trivy to scan dependencies for known CVEs (npm/pip/maven/go).
    
    Best for: detecting vulnerable third-party libraries in package.json,
              requirements.txt, pom.xml, go.mod, etc.
    Language-agnostic. Always run on every project.
    
    Args:
        repo_dir: Repository root directory
    
    Returns: {"findings": [...], "total": N}
    """
    try:
        cmd = [
            "trivy", "fs",
            "--format", "json",
            "--scanners", "vuln",
            "--severity", "CRITICAL,HIGH,MEDIUM",
            repo_dir,
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return {"findings": [], "total": 0, "error": stderr.decode()[:500]}
        
        results = json.loads(stdout) if stdout else {}
        findings = []
        
        for result in results.get("Results", []):
            target = result.get("Target", "")
            for vuln in result.get("Vulnerabilities", []):
                findings.append({
                    "check_id": vuln.get("VulnerabilityID", ""),
                    "path": target,
                    "start_line": 0,
                    "end_line": 0,
                    "message": f"{vuln.get('PkgName', '')} {vuln.get('InstalledVersion', '')}: {vuln.get('Title', vuln.get('Description', '')[:200])}",
                    "severity": vuln.get("Severity", "MEDIUM").upper(),
                    "confidence": 95,
                    "source": "trivy",
                    "metadata": {
                        "fixed_version": vuln.get("FixedVersion", ""),
                        "references": vuln.get("References", [])[:3],
                    },
                })
        
        return {"findings": findings, "total": len(findings)}
    except FileNotFoundError:
        return {"findings": [], "total": 0, "error": "trivy not installed"}
    except Exception as e:
        return {"findings": [], "total": 0, "error": str(e)}


# All tools available to the agent
ALL_TOOLS = [
    semgrep_scan,
    bandit_scan,
    gitleaks_scan,
    trivy_scan,
    ai_scan,
    list_source_files,
    read_file,
]