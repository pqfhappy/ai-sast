"""测试用：包含常见漏洞的示例代码"""

def sql_injection(user_input: str):
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    execute(query)


def hardcoded_secret():
    password = "admin123"
    api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    db_url = "postgresql://user:pass@localhost/db"
    return password


def command_injection(user_input: str):
    import os
    os.system(f"ping {user_input}")


def path_traversal(filename: str):
    with open(f"/var/data/{filename}", "r") as f:
        return f.read()


def xss_vulnerable(user_input: str):
    return f"<div>{user_input}</div>"


def unsafe_eval(user_input: str):
    result = eval(user_input)
    return result


def insecure_deserialization(data: bytes):
    import pickle
    obj = pickle.loads(data)
    return obj


def weak_crypto():
    import hashlib
    return hashlib.md5(b"password").hexdigest()


def execute(query):
    print(f"Executing: {query}")
