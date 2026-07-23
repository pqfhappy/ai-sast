#!/bin/bash
# 阿里云ECS一键部署脚本
# 使用方法: bash deploy.sh

set -e

echo "🚀 AI-SAST 部署脚本"

# 1. 安装Docker
if ! command -v docker &> /dev/null; then
    echo "📦 安装Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl start docker
    systemctl enable docker
fi

# 2. 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 3. 克隆项目
if [ ! -d "ai-sast" ]; then
    echo "📥 克隆项目..."
    git clone https://github.com/pqfhappy/ai-sast.git
fi
cd ai-sast

# 4. 配置环境变量
if [ ! -f ".env" ]; then
    echo "⚙️ 配置环境变量..."
    cp .env.example .env
    echo "请编辑 .env 文件，填入你的 QWEN_API_KEY"
    exit 1
fi

# 5. 启动服务
echo "🐳 启动Docker服务..."
docker-compose up -d --build

echo "✅ 部署完成！"
echo "   前端: http://${PUBLIC_IP:-<ECS_PUBLIC_IP>}"
echo "   API: http://${PUBLIC_IP:-<ECS_PUBLIC_IP>}:8000"
echo "   API文档: http://${PUBLIC_IP:-<ECS_PUBLIC_IP>}:8000/docs"
