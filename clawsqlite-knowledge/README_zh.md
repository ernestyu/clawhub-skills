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
- 通过底层 `clawsqlite` CLI 做健康检查和清理（孤儿文件、备份、VACUUM）

具体的表结构、索引、Embedding、维护逻辑，都由 PyPI 包
`clawsqlite` 实现。`clawsqlite-knowledge` 只是一个薄薄的 JSON 封装，
让 Agent 调用更方便、更安全。

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

你可以简单理解为：

- 需要 **全功能 CLI / 算法** → 用 `clawsqlite`；
- 需要 **给 Agent 用的知识库 Skill** → 用 `clawsqlite-knowledge`。

---

## 2. 在 ClawHub / OpenClaw 中的安装

本 Skill 由 ClawHub / OpenClaw 负责安装和运行。

引导脚本会根据固定的版本约束从 PyPI 安装 `clawsqlite`。当前版本
要求为：

```text
clawsqlite>=0.1.2
```

这样可以保证本 Skill 依赖的标签生成、语义重排、查询关键词抽取和
混合打分权重等行为，与 `clawsqlite` 自身 README 中的说明保持一致。

- `manifest.yaml` 中声明了：
  - Python 运行环境；
  - 引导脚本：`bootstrap_deps.py`；
  - 运行入口：`run_clawknowledge.py`。
- `bootstrap_deps.py` 会安装 PyPI 上的 `clawsqlite>=0.1.2`：

  ```python
  requirement = "clawsqlite>=0.1.2"
  cmd = [sys.executable, "-m", "pip", "install", requirement]
  proc = subprocess.run(cmd)
  if proc.returncode != 0:
      prefix = _workspace_prefix()
      subprocess.run([
          sys.executable,
          "-m",
          "pip",
          "install",
          requirement,
          f"--prefix={prefix}",
      ])
  ```

Skill 不会：

- git clone 任意仓库；
- 额外再跑其它 `pip install`；
- 安装系统级依赖。

如果运行环境的 venv 只读，安装脚本会退回到
`<workspace>/.clawsqlite-venv`，运行时会自动把该前缀的
site-packages 加入 `PYTHONPATH`。

### 2.1 OpenClaw 主机上的推荐配置（workspace 本地）

向量检索（vec0）推荐在 workspace 下安装 sqlite-vec：

```bash
python -m pip install "sqlite-vec>=0.1.7" --prefix="./.sqlite-vec"
CLAWSQLITE_VEC_EXT=<workspace>/.sqlite-vec/lib/python3.X/site-packages/sqlite_vec/vec0.so
CLAWSQLITE_VEC_DIM=<你的 embedding 维度，例如 1024>
```

URL 入库推荐使用 workspace 内的 clawfetch：

```bash
CLAWSQLITE_SCRAPE_CMD="node <workspace>/clawfetch/clawfetch.js --auto-install"
```

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
- 失败：`{"ok": false, "error": "...", "exit_code": 1, "stdout": "...", "stderr": "..."}`；
- 若底层 CLI 输出 `NEXT:` 提示，会在返回中附带 `next` 数组；
- 失败时还会包含 `error_kind` 字段，粗略标记错误类型（例如
  `missing_scraper` / `missing_embedding` / `other`）。

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
- 建议在环境中配置 `CLAWSQLITE_SCRAPE_CMD` 为 clawfetch Skill/CLI；
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

底层调用的是 `clawsqlite knowledge search ...`，并且继承了
clawsqlite 在 0.1.2 版本中的新版行为：

- hybrid 检索：向量 + FTS 的混合模式，在 Embedding 或 vec0
  不可用时自动退化为纯 FTS；
- 标签感知打分：标签由 TextRank/TF‑IDF +（可选的）语义向心力生成，
  并以 0..1 的得分参与最终排序；
- 查询关键词抽取：自然语言问句会先经过与标签生成相同的
  TextRank + 语义向心力流水线抽取少量关键词，再喂给 FTS。

混合打分的权重可以通过 `CLAWSQLITE_SCORE_WEIGHTS` 环境变量进行微调，
具体含义见 `ENV_EXAMPLE.md` 及底层 `clawsqlite` README。

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

---

## 5. 错误处理与 NEXT 提示

底层 `clawsqlite` CLI 为 Agent 设计，所有错误都会带一条
`NEXT: ...` 导航提示，例如：

```text
ERROR: db not found at /path/to/db. Check --root/--db or .env configuration.
NEXT: set --root/--db (or CLAWSQLITE_ROOT/CLAWSQLITE_DB) to an existing knowledge_data directory, or run an ingest command first to initialize the DB.
```

`run_clawknowledge.py` 在 CLI 退出码非 0 时，会解析这些 `NEXT:` 行，
将其放入返回 JSON 的 `next` 数组，并设置 `error_kind` 字段，方便
上层 Agent 根据错误类型和 NEXT 做下一步动作。

---

## 6. 什么时候用 clawsqlite-knowledge，什么时候直接用 clawsqlite？

适合用 **clawsqlite-knowledge** 的场景：

- 在 ClawHub/OpenClaw 中，需要一个「个人知识库 Skill」给 Agent 调；
- 日常主要操作是：URL / 文本入库、搜索、按 id 查看记录。

适合直接用 **clawsqlite** 的场景：

- 需要对知识库的 schema/索引/Embedding 流程有完全掌控；
- 需要 plumbing 命令：
  - `clawsqlite db schema/exec/backup/vacuum`
  - `clawsqlite index check/rebuild`
  - `clawsqlite fs list-orphans/gc`
  - `clawsqlite embed column`
- 正在开发新的应用，而不是单一的个人知识库。

两者可以复用同一套数据根目录（`CLAWSQLITE_ROOT` / `CLAWSQLITE_DB` /
`CLAWSQLITE_ARTICLES_DIR`），方便你在 CLI 和 Skill 之间切换。
### 中文 FTS 退级：libsimple 缺失时的 jieba 模式

本 Skill 在分词与检索层面完全依赖底层 `clawsqlite` 的实现。当
`libsimple`（CJK tokenizer 扩展）无法加载时，可以通过
`CLAWSQLITE_FTS_JIEBA=auto|on|off` 启用 `jieba` 预分词模式：

- `auto`（默认）：仅当 `libsimple` 无法加载且环境中有 `jieba` 时启用；
- `on`：强制启用 jieba 预分词（即使 `libsimple` 可用）；
- `off`：禁用 jieba 预分词。

在 jieba 模式下，CJK 文本会先用 jieba 分词并用空格拼接后写入 FTS；
查询侧也使用同样的规则归一化，因此写入 / 重建 / 查询保持一致。
英文文本不受影响。

如果在已有数据库上切换该模式，建议执行：

```bash
clawsqlite knowledge reindex --rebuild --fts
```

让 FTS 索引按当前 tokenizer 配置（simple 或 jieba 退级）重建。
详细行为说明见 `clawsqlite` 仓库的 README/README_zh。

---

## 7. 升级说明（clawsqlite>=0.1.2）

- 本 Skill 依赖 `clawsqlite>=0.1.2`，更新时会通过 `bootstrap_deps.py` 安装新的 PyPI 版本。
- 在 OpenClaw 中，推荐的下发流程是：`openclaw skills update clawsqlite-knowledge`，如同时调整了 `CLAWSQLITE_FTS_JIEBA`，再执行一次 FTS 重建。
