"""Setup demo projects with real open-source project code for SAST scanning."""
import requests, json

BASE = "http://8.130.89.12/api"

# Pre-defined demo projects and their vulnerable code snippets
DEMO_PROJECTS = [
    {
        "name": "OWASP WebGoat (Java)",
        "description": "OWASP官方 deliberately insecure Java Web应用，包含SQL注入、XSS、路径遍历等经典漏洞",
        "language": "java",
        "code": """// WebGoat SQL Injection Example
@PostMapping("/SqlInjection/attack")
@ResponseBody
public String sqlInjection(@RequestParam("query") String query) {
    String sql = "SELECT * FROM users WHERE name = '" + query + "'";
    Statement stmt = connection.createStatement();
    ResultSet rs = stmt.executeQuery(sql);
    return resultSetToString(rs);
}

// Also check for hardcoded credentials
String dbPassword = "webgoat_password";
String apiKey = "AIzaSyD-xxxxxxxxxxxxxxxxxxxxx";

// Command injection
Runtime.getRuntime().exec("ping " + query);"""
    },
    {
        "name": "DVWA (PHP)",
        "description": "Damn Vulnerable Web Application - PHP漏洞演练平台，含文件包含、CSRF、文件上传等漏洞",
        "language": "php",
        "code": """<?php
// DVWA SQL Injection
$id = $_GET['id'];
$query  = "SELECT first_name, last_name FROM users WHERE user_id = '$id';";
$result = mysqli_query($GLOBALS["___mysqli_ston"],  $query);

// DVWA File Inclusion
$file = $_GET['page'];
include($file);

// DVWA Command Injection
$target = $_REQUEST['ip'];
$cmd = shell_exec('ping -c 3 ' . $target);
echo $cmd;

// DVWA File Upload
move_uploaded_file($_FILES['uploaded']['tmp_name'], $target_path);
?>"""
    },
    {
        "name": "NodeGoat (Node.js)",
        "description": "Node.js漏洞示例项目，含NoSQL注入、SSRF、不安全的直接对象引用等OWASP Top 10漏洞",
        "language": "javascript",
        "code": """// NodeGoat NoSQL Injection
app.post('/login', (req, res) => {
    const username = req.body.username;
    const password = req.body.password;
    // NoSQL injection vulnerability
    db.collection('users').find({
        $where: `this.username === '${username}' && this.password === '${password}'`
    }).toArray((err, users) => {
        if (users.length > 0) res.send('Login success');
    });
});

// SSRF vulnerability
app.get('/fetch', (req, res) => {
    const url = req.query.url;
    request(url, (err, resp, body) => res.send(body));
});

// Insecure direct object reference
app.get('/user/:id', (req, res) => {
    db.collection('users').findOne({_id: req.params.id}).then(user => res.json(user));
});

// Hardcoded secret
const JWT_SECRET = 'supersecretkey123';
"""
    },
    {
        "name": "Rust Security Examples",
        "description": "Rust语言常见安全漏洞示例，含不安全unsafe代码、命令注入、SQL注入等",
        "language": "rust",
        "code": """// Rust - Unsafe code vulnerability
use std::ffi::CString;
use std::os::raw::c_char;

fn unsafe_ffi(input: &str) {
    let c_str = CString::new(input).unwrap();
    unsafe {
        let ptr = c_str.into_raw();
        // Buffer overflow possible
        println!("{:?}", *ptr);
    }
}

// Command injection
use std::process::Command;
fn run_command(user_input: &str) {
    let output = Command::new("sh")
        .arg("-c")
        .arg(format!("echo {}", user_input))
        .output()
        .expect("failed");
}

// SQL injection with diesel
use diesel::sql_query;
fn unsafe_query(user_input: &str) {
    let query = format!("SELECT * FROM users WHERE name = '{}'", user_input);
    let results = sql_query(query).load::<User>(&connection);
}
"""
    },
    {
        "name": "Go Vulnerability Examples",
        "description": "Golang常见安全漏洞示例，含SQL注入、命令注入、不安全的反序列化等",
        "language": "go",
        "code": """package main

import (
    "database/sql"
    "fmt"
    "os/exec"
    "net/http"
)

// SQL Injection
func unsafeQuery(db *sql.DB, userInput string) {
    query := fmt.Sprintf("SELECT * FROM users WHERE name='%s'", userInput)
    rows, _ := db.Query(query)
}

// Command Injection
func runCmd(userInput string) {
    cmd := exec.Command("bash", "-c", "echo "+userInput)
    output, _ := cmd.Output()
    fmt.Println(string(output))
}

// Path traversal
func readFile(w http.ResponseWriter, r *http.Request) {
    filename := r.URL.Query().Get("file")
    http.ServeFile(w, r, "/data/"+filename)
}

// Hardcoded credentials
const (
    DB_PASSWORD = "password123"
    API_KEY     = "sk-xxxxxxxxxxxxxxxxxxxx"
)
"""
    },
    {
        "name": "C Buffer Overflow Examples",
        "description": "C语言内存安全漏洞示例，含缓冲区溢出、格式化字符串、use-after-free等经典漏洞",
        "language": "c",
        "code": """// C Buffer Overflow
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void vulnerable_function(char *user_input) {
    char buffer[64];
    // Buffer overflow
    strcpy(buffer, user_input);
}

void format_string_vuln(char *user_input) {
    // Format string vulnerability
    printf(user_input);
}

// Use after free
void use_after_free() {
    char *ptr = (char*)malloc(64);
    strcpy(ptr, "hello");
    free(ptr);
    // Use after free!
    strcpy(ptr, "world");
}

// Command injection
void run_command() {
    char cmd[256];
    sprintf(cmd, "ls -l %s", getenv("USER_INPUT"));
    system(cmd);
}
"""
    },
]

# Create projects and scan them
print(f"Creating {len(DEMO_PROJECTS)} demo projects...\n")

for project in DEMO_PROJECTS:
    # Create project
    r = requests.post(f"{BASE}/projects", params={
        "name": project["name"],
        "description": project["description"],
        "language": project["language"],
    })
    p = r.json()
    pid = p.get("id")
    print(f"[{pid}] {project['name']} ({project['language']})")

    # Create scan
    r = requests.post(f"{BASE}/scans", params={"project_id": pid, "branch": "master"})
    scan = r.json()
    sid = scan.get("id")

    # Run scan
    r = requests.post(f"{BASE}/scans/{sid}/run", json={
        "code": project["code"],
        "language": project["language"],
    })
    result = r.json()
    vuln_count = result.get("total", 0)
    print(f"  -> 扫描完成, 发现 {vuln_count} 个漏洞")

print("\n✅ 所有项目创建并扫描完成！")
print(f"访问 http://8.130.89.12 查看效果")
