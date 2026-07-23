# 实验专区 — 需求测试用例（需求记忆，禁止随代码漂移）

> **来源**：用户诉求（2026-07-22）。本文件是需求的固化，**只有用户改诉求时才能改本文件**。
> AI 修改业务代码后，必须重跑这些用例验证，**不得为迁就代码而修改本文件**。
> 自动化部分见 `scripts/verify_experiment.py`。

---

## 诉求 1：每个扫描任务必须有明确的资源描述

| 用例ID | 验证点 | 验证方法 | 通过标准 |
|--------|--------|----------|----------|
| EXP-1.1 | 显示开源项目名称 | auto | 每个实验任务有非空 `project_name` |
| EXP-1.2 | 项目地址以**可点击超链接**展示，新标签打开 | manual+auto | URL 真实有效（非 `#`/空），前端 `<a target="_blank">` |
| EXP-1.3 | 显示该项目的**预期漏洞数量** | auto | 每个任务有 `expected_count` 字段（整数，来自项目文档/CVE，非随意填） |
| EXP-1.4 | 显示**实际检出漏洞数量** | auto | 每个任务有 `actual_count` 字段（来自真实扫描结果） |
| EXP-1.5 | 显示**其他指标**（用户可能没想到的） | auto | 至少含 2 项额外指标（如：检测率、严重度分布、扫描文件数、扫描耗时、误报数） |

---

## 诉求 2：Agent 博弈效果必须真实展示（不是文字描述）

> 反例：当前页面只写"审查员负责识别代码规范问题…"——这是描述 agent 干嘛，**不是效果**。

| 用例ID | 验证点 | 验证方法 | 通过标准 |
|--------|--------|----------|----------|
| EXP-2.1 | 展示**无 Agent（仅传统工具）**的基线效果 | auto | 有 `baseline` 真实扫描数据（semgrep/bandit/gitleaks/trivy，无 LLM agent） |
| EXP-2.2 | 展示**单 Agent** 的效果 | auto | 有 `single_agent` 真实扫描数据 |
| EXP-2.3 | 展示**多 Agent 博弈后**的效果 | auto | 有 `debate` 真实扫描数据（reviewer/security/fixer 辩论仲裁） |
| EXP-2.4 | 三种效果有**可对比的量化指标** | auto | 同一指标维度可对比（如检出数、确认漏洞数、误报数、严重度准确率） |
| EXP-2.5 | 支持**按单项目**查看，也支持**总体**查看 | auto+manual | 数据既有 per-project 也有 overall 聚合 |
| EXP-2.6 | 效果数据来自**真实扫描**，非硬编码 | auto | 数据可追溯到具体 scan_id，非前端写死 |
| EXP-2.7 | **不能只是文字描述 agent 职责** | manual | 博弈效果区块主体是量化对比（表/图），不是角色介绍文字 |

---

## 诉求 3：必须真实开源项目（绝对禁止伪造）

> 反例：setup_demo.py 用内联代码片段伪装成 "OWASP WebGoat/DVWA/NodeGoat/Rust/Go/C Examples"——**绝对禁止**。

| 用例ID | 验证点 | 验证方法 | 通过标准 |
|--------|--------|----------|----------|
| EXP-3.1 | 每个项目是**真实开源项目**，有有效 GitHub URL | auto | URL 匹配 `github.com/<org>/<repo>` 且可访问 |
| EXP-3.2 | 无项目 URL 为 `#` 或占位符 | auto | 所有 URL 非 `#`、非空、非 `example.com` |
| EXP-3.3 | 扫描数据来自**真实 clone 并扫描**该仓库 | auto | 项目 `repo_url` 非空，扫描走 `run-project`（真实 git clone），非内联代码 |
| EXP-3.4 | **不含 setup_demo.py 伪造样本** | auto | 排除伪造项目名单（见下），实验区只展示真实 clone 扫描的项目 |

**伪造项目黑名单**（这些是 setup_demo.py 用内联代码造的，禁止出现在实验区）：
- `OWASP WebGoat (Java)`（内联代码版，注意区别于真实 clone 的 `WebGoat (Real)`）
- `DVWA (PHP)`（内联代码版）
- `NodeGoat (Node.js)`（内联代码版）
- `Rust Security Examples`
- `Go Vulnerability Examples`
- `C Buffer Overflow Examples`
- 任何 `repo_url` 为空但号称是开源项目的记录

---

## 当前已知真实项目（实际 clone 扫描过的）

| 项目 | 真实仓库 | 语言 | 说明 |
|------|----------|------|------|
| Vulnerable-Flask-App | https://github.com/we45/Vulnerable-Flask-App | python | 故意含漏洞的 Flask 应用，已扫描（scan 8/12/15） |
| WebGoat (Real) | https://github.com/WebGoat/WebGoat | java | OWASP 官方漏洞项目，已扫描（scan 11） |

> 注：实验区应围绕**真实扫描过的项目**构建。如需更多样本，必须真实 clone 扫描，不得伪造。

---

## 第二轮诉求（2026-07-22 追加）

> 用户反馈：界面要支持多项目、漏洞要能看代码上下文、指标看不懂、样本要更权威（DVWA）。
> 这些是新增需求，测试用例随之扩充（旧用例仍有效）。

### 诉求 4：界面支持多项目（可扩展，不写死单个）

| 用例ID | 验证点 | 验证方法 | 通过标准 |
|--------|--------|----------|----------|
| EXP-4.1 | 数据源支持多项目 | auto | `projects` 是数组，可含 N 个项目 |
| EXP-4.2 | 前端有项目切换控件 | manual | 有 tabs/选择器，可切换查看不同项目 |
| EXP-4.3 | 界面不写死单项目 | manual | 新增项目无需改前端代码即可展示 |

### 诉求 5：漏洞展示位置 + 代码上下文（同扫描任务）

| 用例ID | 验证点 | 验证方法 | 通过标准 |
|--------|--------|----------|----------|
| EXP-5.1 | 实验区每个项目能展示漏洞列表 | auto | 项目数据含 `scan_id`，可取到漏洞列表 |
| EXP-5.2 | 漏洞能展开看代码上下文 | auto | 漏洞含非空 `code_snippet`（带行号） |
| EXP-5.3 | 漏洞有文件路径 + 行号 | auto | 漏洞含 `file_path` + `line_start` |

### 诉求 6：指标清晰（区分类别/实例，去掉难懂指标）

| 用例ID | 验证点 | 验证方法 | 通过标准 |
|--------|--------|----------|----------|
| EXP-6.1 | 明确区分"漏洞类别数"与"漏洞实例数" | auto | 数据有独立的类别数与实例数字段，不混用 |
| EXP-6.2 | 去掉冗余难懂指标 | auto | 对比指标不含 `confirmed_count`/`unique_types`（已确认看不懂） |
| EXP-6.3 | 主指标是"类别覆盖率 x/y" | auto | `detection_rate` 基于类别命中（ground_truth_hits/total） |
| EXP-6.4 | ground truth 标注来源 | auto | 项目含 `ground_truth_source` 字段（如"DVWA 官方模块列表"） |

### 诉求 7：DVWA 真实样本 + 已验证 ground truth

| 用例ID | 验证点 | 验证方法 | 通过标准 |
|--------|--------|----------|----------|
| EXP-7.1 | DVWA 是真实 clone 扫描的 | auto | DVWA 项目 `repo_url` = 真实 github 地址 |
| EXP-7.2 | DVWA ground truth = 19 类（官方实测） | auto | DVWA `ground_truth_total == 19`（来自官方 vulnerabilities/ 目录） |
| EXP-7.3 | DVWA 有三模式真实对比数据 | auto | DVWA `agent_comparison` 含 baseline/single_agent/debate |

**DVWA 19 类官方漏洞模块**（实测自 `vulnerabilities/` 目录）：
sqli, sqli_blind, xss_r, xss_s, xss_d, exec, fi, upload, csrf, brute, captcha, weak_id, authbypass, bac, open_redirect, csp, cryptography, javascript, api

---

## 验收门禁

- **所有 EXP-3.x、EXP-7.x 必须通过**（真实性是底线，一票否决）
- EXP-1.x、2.x、4.x、5.x、6.x 的 auto 项必须通过；manual 项需用户确认
- 自动化运行：`python scripts/verify_experiment.py`，全 PASS 退出码 0
