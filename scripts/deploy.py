"""AI-SAST deployment script for Alibaba Cloud ECS."""
import os
import time
import paramiko

HOST = os.environ.get("SAST_HOST", "8.130.89.12")
USER = os.environ.get("SAST_USER", "root")
PASSWORD = os.environ.get("SAST_PASSWORD", "Root@123")
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")

NGINX_MAIN = """user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /run/nginx.pid;
events { worker_connections 1024; }
http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"';
    access_log /var/log/nginx/access.log main;
    sendfile on; tcp_nopush on; keepalive_timeout 65; types_hash_max_size 4096;
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    include /etc/nginx/conf.d/*.conf;
}"""

NGINX_SITE = """server {
    listen 80 default_server;
    access_log /var/log/nginx/ai-sast.log;
    root /data/ai-sast/frontend/dist;
    index index.html;
    try_files $uri $uri/ /index.html;
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}"""

SYSTEMD_SERVICE = """[Unit]
Description=AI-SAST Backend
After=network.target
[Service]
Type=simple
WorkingDirectory=/data/ai-sast/backend
Environment=QWEN_API_KEY=%s
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
[Install]
WantedBy=multi-user.target"""


class Deployer:
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

    def run(self, cmd, timeout=60):
        stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out + ("\nERR: " + err[:300] if err else "")

    def write_file(self, path, content):
        stdin, stdout, stderr = self.client.exec_command("tee " + path, timeout=10)
        stdin.write(content + "\n")
        stdin.flush()
        stdin.channel.shutdown_write()
        return (stdout.read().decode() + stderr.read().decode())[:200]

    def deploy(self):
        print("1. Installing Python deps...")
        print(self.run("pip3 install fastapi uvicorn sqlalchemy aiosqlite openai pydantic-settings chromadb 2>&1 | tail -3", 120))

        print("2. Building frontend...")
        print(self.run("cd /data/ai-sast/frontend && npm install 2>&1 | tail -3", 120))
        print(self.run("cd /data/ai-sast/frontend && npm run build 2>&1 | tail -5", 60))

        print("3. Configuring nginx...")
        print(self.run("dnf install -y nginx 2>&1 | tail -2", 60))
        print(self.write_file("/etc/nginx/nginx.conf", NGINX_MAIN))
        print(self.write_file("/etc/nginx/conf.d/ai-sast.conf", NGINX_SITE))
        print(self.run("nginx -t 2>&1 && systemctl enable nginx && systemctl restart nginx", 15))

        print("4. Configuring backend service...")
        svc_content = SYSTEMD_SERVICE % QWEN_API_KEY
        print(self.write_file("/etc/systemd/system/ai-sast.service", svc_content))
        print(self.run("systemctl daemon-reload && systemctl enable ai-sast && systemctl restart ai-sast", 15))

        print("5. Verifying...")
        time.sleep(3)
        print("Health:", self.run("curl -s http://localhost:8000/api/health", 10))
        print("Frontend:", self.run("curl -s http://localhost/ | head -2", 10))

    def close(self):
        self.client.close()


if __name__ == "__main__":
    d = Deployer()
    d.connect()
    d.deploy()
    d.close()
