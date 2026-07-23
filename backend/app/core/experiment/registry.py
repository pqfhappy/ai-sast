"""Experiment project registry.

Only REAL open-source projects we actually clone & scan. NO fabricated data.
Ground truth = the project's KNOWN intentional vulnerability categories, from OFFICIAL
project documentation/structure (verifiable), NOT from guessing.

code_glob: relative glob of source files fed to the agents (concatenated with markers).
ground_truth matching: keyword-based on finding type/description (consistent across all
  3 modes so the COMPARISON is fair; documented as methodology).
"""

EXPERIMENT_PROJECTS = [
    {
        "project_name": "Vulnerable-Flask-App",
        "repo_url": "https://github.com/we45/Vulnerable-Flask-App",
        "language": "python",
        "code_glob": "app/app.py",
        "description": "we45 出品的故意含漏洞 Flask 应用（ZAP 测试靶场）",
        "ground_truth_source": "对 app/app.py 源码逐行分析归纳的漏洞类别",
        "ground_truth": [
            {"category": "硬编码密钥", "keywords": ["hardcod", "secret", "secret_key"]},
            {"category": "弱密码哈希(MD5)", "keywords": ["md5", "weak_hash", "insecure_hash"]},
            {"category": "不安全JWT验证", "keywords": ["jwt", "insecure_jwt"]},
            {"category": "明文密码存储", "keywords": ["plaintext", "password_storage"]},
            {"category": "SQL注入", "keywords": ["sql", "sqli"]},
            {"category": "越权访问(IDOR)", "keywords": ["idor", "direct_object", "insecure_direct"]},
            {"category": "XXE实体注入", "keywords": ["xxe", "external_entity"]},
            {"category": "YAML反序列化", "keywords": ["yaml", "deserializ"]},
            {"category": "不安全文件上传", "keywords": ["upload", "file_upload"]},
        ],
    },
    {
        "project_name": "DVWA",
        "repo_url": "https://github.com/digininja/DVWA",
        "language": "php",
        "code_glob": "vulnerabilities/*/source/low.php",
        "description": "DVWA (Damn Vulnerable Web Application) — OWASP 经典 PHP 漏洞靶场",
        "ground_truth_source": "DVWA 官方 vulnerabilities/ 目录的 19 个漏洞模块（实测）",
        "ground_truth": [
            {"category": "SQL注入", "keywords": ["sql injection", "sqli", "sql_injection"]},
            {"category": "SQL盲注", "keywords": ["blind sql", "sqli_blind", "blind_sql", "sql injection (blind)"]},
            {"category": "反射型XSS", "keywords": ["reflected xss", "xss_r", "xss reflected"]},
            {"category": "存储型XSS", "keywords": ["stored xss", "xss_s", "xss stored"]},
            {"category": "DOM型XSS", "keywords": ["dom xss", "xss_d", "xss dom", "dom-based"]},
            {"category": "命令注入", "keywords": ["command injection", "command_execution", "exec", "os command"]},
            {"category": "文件包含", "keywords": ["file inclusion", "include", "lfi", "rfi"]},
            {"category": "文件上传", "keywords": ["file upload", "upload"]},
            {"category": "CSRF", "keywords": ["csrf", "cross-site request", "cross_site_request"]},
            {"category": "暴力破解", "keywords": ["brute force", "brute_force", "bruteforce"]},
            {"category": "不安全验证码", "keywords": ["captcha"]},
            {"category": "弱会话ID", "keywords": ["weak session", "session id", "weak_id", "session_id"]},
            {"category": "认证绕过", "keywords": ["auth bypass", "authentication bypass", "authbypass"]},
            {"category": "越权访问", "keywords": ["broken access", "access control", "bac", "authorization"]},
            {"category": "开放重定向", "keywords": ["open redirect", "open_redirect", "unvalidated redirect"]},
            {"category": "CSP绕过", "keywords": ["csp", "content security policy"]},
            {"category": "密码学缺陷", "keywords": ["cryptography", "crypto", "cipher", "insecure crypto"]},
            {"category": "JavaScript攻击", "keywords": ["javascript", "js attack"]},
            {"category": "API漏洞", "keywords": ["api"]},
        ],
    },
]


def get_project(name: str):
    for p in EXPERIMENT_PROJECTS:
        if p["project_name"] == name:
            return p
    return None
