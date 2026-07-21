"""Comprehensive vulnerable Python code sample for SAST testing."""
import hashlib
import hmac
import os
import subprocess
import pickle
import sqlite3


def sql_injection(user_input: str):
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    cursor.execute(query)
    return cursor.fetchall()


def hardcoded_credentials():
    username = "admin"
    password = "P@ssw0rd!"
    api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    db_url = "postgresql://user:secret@localhost:5432/mydb"
    return {"username": username, "password": password}


def command_injection(user_input: str):
    os.system(f"ping {user_input}")
    subprocess.call(f"nslookup {user_input}", shell=True)


def path_traversal(filename: str):
    with open(f"/var/data/{filename}", "r") as f:
        return f.read()


def xss_reflected(user_input: str):
    return f"<html><body><div>{user_input}</div></body></html>"


def unsafe_eval(user_input: str):
    result = eval(user_input)
    return result


def insecure_deserialization(data: bytes):
    obj = pickle.loads(data)
    return obj


def weak_hash():
    return hashlib.md5(b"password").hexdigest()


def weak_crypto():
    data = b"sensitive data"
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    cipher = Cipher(algorithms.DES(b"key12345"), modes.ECB())
    return cipher


def insecure_random():
    import random
    return random.randint(0, 1000000)


def assert_statement(user_input):
    assert user_input.isalpha(), "Invalid input"
    return user_input


def dangerous_exec():
    code = "print('hello')"
    exec(code)


def insecure_http():
    import requests
    resp = requests.get("http://example.com/api/data", verify=False)
    return resp.text


def debug_info_leak():
    import flask
    app = flask.Flask(__name__)
    @app.route("/debug")
    def debug():
        return flask.jsonify(app.config)


def insecure_temperory_file():
    import tempfile
    tmp = tempfile.mktemp()
    with open(tmp, "w") as f:
        f.write("sensitive data")


def no_rate_limit():
    import flask
    app = flask.Flask(__name__)
    @app.route("/login")
    def login():
        return "login success"


def dangerous_import():
    import telnetlib
    tn = telnetlib.Telnet("example.com")


def weak_password_policy():
    password = "123456"
    return password


def clickjacking_vulnerable():
    import flask
    app = flask.Flask(__name__)
    @app.route("/")
    def index():
        return "<html><body>Vulnerable</body></html>"


def open_redirect(url):
    import flask
    return flask.redirect(url)


def server_side_template_injection():
    from jinja2 import Template
    user_input = "{{ config }}"
    template = Template(user_input)
    return template.render()
