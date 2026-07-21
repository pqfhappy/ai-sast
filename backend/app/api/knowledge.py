from fastapi import APIRouter

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

KNOWLEDGE_BASE = {
    "vulnerability_types": [
        {
            "name": "SQL注入",
            "cwe": "CWE-89",
            "severity": "HIGH",
            "description": "通过拼接用户输入构造SQL查询，可能导致数据库信息泄露",
            "fix": "使用参数化查询或ORM，避免字符串拼接SQL",
        },
        {
            "name": "XSS跨站脚本",
            "cwe": "CWE-79",
            "severity": "MEDIUM",
            "description": "未转义用户输入直接输出到页面，可执行恶意脚本",
            "fix": "对输出进行HTML实体编码，使用CSP头",
        },
        {
            "name": "硬编码密钥",
            "cwe": "CWE-798",
            "severity": "HIGH",
            "description": "代码中直接写入密码、API密钥等敏感信息",
            "fix": "使用环境变量或密钥管理服务",
        },
        {
            "name": "命令注入",
            "cwe": "CWE-78",
            "severity": "CRITICAL",
            "description": "未过滤用户输入直接传递给系统命令执行",
            "fix": "避免使用shell=True，使用安全的API替代",
        },
        {
            "name": "路径遍历",
            "cwe": "CWE-22",
            "severity": "MEDIUM",
            "description": "未验证文件路径，可能导致读取任意文件",
            "fix": "对路径进行规范化校验，限制在允许目录内",
        },
    ]
}


@router.get("/vulnerabilities")
async def list_vulnerability_types():
    return KNOWLEDGE_BASE["vulnerability_types"]


@router.get("/search")
async def search_knowledge(q: str = ""):
    if not q:
        return KNOWLEDGE_BASE
    results = []
    q = q.lower()
    for vuln in KNOWLEDGE_BASE["vulnerability_types"]:
        if q in vuln["name"].lower() or q in vuln["cwe"].lower():
            results.append(vuln)
    return {"results": results}
