---
name: clawsqlite-knowledge
description: Knowledge base skill that wraps the clawsqlite knowledge CLI for ingest/search/maintenance.
version: 0.1.0
metadata: {"openclaw":{"homepage":"https://github.com/ernestyu/clawsqlite","tags":["knowledge","sqlite","search","cli"],"requires":{"bins":["python"],"env":[]},"install":[{"id":"clawsqlite_knowledge_bootstrap","kind":"python","label":"Install clawsqlite from PyPI","script":"bootstrap_deps.py"}],"runtime":{"entry":"run_clawknowledge.py"}}}
---

# clawsqlite-knowledge (OpenClaw Skill)

`clawsqlite-knowledge` 是一个围绕 PyPI 包 **clawsqlite** 构建的知识库 Skill。

它是一个**薄包装**：

- 不 vendor 源码，不 git clone 任何仓库；
- 安装阶段只做一件事：`pip install clawsqlite>=0.1.0`；
- 运行阶段只通过 `clawsqlite knowledge ...` CLI 操作知识库。

主要能力集中在三类：

1. **入库**
   - 从 URL 入库（结合现有抓取工具，例如 clawfetch）；
   - 从一段文本/想法/摘抄入库（标记为本地来源）。
2. **检索**
   - 混合检索（hybrid/FTS/vec 自动退级）
   - 按 id 查看完整记录（含全文）。
3. **维护**
   - 预览孤儿文件 / 备份 / 路径问题；
   - 应用一次清理 + VACUUM。

---

## 安装（由 ClawHub / OpenClaw 执行）

前提：

- Skill 运行环境中有 Python 3.10+；
- 可以访问 PyPI 安装 `clawsqlite` 包。

安装步骤由 `manifest.yaml` 声明：

```yaml
install:
  - id: clawsqlite_knowledge_bootstrap
    kind: python
    label: Install clawsqlite from PyPI
    script: bootstrap_deps.py
```

`bootstrap_deps.py` 的内容很简单，可以全文审计：

```python
cmd = [sys.executable, "-m", "pip", "install", "clawsqlite>=0.1.0"]
subprocess.run(cmd)
```

Skill 自身不会：

- 克隆任何 git 仓库；
- 在安装过程中安装未声明的额外包；
- 在运行阶段写入非工作目录。

---

## 运行时入口

Skill runtime 会调用 `run_clawknowledge.py`，该脚本：

- 从 stdin 读取一个 JSON payload；
- 根据 `action` 字段路由到对应的 handler；
- 调用 `python -m clawsqlite_cli knowledge ...` 完成实际操作；
- 把结果 JSON 写回 stdout。

所有调用都集中在一个函数中：

```python
cmd = [sys.executable, "-m", "clawsqlite_cli", "knowledge"] + args
subprocess.run(cmd, cwd=...)
```

---

## 支持的 action

### 1. `ingest_url`

从 URL 入库一篇文章。抓取逻辑由环境中的 `CLAWSQLITE_SCRAPE_CMD`
（推荐使用 clawfetch CLI）决定，本 Skill 不直接抓网页。

**Payload 示例：**

```json
{
  "action": "ingest_url",
  "url": "https://mp.weixin.qq.com/s/UzgKeQwWWoV4v884l_jcrg",
  "title": "微信文章: Ground Station 项目",      // 可选
  "category": "web",                           // 可选（默认 web）
  "tags": "wechat,ground-station",            // 可选
  "gen_provider": "openclaw",                 // 可选：openclaw|llm|off（默认 openclaw）
  "root": "/home/node/.openclaw/workspace/knowledge_root"  // 可选
}
```

**行为：**

- 调用 `clawsqlite knowledge ingest --url ...`；
- 默认通过 `provider=openclaw`：
  - 用 heuristic 生成长摘要（前 ~800 字，按句子/段落截断）；
  - 用 jieba/轻量算法生成标签；
  - 在 embedding 配置完整时，为长摘要生成向量写入 vec 表；
- 文件名使用拼音 + 英文 slug，易于跨平台存储；
- DB 中保留原始中文标题和 source_url。

**返回：**

```json
{
  "ok": true,
  "data": { "id": 1, "title": "...", "local_file_path": "...", ... }
}
```

### 2. `ingest_text`

从一段文本/想法/摘抄入库，标记为本地来源（source = Local）。

**Payload 示例：**

```json
{
  "action": "ingest_text",
  "text": "今天想到一个关于网络抓取架构的想法...",
  "title": "网络抓取架构随记",      // 可选，不给则自动生成
  "category": "idea",             // 可选（默认 note）
  "tags": "crawler,architecture", // 可选
  "gen_provider": "openclaw",     // 可选
  "root": "/home/node/.../knowledge_root"     // 可选
}
```

**行为：**

- 调用 `clawsqlite knowledge ingest --text ...`；
- 与 URL 场景一样生成长摘要/标签/向量（取决于配置）；
- `source_url` 将为 `Local`；
- 文件名使用拼音/英文 slug，方便跨平台。

### 3. `search`

按关键字/向量/混合检索知识库。

**Payload 示例：**

```json
{
  "action": "search",
  "query": "网络抓取 架构",
  "mode": "hybrid",               // 可选：hybrid|fts|vec（默认 hybrid）
  "topk": 10,                      // 可选
  "category": "idea",            // 可选
  "tag": "crawler",              // 可选
  "include_deleted": false,       // 可选
  "root": "/home/node/.../knowledge_root"     // 可选
}
```

**行为：**

- 调用 `clawsqlite knowledge search ...`；
- 当 embedding 启用且 vec 表存在时，`mode=hybrid` 会结合向量和 FTS；
- 当 embedding 未启用时，`mode=hybrid` 自动退化为纯 FTS；
- 支持按 category/tag 过滤，以及是否包含软删记录。

**返回：**

```json
{
  "ok": true,
  "data": [
    {"id": 3, "title": "...", "category": "idea", "score": 0.92, ...},
    ...
  ]
}
```

### 4. `show`

按 id 查看知识库中的一条记录，可选返回全文。

**Payload 示例：**

```json
{
  "action": "show",
  "id": 3,
  "full": true,                     // 可选，默认 true
  "root": "/home/node/.../knowledge_root"     // 可选
}
```

**行为：**

- 调用 `clawsqlite knowledge show --id ... --full --json`；
- 返回完整元数据与可选正文内容（`content` 字段）。

### 5. `maintenance_preview`

预览一次维护操作，检查孤儿文件/备份/路径问题，不执行删改。

**Payload 示例：**

```json
{
  "action": "maintenance_preview",
  "days": 3,                        // 可选，备份保留天数
  "root": "/home/node/.../knowledge_root"     // 可选
}
```

**行为：**

- 调用 `clawsqlite knowledge maintenance gc --days N --dry-run --json`；
- 报告：
  - `orphans`: 磁盘有文件但 DB 无记录；
  - `bak_to_delete`: `.bak_YYYYMMDD` 且早于保留天数；
  - `broken_records`: DB 中指向不存在路径的记录。

### 6. `maintenance_apply`

执行一次维护清理（慎用）。

**Payload 示例：**

```json
{
  "action": "maintenance_apply",
  "days": 7,
  "root": "/home/node/.../knowledge_root"
}
```

**行为：**

- 调用 `clawsqlite knowledge maintenance gc --days N --json`；
- 删除 `orphans + bak_to_delete`；
- 通过 plumbing 跑一次 `VACUUM` 压缩 DB；
- 返回 deleted 列表及状态。

---

## 安全与可审计性

- Skill 仅依赖 PyPI 上的 `clawsqlite` 包；
- 不 vendor 源码、不 git clone、不下载额外二进制；
- 所有对知识库的操作都通过显式的 `clawsqlite knowledge ...` CLI 完成，
  并且可以在日志中完整审计 `stdout/stderr`；
- 重度操作（maintenance_apply 等）建议只由管理员或预定的
  自动任务调用，不在普通对话中频繁触发。
