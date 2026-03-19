---
name: clawhealth-garmin
description: 轻量级 Garmin Connect 技能：运行时从 GitHub 拉取 clawhealth 源码，同步健康数据到本地 SQLite，并提供 JSON 命令给 OpenClaw。
metadata: {"openclaw":{"requires":{"bins":["python"]},"homepage":"https://github.com/ernestyu/clawhealth","tags":["health","garmin","sqlite","cli"]}}
---

# clawhealth-garmin（OpenClaw 技能）

该技能连接 Garmin Connect，同步健康数据到本地 SQLite，并提供
JSON 友好的命令给 OpenClaw 调用。

这是**轻量版**技能包：**不包含** `clawhealth` 源代码，安装/运行时只会从
GitHub 拉取 `src/clawhealth` 目录。

## 功能概述

- 使用用户名/密码登录（支持 MFA）
- 同步每日健康摘要到 SQLite（阶段 1）
- HRV / 训练指标等单独命令获取（阶段 2）
- 睡眠分期 + 睡眠评分（阶段 2）
- 体成分（阶段 2）
- 活动列表与活动详情（阶段 2）
- 月经日视图与日历范围（实验性，需 garminconnect 支持）
- 支持 `--json` 输出，方便代理调用
- 保存原始 JSON 便于后续分析

## 先决条件

- Python 3.10+
- 可访问 GitHub 与 Garmin Connect 的网络
- Garmin 账号（可能需要 MFA）
- 可选：`git`（建议安装；没有 git 会回退到 GitHub zip 下载）

如果在 Docker 里运行 OpenClaw，可考虑预打包依赖的镜像：

- `ernestyu/openclaw-patched`

## 安装与配置

1) 创建 `{baseDir}/.env`（参考 `{baseDir}/ENV.example`）。

建议使用 `CLAWHEALTH_GARMIN_PASSWORD_FILE`（密码文件）而不是
`CLAWHEALTH_GARMIN_PASSWORD`（明文环境变量）。

注意：如 `./garmin_pass.txt` 等相对路径会被视为相对技能目录。

2) 拉取 `clawhealth` 源码（可选；首次运行会自动拉取）：

```bash
python {baseDir}/fetch_src.py
```

3) 安装 Python 依赖（如需要）：

```bash
python {baseDir}/bootstrap_deps.py
```

备注：

- 默认下载到 `{baseDir}/clawhealth_src`（仅包含 `src/clawhealth`）
- 可通过 `CLAWHEALTH_SRC_DIR / CLAWHEALTH_REPO_URL / CLAWHEALTH_REPO_REF` 覆盖
- `run_clawhealth.py` 会在源码缺失时自动拉取（`CLAWHEALTH_AUTO_FETCH`）
- `run_clawhealth.py` 会在依赖缺失时自动引导安装（`CLAWHEALTH_AUTO_BOOTSTRAP`）
- 若存在 `{baseDir}/.venv`，会自动切换到虚拟环境执行
- 若临时目录权限不足，可设置 `CLAWHEALTH_TMP_DIR` 到可写路径

## 基础命令

登录（可能返回 `NEED_MFA`）：

```bash
python {baseDir}/run_clawhealth.py garmin login --username you@example.com --json
```

完成 MFA：

```bash
python {baseDir}/run_clawhealth.py garmin login --mfa-code 123456 --json
```

同步：

```bash
python {baseDir}/run_clawhealth.py garmin sync --since 2026-03-01 --until 2026-03-03 --json
```

状态：

```bash
python {baseDir}/run_clawhealth.py garmin status --json
```

每日摘要：

```bash
python {baseDir}/run_clawhealth.py daily-summary --date 2026-03-03 --json
```

## 高级数据端点（阶段 2）

### HRV（按日期）

```bash
python {baseDir}/run_clawhealth.py garmin hrv-dump --date 2026-03-03 --json
```

注意：

- 先对同一日期执行 `garmin sync`，HRV 才能映射进 `uhm_daily`。

### 训练就绪 / 状态 / 耐力 / 体能年龄（当天）

```bash
python {baseDir}/run_clawhealth.py garmin training-metrics --json
```

注意：

- 该命令默认使用“今天”的数据；请先同步当天数据。

### 睡眠分期 + 睡眠评分

```bash
python {baseDir}/run_clawhealth.py garmin sleep-dump --date 2026-03-03 --json
```

### 体成分

```bash
python {baseDir}/run_clawhealth.py garmin body-composition --date 2026-03-03 --json
```

### 活动（列表 + 详情）

```bash
python {baseDir}/run_clawhealth.py garmin activities --since 2026-03-01 --until 2026-03-03 --json
python {baseDir}/run_clawhealth.py garmin activity-details --activity-id 123456789 --json
```

### 月经数据（实验性，需 garminconnect 支持）

```bash
python {baseDir}/run_clawhealth.py garmin menstrual --date 2026-03-03 --json
python {baseDir}/run_clawhealth.py garmin menstrual-calendar --since 2026-03-01 --until 2026-03-31 --json
```

## 诊断与分析

### 趋势摘要（滑动窗口均值）

```bash
python {baseDir}/run_clawhealth.py garmin trend-summary --days 7 --json
```

### 健康提示（简单告警）

```bash
python {baseDir}/run_clawhealth.py garmin flags --days 7 --json
```

## 数据位置

- Token / 配置：`{baseDir}/config`
- SQLite 数据库：`{baseDir}/data/health.db`

可通过 `CLAWHEALTH_CONFIG_DIR` 与 `CLAWHEALTH_DB` 覆盖。

## 发布校验

```bash
python {baseDir}/validate_skill.py
python {baseDir}/test_minimal.py
```

可选：真实账号集成测试

```bash
CLAWHEALTH_RUN_INTEGRATION_TESTS=1 python {baseDir}/test_integration_optional.py
```

## 安全建议

- 不要打印/记录明文凭据
- 优先使用密码文件
- 数据本地保存（SQLite + 本地 token）

## 当前限制

- 活动 / 月经 / 体成分目前仅保存原始 JSON，尚无结构化明细
- 月经接口依赖 garminconnect 支持，否则会返回 `UNSUPPORTED_ENDPOINT`
- 部分指标依赖特定设备或账号设置
- HRV 需要按日期补齐；训练指标默认以“当天”为目标
