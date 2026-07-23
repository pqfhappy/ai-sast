# AI-SAST Project Requirements

## Deployment
- `deploy.py` 没有 `git pull` 步骤，部署前必须手动同步修改过的文件到 ECS（通过 SFTP/scp）
- 修改文件后需执行：上传文件 → ECS 重新构建前端 → 重启后端 → reload nginx
- 部署脚本会在 nginx 中写入 server block，如果 conf.d/ 里已有重复配置会导致冲突

## Frontend
- 使用 Vue3 + Element Plus 暗色主题（参见 App.vue 的全局 CSS 覆盖）
- 暗色主题下 `el-button link type="primary"` 蓝字看不清，需替换为自定义 el-tag 或覆盖 `.el-button--link` 颜色
- 所有表格的日期字段需通过 `formatDate()` 格式化为 `YYYY-MM-DD HH:mm:ss`（含时区校正）
- 漏洞报告页的展开行使用 Element Plus 内置的 `type="expand"` + `expand-row-keys` 机制，禁止自定义 `v-if` 控制
- Dashboard 表格列尽量使用 `min-width` + `show-overflow-tooltip`，避免固定宽度导致内容截断或过宽
- **严禁白色/浅色背景**：全站暗色主题，任何模块（代码块、卡片、弹窗等）都不允许出现白色或亮色背景

## Backend
- `context_lines` 参数设为 5（`_extract_code_snippet` 函数）
- 数据库使用 SQLite，路径 `/data/ai-sast/backend/data/sast.db`
- ChromaDB 需要 pysqlite3-binary 补丁

## Convention
- AGENTS.md 中记录项目长期要求和约束，每次会话开始时读取
- 本地 `.env` 用完即删，敏感信息不上传代码仓
