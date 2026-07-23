# 🛡️ AI-SAST: 智能静态应用安全测试平台

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/AI-LLM%20Agent-orange" alt="AI">
  <img src="https://img.shields.io/github/stars/pqfhappy/ai-sast" alt="Stars">
</p>

<p align="center">
  <b>基于多Agent协作的下一代代码安全检测平台</b><br>
  🤖 多Agent博弈分析 · 🧬 自我进化 · 📊 可视化管理
</p>

---

## 项目亮点 ✨

| 特性 | 说明 |
|------|------|
| **🧠 AI Native 编排** | LangGraph StateGraph 驱动，LLM 自主决策扫描策略，告别写死流水线 |
| **🤖 双层 Agent 架构** | 编排层（LangGraph 宏观调度）+ 分析层（三 Agent 博弈微观分析） |
| **🔍 七引擎扫描** | Semgrep + Bandit + Gitleaks + Trivy + AI 深度分析 + 文件遍历 + 代码读取 |
| **🧬 自我进化** | 从误报/漏报中学习，持续优化检测规则 |
| **📊 Web管理界面** | 暗色主题的可视化仪表盘，实时监控Agent协作过程 |
| **💰 极低成本** | 基于通义千问，免费额度足够个人使用 |

## 快速开始 🚀

### 前置条件

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose（可选）

### 安装

```bash
# 克隆项目
git clone https://github.com/pqfhappy/ai-sast.git
cd ai-sast

# 配置API Key
cp .env.example .env
# 编辑 .env，填入你的通义千问API Key

# Docker一键部署
docker-compose up -d
```

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 系统架构 🏗️

```
代码输入 → [LangGraph 编排 Agent] → 自主决策调用工具 → [三 Agent 博弈分析] → 最终报告
                    │                                        │
                    ▼                                        ▼
        ┌─────────────────────┐              ┌─────────────────────────┐
        │  semgrep (多语言)   │              │  审查Agent → 安全Agent  │
        │  bandit (Python)    │              │       → 修复Agent       │
        │  gitleaks (密钥)    │              │    多轮博弈 → 仲裁      │
        │  trivy (依赖CVE)    │              └─────────────────────────┘
        │  ai_scan (LLM深挖)  │
        └─────────────────────┘
```

- **编排层**：LLM 分析代码库结构后，动态决定「先扫什么、用什么工具、要不要深挖」
- **分析层**：三 Agent 对高危发现进行博弈辩论，达成共识后输出最终结论

## 技术栈 🛠️

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 前端 | Vue3 + Element Plus + Vite |
| AI 编排 | LangGraph + LangChain + 通义千问 |
| 扫描引擎 | Semgrep + Bandit + Gitleaks + Trivy + AI增强 |
| 向量库 | ChromaDB |
| 部署 | Docker + Nginx |

## 项目结构 📁

```
ai-sast/
├── backend/          # FastAPI后端
│   └── app/
│       ├── api/      # API路由
│       ├── core/     # 核心逻辑
│       │   ├── scanner/    # 扫描引擎
│       │   │   ├── orchestrator.py      # LangGraph 编排器（AI Native）
│       │   │   ├── tools.py             # LangChain Tools 封装
│       │   │   ├── semgrep.py           # Semgrep 扫描器
│       │   │   ├── bandit.py            # Bandit 扫描器
│       │   │   └── ai_scanner.py        # LLM 深度分析
│       │   ├── agents/     # 多Agent系统（三Agent博弈）
│       │   └── evolution/  # 自我进化
│       └── services/       # 业务服务
├── frontend/         # Vue3前端
└── knowledge/        # 知识库
```

## Agent角色 👥

### 编排层（LangGraph）

| Agent | 角色 | 职责 |
|-------|------|------|
| 🧠 **编排 Agent** | 项目经理 | 分析代码结构，自主决定扫描策略、工具组合、深挖时机 |

### 分析层（三 Agent 博弈）

| Agent | 角色 | 职责 |
|-------|------|------|
| 🔍 **审查Agent** | 代码审查员 | 初步判断漏洞真实性，Semgrep + LLM分析 |
| 🛡️ **安全Agent** | 安全专家 | 深度分析，CVSS评分，攻击路径推演 |
| 🔧 **修复Agent** | 修复顾问 | 生成修复代码，评估修复可行性与成本 |

## 自我进化 🧬

系统通过以下方式持续进化：

1. **反馈学习**：用户标记误报/漏报，系统记录并分析
2. **规则生成**：基于高频漏洞类型，自动建议新的Semgrep规则
3. **Prompt优化**：根据历史反馈优化Agent的Prompt

## 开发计划 📅

- [x] Day 1: 项目骨架 + 框架搭建
- [x] Day 2: 扫描引擎（Semgrep + Bandit + AI）
- [x] Day 3: 多Agent系统（辩论-仲裁机制）
- [x] Day 4: Web界面（暗色主题仪表盘）
- [x] Day 5: 知识库 + 进化机制
- [x] Day 6: 部署到阿里云ECS + 文档
- [x] Day 7: **AI Native 改造**（LangGraph 编排 + Gitleaks/Trivy 工具接入）

## License 📄

MIT
