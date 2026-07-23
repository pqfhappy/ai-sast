# AI-SAST 项目规则与约束

> 所有开发必须遵守的硬性规则。AI 编码时请优先阅读此文件。

---

## 1. Git 提交规范

### Commit Message 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型
| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(scans): add real project scan endpoint` |
| `fix` | Bug 修复 | `fix(reports): handle legacy code_snippet format` |
| `refactor` | 重构（无功能变更） | `refactor(orchestrator): use LangGraph state graph` |
| `perf` | 性能优化 | `perf(bandit): use recursive scan mode` |
| `style` | 代码格式/风格（不影响逻辑） | `style(frontend): fix ESLint warnings` |
| `docs` | 文档更新 | `docs: update AGENTS.md with deploy steps` |
| `test` | 测试相关 | `test(scanner): add bandit integration test` |
| `chore` | 构建/工具/依赖更新 | `chore(deps): upgrade fastapi to 0.115` |
| `deploy` | 部署相关脚本/配置 | `deploy: add nginx config template` |

### Scope 范围
- `backend` / `frontend` / `scanner` / `api` / `db` / `deploy` / `docs` / `ci` / `experiment`

### 示例
```
feat(scanner): add recursive bandit scan for directories

- bandit.py: add -r flag for recursive directory scan
- orchestrator.py: update scan_project to pass dir path
- fixes timeout on large repos

Closes #42
```

### 硬性要求
- **每次提交必须包含 type 和 scope**
- subject 使用祈使语气，首字母小写，不超过 72 字符
- 破坏性变更必须在 footer 写 `BREAKING CHANGE: ...`
- 关联 Issue 写 `Closes #<num>` 或 `Refs #<num>`
- **尽量少提交**：除非涉及多设备同步代码，否则本地暂存即可，减少无意义提交历史
- **临时脚本不入库**：本地生成的临时操作脚本（如 `_check_scan.py`、`deploy_backend.py` 等）验证完即删，**不提交**；仅将与工程强相关、已整合为正式工具的脚本（如 `scripts/deploy.py`、`scripts/setup_demo.py`）纳入版本控制
- **AI 提交标识**：AI 自动提交时，**通过提交者名字体现**（不是写在 message 里）。用 `git -c user.name="八戒" -c user.email="bajie@ai-sast.bot" commit ...` 临时覆盖**单次**提交，**严禁修改 git config**（`git config user.name` 等），保证用户手动提交时仍是其本人名字。
  ```bash
  git -c user.name="八戒" -c user.email="bajie@ai-sast.bot" commit -m "feat(scanner): add recursive bandit scan"
  ```

---

## 2. 部署约束

### 部署流程（严禁跳过步骤）
1. **本地修改完成** → 运行本地测试/构建验证
2. **手动同步文件到 ECS**：`scp` / SFTP 上传**仅修改过的文件**（不要整仓库）
3. **ECS 上重新构建前端**：`cd /data/ai-sast/frontend && npm run build`
4. **重启后端**：`sudo systemctl restart ai-sast`
5. **Reload Nginx**：`sudo nginx -s reload`
6. **强制自验证**：运行 `python scripts/verify_deploy.py`，**全部 PASS 才能向用户报告完成**（见第 9 节）

### 部署脚本限制
- `deploy.py` **没有 `git pull` 步骤**，ECS 上代码不会自动更新
- `nginx conf.d/` 下如果已有同名配置会导致冲突，部署前需检查
- `.env` 文件**本地用完即删**，敏感信息（API Key、密码）绝不上传代码仓

### ECS Python 环境
- `python` / `python3` = **3.6.8**（太老，禁用）
- `python310` = **3.10.15**
- `python3.11` = **3.11.13**（systemd 服务使用此版本）
- `pip3` 指向 Python 3.6，**安装依赖必须用 `python3.11 -m pip`**
- PyPI 外网慢，**必须加阿里云镜像**：`-i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`
- gitleaks/trivy 等二进制工具从 GitHub 下载也慢，建议后台 `nohup` 安装或提前下载好上传

---

## 3. 前端规范（Vue 3 + Element Plus）

### 主题与颜色
- **全站暗色主题**，严禁出现白色/浅色背景
- 任何模块（代码块、卡片、弹窗、表格、Tooltip）背景必须是深色
- 全局 CSS 覆盖在 `App.vue` 的 `<style>` 中定义

### 组件用法
| 场景 | 规范 |
|------|------|
| 表格日期列 | 必须用 `formatDate()` 格式化为 `YYYY-MM-DD HH:mm:ss`（含时区校正 UTC+8） |
| 展开行 | 必须用 Element Plus 内置 `type="expand"` + `expand-row-keys`，**禁止**自定义 `v-if` 控制 |
| 列宽 | 优先用 `min-width` + `show-overflow-tooltip`，避免固定 `width` 导致截断/过宽 |
| 链接按钮 | 暗色主题下 `el-button link type="primary"` 蓝字不可见，**禁用**；改用普通 `<span>` + 自定义颜色 `#7fc1ff` 或 `el-tag` |
| 状态标签 | 统一用 `el-tag`，severity 对应：critical=red, high=orange, medium=yellow, low=green |

### 代码规范
- 组件名 PascalCase，文件名 PascalCase.vue
- 组合式 API `<script setup>`，避免 Options API
- 类型定义优先用 `interface`，复杂类型用 `type`
- 避免 `any`，用 `unknown` 或具体类型
- 事件命名：`on<Event>`（如 `onScanComplete`）

---

## 4. 后端规范（FastAPI + SQLAlchemy）

### 代码结构
```
backend/app/
├── api/           # 路由层（仅处理 HTTP，不含业务逻辑）
├── core/          # 核心逻辑
│   ├── scanner/   # 扫描引擎（每个引擎一个文件）
│   ├── agents/    # Agent 系统
│   └── evolution/ # 自我进化
├── services/      # 业务服务层
├── models/        # SQLAlchemy 模型
├── schemas/       # Pydantic 模型（请求/响应）
└── main.py        # 入口
```

### 数据库
- SQLite，路径固定：`/data/ai-sast/backend/data/sast.db`
- 所有时间戳用 `datetime.utcnow()` 存 **UTC**，前端负责 +8 转北京时间
- ChromaDB 需要 `pysqlite3-binary` 补丁（已在 requirements.txt）

### 扫描器约束
- `context_lines = 5`（`_extract_code_snippet` 函数固定值，不得改动）
- Bandit 必须使用 `-r` 递归模式扫描目录
- AI 扫描器单项目限制前 10 个文件（控制成本/耗时）

### API 设计
- RESTful 风格，复数名词（`/api/scans`、`/api/projects`）
- 统一响应格式：成功返回数据，失败返回 `{ "detail": "..." }`
- 分页：`page` + `page_size`，默认 20，最大 100
- 筛选用 query params：`?status=running&severity=high`

---

## 5. 代码风格通用

### Python
- 缩进 4 空格，行长 ≤ 100 字符
- 类型注解**全量覆盖**（参数、返回值、关键变量）
- `black` + `isort` 格式化，`mypy --strict` 类型检查
- 异常处理：捕获具体异常，记录结构化日志，不裸露 `except:`

### TypeScript/Vue
- 缩进 2 空格，行长 ≤ 100 字符
- `eslint` + `prettier` + `vue-tsc` 检查
- 组件 props 必须定义类型 + 默认值
- 避免在模板中写复杂表达式，提取为计算属性/方法

### 注释规范
- **不写无意义注释**（如 `// 定义变量`）
- 公共 API/复杂算法**必须**写 docstring/JSDoc
- TODO/FIXME 格式：`// TODO(<author>): <description>`

---

## 6. 安全与敏感信息

| 项目 | 规则 |
|------|------|
| API Key / 密码 | 仅存在 `.env`（本地）或 ECS 环境变量，**绝不**写入代码/提交历史 |
| 数据库文件 | `sast.db` 不提交，`.gitignore` 已忽略 |
| 上传文件 | 扫描样本代码归档到 `/data/ai-sast/samples/scan{ID}_{仓库名}/`（保留供对比，不再删除） |
| CORS | 生产环境仅允许前端域名，开发环境 `*` |

---

## 7. 实验性功能隔离

- 新功能先在 `/experiment` 页面验证，不污染主流程
- 实验代码放 `frontend/src/views/Experiment.vue`，后端单独路由前缀 `/api/experiment/`
- 稳定后再合并到主功能模块

---

## 8. 测试 Agent 与自验证闭环（AI Native 核心）

> **核心原则：AI 改完代码后，必须先自验证通过，才能向用户报告"完成"。把验证从用户身上转移到 AI 身上。**

### 8.1 强制自验证规则（硬性）
- **每次部署到 ECS 后**，必须运行 `python scripts/verify_deploy.py`
- **所有检查项 PASS** 才能向用户报告完成；有任何 FAIL，必须**自行修复并重新部署**，直到全绿
- **新增功能时**，必须同步在 `verify_deploy.py` 中**增加对应的检查项**（测试随功能演进）
- 严禁在未运行自验证的情况下声称"部署完成/功能正常"

### 8.2 测试 Agent 的三层结构
```
测试脚本 (scripts/verify_deploy.py)  ← 手脚：确定性冒烟检查，可重复执行
        ↑ 运行
AI 大脑 (主 Agent / Task 子 Agent)   ← 大脑：解读失败、定位根因、自动修复
        ↑ 触发
规则 (本节)                          ← 触发器：每次部署后强制执行
```

### 8.3 验证脚本检查项清单
| # | 检查项 | 类型 | 防的是哪个历史 Bug |
|---|--------|------|--------------------|
| 1 | backend health | HTTP | 服务起不来 |
| 2 | frontend 200 | HTTP | 前端构建失败 |
| 3 | projects API 有数据 | HTTP | 接口空响应/重定向 |
| 4 | scans API 有数据 | HTTP | 接口空响应 |
| 5 | 报告返回漏洞 | HTTP | 报告页无数据 |
| 6 | confidence 是 0-100 整数 | HTTP | `MEDIUM%` 字符串置信度 |
| 7 | 漏洞有 code_snippet | HTTP | 项目扫描无代码片段 |
| 8 | severity 枚举合法 | HTTP | 非法严重度值 |
| 9 | 后端服务 active | SSH | 服务崩溃 |
| 10 | 日志无 import 错误 | SSH | 模块导入失败（如 config 路径错） |
| 11 | samples 目录有归档 | SSH | 样本未保留/权限问题 |

### 8.4 深度验证（可选，复杂改动时）
对于架构级改动，除跑脚本外，可用 Task 工具启动 `general` 子 Agent 做探索性验证：
- 让子 Agent 阅读改动文件 + 运行 verify_deploy.py + 实际触发一次扫描
- 子 Agent 返回结构化验证报告（通过/失败/疑点）
- 主 Agent 根据报告决定是否修复

### 8.5 运行方式（分层，按需省 token）

**核心认知**：只读冒烟检查本身**不花 token**（纯本地 HTTP），跑全量更安全（抓回归）。真正花 token 的是「AI 修复循环」和「主动触发扫描」。因此分层：

```bash
# 第1层｜冒烟（默认全跑，免费，抓回归）—— 每次部署后必跑
python scripts/verify_deploy.py

# 第2层｜定向（只跑改动相关的标签，省时）
python scripts/verify_deploy.py --only quality        # 只查数据质量
python scripts/verify_deploy.py --only api,frontend   # 只查接口+前端

# 第3层｜主动（触发真实扫描，花 Qwen token，opt-in）—— 仅在验证扫描链路时手动跑
python scripts/verify_deploy.py --with-scan

# 含 SSH 检查（服务状态/日志/samples）
SAST_HOST=<your-ecs-ip> SAST_PASSWORD=xxx python scripts/verify_deploy.py
```

**标签说明**：`api`(接口连通) / `frontend`(前端) / `quality`(数据质量回归) / `ssh`(服务/日志/样本) / `scan`(主动扫描,opt-in)

### 8.6 改动 → 检查项映射（AI 据此选择子集）

| 改动了什么 | 至少跑这些标签 | 说明 |
|-----------|---------------|------|
| 前端 Vue 组件 | `frontend` + `quality` | 前端构建 + 数据展示回归 |
| API 路由 / scans.py | `api` + `quality` | 接口连通 + 数据质量 |
| 扫描器 / orchestrator / tools | **全量** + 视情况 `--with-scan` | 核心链路，必须全跑 |
| 置信度/片段/严重度逻辑 | `quality` | 数据质量回归 |
| 部署配置 / 依赖 / 服务 | **全量** + SSH | 基础设施变更最易引回归 |
| 仅文档 / rules.md | 无需跑 | 不影响运行时 |

> **原则**：拿不准就跑全量（免费）。只有明确只动了局部、且想省时才用 `--only`。`--with-scan` 花真钱，仅在改了扫描链路需要端到端验证时用。

退出码：全 PASS 返回 0，有 FAIL 返回 1，无检查运行返回 2（可用于自动化门禁）。

---

## 9. 需求驱动的测试用例原则（最高优先级）

> **核心：测试用例由「用户诉求」生成，是需求的固化记忆。代码可以改，测试用例不能随代码漂移。**

### 9.1 强制流程（每次调试功能都必须遵守）
1. **用户提诉求** → AI 先把诉求**逐条转成测试用例**（写明：用例ID、对应诉求、验证方法、通过标准）
2. 测试用例落到**独立文件**（如 `docs/<功能>_test_cases.md` + 可自动化部分进 `scripts/verify_<功能>.py`）
3. **先跑一遍基线**，记录当前哪些用例失败（证明用例真实反映了差距）
4. AI 修改代码 → **每改一轮就重跑测试用例** → 全过才算完成
5. 向用户报告时，**附测试用例通过情况**，而非只说"改好了"

### 9.2 测试用例的铁律
- **来源唯一**：测试用例只从「用户诉求」推导，**不从业务代码推导**
- **禁止漂移**：多轮修改后，AI 可能忘记用户原始要求，但**测试用例必须始终持有用户要求**，用它来校验代码，而不是反过来改测试用例迁就代码
- **只有用户改诉求时**才能改测试用例；AI 不得因为"代码实现不了"就删改测试用例
- 测试用例文件是**长期资产**，跨会话保留，每次继续调试先读它

### 9.3 测试用例 vs 自验证脚本（8节）的区别
| | 自验证脚本 (verify_deploy.py) | 需求测试用例 (verify_<功能>.py) |
|---|---|---|
| 来源 | 历史 Bug 回归 + 通用健康检查 | **用户当前诉求** |
| 生命周期 | 长期，随系统演进 | 跟随特定功能调试周期 |
| 目的 | 防回归、保健康 | 验证「是否满足用户要求」 |
| 谁定义 | AI 从 Bug 总结 | **用户诉求逐条转译** |

### 9.4 反例（绝对禁止）
- ❌ 改了代码后，发现测试用例失败，于是修改测试用例让它通过
- ❌ 测试用例写得很模糊（如"功能正常"），无法客观判定通过/失败
- ❌ 多轮讨论后，按自己理解的需求改代码，忘了用户原始诉求
- ❌ 用伪造数据让测试用例"通过"（尤其违反诉求真实性时）

---

## 10. 变更记录

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-07-21 | 初版：整理部署、前端、后端、Git 等核心约束 | - |
| 2026-07-21 | v2：新增 AI Native 改造规范（LangGraph 编排、双层 Agent 架构、七引擎工具清单） | 八戒 |
| 2026-07-22 | v3：新增测试 Agent 与自验证闭环（verify_deploy.py + 强制自验证规则） | 八戒 |
| 2026-07-22 | v4：验证脚本支持标签分层 + 按需筛选（--only / --with-scan），省 token | 八戒 |
| 2026-07-22 | v5：新增需求驱动测试用例原则（测试用例由诉求生成、禁止随代码漂移） | 八戒 |

---

> **AI 编码时请先读此文件，所有产出代码必须符合上述规范。部署后必须自验证通过才能报告完成。调试功能必须先写需求测试用例。**