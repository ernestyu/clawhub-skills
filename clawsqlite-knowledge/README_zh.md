# clawsqlite-knowledge（ClawHub Skill）

`clawsqlite-knowledge` 是一个围绕
[clawsqlite](https://github.com/ernestyu/clawsqlite) **knowledge** CLI
封装的 ClawHub 技能。

它不是通用的 SQLite 工具，而是专门为 OpenClaw/ClawHub 场景做的
「日常知识库操作面板」：

- 从网页 URL 入库 → markdown + SQLite
- 把你的想法/随记/摘抄入库
- 在知识库里检索（FTS / hybrid / vec 自动退级）
- 按 id 查看某条记录
- 做基本的健康检查和清理（孤儿文件、备份、VACUUM）

具体的表结构、索引、Embedding、维护逻辑，都由 PyPI 包
`clawsqlite` 实现。`clawknowledge` 只是一个薄薄的 JSON 封装，让
Agent 调用更方便、更安全。

> 如果你需要完全控制 clawsqlite 的所有能力（包括 plumbing 命令、
> 自己的表、复杂流水线），应该直接使用 `clawsqlite` 包和 CLI，
> 而不是这个 Skill。

---

## 1. 与 clawsqlite 的关系

- **clawsqlite（PyPI / GitHub 仓库）**
  - 一个通用的 SQLite + 知识库 CLI/库；
  - 暴露多个一级命令：`clawsqlite knowledge|db|index|fs|embed`；
  - 适合在 shell 里直接用，也适合写脚本、做其它应用。

- **clawsqlite-knowledge（本 Skill）**
  - 代码目录：`clawhub-skills/clawsqlite-knowledge`；
  - 由 ClawHub 安装并运行；
  - 依赖 PyPI 上的 `clawsqlite` 包（不 vendor 源码，不 git clone）；
  - 对外暴露一个小而精的 JSON API：
    - `ingest_url`
    - `ingest_text`
    - `search`
    - `show`
    - `maintenance_preview`
    - `maintenance_apply`

你可以简单理解为：

- 需要**全功能 CLI / 算法** → 用 `clawsqlite`；
- 需要**给 Agent 用的知识库 Skill** → 用 `clawsqlite-knowledge`。

---

## 2. 在 ClawHub 中的安装

本 Skill 由 ClawHub 负责安装和运行。

- `manifest.yaml` 中声明了：
  - Python 运行环境；
  - 引导脚本：`bootstrap_deps.py`；
  - 运行入口：`run_clawknowledge.py`。
- `bootstrap_deps.py` 做的事情非常简单，只安装 PyPI 包：

  ```python
  cmd = [sys.executable, "-m", "pip", "install", "clawsqlite>=0.1.0"]
  subprocess.run(cmd)
  ```

Skill 不会：

- git clone 任意仓库；
- 额外再跑其它 `pip install`；
- 安装系统级依赖。

ClawHub 完成安装后，Agent 通过向 `run_clawknowledge.py` 写入 JSON
即可调用本 Skill。

---

## 3. 运行约定

`run_clawknowledge.py` 的约定是：

- 从 stdin 读入一个 JSON 对象；
- 读取 `action` 字段，根据不同 action 调用不同 handler；
- 在内部执行：`python -m clawsqlite_cli knowledge ...`；
- 最后把结果 JSON 写回 stdout。

通用字段：

- `root`（可选）：知识库根目录覆盖；
- `action`：下文列出的几种之一。

返回格式统一为：

- 成功：`{"ok": true, "data": {...}}`；
- 失败：`{"ok": false, "error": "...", "exit_code": 1, "stdout": "...", "stderr": "..."}`。

---

## 4. 支持的 actions

### 4.1 `ingest_url`

从 URL 入库一篇文章。

**Payload 示例：**

```json
{
  "action": "ingest_url",
  "url": "https://mp.weixin.qq.com/s/UzgKeQwWWoV4v884l_jcrg",
  "title": "微信文章: Ground Station 项目",
  "category": "web",
  "tags": "wechat,ground-station",
  "gen_provider": "openclaw",
  "root": "/home/node/.openclaw/workspace/knowledge_data"
}
```

说明：

- 真正的网页抓取由 `clawsqlite knowledge ingest --url ...` 调用的
  抓取脚本完成；
- 建议在环境中配置 `CLAWSQLITE_SCRAPE_CMD` 为 `clawfetch` Skill/CLI；
- `ingest_url` 只负责把 JSON 请求翻译成 CLI 调用，并返回 JSON 结果。

### 4.2 `ingest_text`

从一段文本/想法/摘抄入库，标记为本地来源。

**Payload 示例：**

```json
{
  "action": "ingest_text",
  "text": "今天想到一个关于网络抓取架构的想法……",
  "title": "网络抓取架构随记",
  "category": "idea",
  "tags": "crawler,architecture",
  "gen_provider": "openclaw",
  "root": "/home/node/.openclaw/workspace/knowledge_data"
}
```

适用场景：

- 突然想到的点子 / 设计想法；
- 书里/小说里的金句摘抄；
- 你和 Agent 对话时，让它“帮我记一下”。

底层 `clawsqlite knowledge ingest --text ...` 会：

- 生成一段较长摘要（约 800 字以内，非硬截）；
- 用 jieba/启发式抽标签；
- 在配置了 Embedding 的情况下，为摘要打向量并写入 vec 表；
- 用拼音/ASCII 生成文件名，在 articles 目录下写入 markdown。

### 4.3 `search`

在知识库中检索。

**Payload 示例：**

```json
{
  "action": "search",
  "query": "网络爬虫 架构",
  "mode": "hybrid",
  "topk": 10,
  "category": "idea",
  "tag": "crawler",
  "include_deleted": false,
  "root": "/home/node/.openclaw/workspace/knowledge_data"
}
```

语义：

- `mode=hybrid`：
  - 如果 Embedding + vec 表可用 → 用向量 + FTS 混合检索；
  - 如果不可用 → 自动退化为 FTS；
- 支持按 `category` / `tag` / `since` / `priority` 等过滤；
- 返回结果里包含 `id` / `title` / `category` / `score` / `created_at` 等字段。

### 4.4 `show`

按 id 查看单条记录。

**Payload 示例：**

```json
{
  "action": "show",
  "id": 3,
  "full": true,
  "root": "/home/node/.openclaw/workspace/knowledge_data"
}
```

- `full=true` 时，会通过 `clawsqlite knowledge show --full` 返回正文内容；
- 适合在 Agent 侧拿到 id 之后，拉取完整上下文进行总结、重写等操作。

### 4.5 `maintenance_preview`

预览一次维护操作，不做任何删除。

**Payload 示例：**

```json
{
  "action": "maintenance_preview",
  "days": 3,
  "root": "/home/node/.openclaw/workspace/knowledge_data"
}
```

对应 CLI：`clawsqlite knowledge maintenance gc --days N --dry-run`，返回：

- `orphans`：磁盘有文件但 DB 无记录；
- `bak_to_delete`：早于保留期的 `.bak_YYYYMMDD` 文件；
- `broken_records`：DB 里指向不存在文件的记录。

### 4.6 `maintenance_apply`

真正执行一次清理（删除孤儿和过期备份）并 VACUUM DB。

**Payload 示例：**

```json
{
  "action": "maintenance_apply",
  "days": 7,
  "root": "/home/node/.openclaw/workspace/knowledge_data"
}
```

对应 CLI：`clawsqlite knowledge maintenance gc --days N`，返回：

- 删除了哪些文件；
- 是否执行了 VACUUM。

> 建议把 `maintenance_apply` 限制在管理员或 cron 场景，避免在对话里频繁调用。

---

## 5. 错误处理与 NEXT 提示

底层 `clawsqlite` CLI 为 Agent 设计，所有错误都会带一条
`NEXT: ...` 导航提示，例如：

```text
ERROR: db not found at /path/to/db. Check --root/--db or .env configuration.
NEXT: set --root/--db (or CLAWSQLITE_ROOT/CLAWSQLITE_DB) to an existing knowledge_data directory, or run an ingest command first to initialize the DB.
```

`run_clawknowledge.py` 在 CLI 退出码非 0 时，会把这些信息一并放入
JSON 返回值中，方便 Agent 根据 `NEXT` 做下一步动作。

---

## 6. 什么时候用 clawknowledge，什么时候直接用 clawsqlite？

**适合用 clawknowledge 的场景：**

- 在 ClawHub/OpenClaw 中，需要一个「个人知识库 Skill」给 Agent 调；
- 日常主要操作是：
  - 入库（URL / 文本）；
  - 搜索；
  - 查看单条记录；
  - 偶尔做一次维护预览/清理。

**适合直接用 clawsqlite 的场景：**

- 需要对知识库的 schema/索引/Embedding 流程有完全掌控；
- 需要 plumbing 命令：
  - `clawsqlite db schema/exec/backup/vacuum`；
  - `clawsqlite index check/rebuild`；
  - `clawsqlite fs list-orphans/gc`；
  - `clawsqlite embed column`；
- 正在开发新的应用，而不是单一的个人知识库。

两者的定位不同，但可以复用同一套数据根目录
(`CLAWSQLITE_ROOT` / `CLAWSQLITE_DB` / `CLAWSQLITE_ARTICLES_DIR`)，方便你在
CLI 和 Skill 之间切换。