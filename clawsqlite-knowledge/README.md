# clawsqlite-knowledge (ClawHub Skill)

`clawsqlite-knowledge` is a ClawHub skill that wraps the
[clawsqlite](https://github.com/ernestyu/clawsqlite) **knowledge** CLI and
exposes a small, opinionated API for day‑to‑day knowledge base work.

It is **not** a generic SQLite tool. Instead, it focuses on the common
operations you actually want to automate in OpenClaw agents:

- Ingest articles from the web (URL → markdown + SQLite)
- Ingest your own notes/ideas/quotes as text
- Search the knowledge base (FTS / hybrid / vec)
- Show a single record by id
- Run basic maintenance (orphan detection + GC)

All heavy lifting (schema, indexing, embedding, maintenance) is implemented
in the `clawsqlite` PyPI package. This skill is just a thin, auditable
wrapper.

> If you need full control over `clawsqlite` (plumbing commands, custom
> tables, advanced CLIs), use the Python package and CLI directly instead of
> this skill.

---

## 1. Relationship to clawsqlite

- **clawsqlite (PyPI / GitHub)**
  - A general‑purpose CLI and library for SQLite‑backed knowledge bases.
  - Exposes multiple namespaces: `clawsqlite knowledge|db|index|fs|embed`.
  - Suitable for direct shell use, scripting, and other applications.

- **clawsqlite-knowledge (this skill)**
  - Lives under `clawhub-skills/clawsqlite-knowledge`.
  - Installed inside the ClawHub environment as a skill.
  - Depends on `clawsqlite` via PyPI (no vendored source, no git clone).
  - Exposes a **small JSON API** over stdin/stdout:
    - `ingest_url`
    - `ingest_text`
    - `search`
    - `show`
    - `maintenance_preview`
    - `maintenance_apply`

The idea is:

- Use `clawsqlite` when you want the **full CLI** and Python library;
- Use `clawsqlite-knowledge` when you want a **high‑level skill** your agents can
  call to manage a personal knowledge base.

---

## 2. Installation (ClawHub)

This skill is meant to be installed and run by ClawHub.

- The skill manifest (`manifest.yaml`) declares:
  - A Python runtime
  - A bootstrap script: `bootstrap_deps.py`
  - The runtime entry: `run_clawknowledge.py`
- The bootstrap script installs `clawsqlite` and falls back to a workspace-local
  prefix if the runtime env is not writable:

  ```python
  cmd = [sys.executable, "-m", "pip", "install", "clawsqlite>=0.1.0"]
  proc = subprocess.run(cmd)
  if proc.returncode != 0:
      subprocess.run([...,"--prefix=.clawsqlite-venv"])
  ```

There are **no** git clones, no extra `pip install` calls, and no system
package installs at runtime. All heavy code lives in the public
`clawsqlite` package.

Once installed by ClawHub, agents can invoke the skill by sending JSON
payloads to `run_clawknowledge.py`.

---

### 2.1 OpenClaw workspace-friendly setup (recommended)

If the OpenClaw runtime uses a read-only venv, the bootstrap fallback installs
`clawsqlite` under `<workspace>/.clawsqlite-venv`. The runtime auto-adds that
prefix site-packages directory to `PYTHONPATH` when present.

For vector search (vec0), a workspace-local sqlite-vec install is the safest:

```bash
python -m pip install "sqlite-vec>=0.1.7" --prefix="./.sqlite-vec"
CLAWSQLITE_VEC_EXT=<workspace>/.sqlite-vec/lib/python3.X/site-packages/sqlite_vec/vec0.so
CLAWSQLITE_VEC_DIM=<your-embedding-dim>
```

For URL ingestion, configure a workspace scraper (clawfetch):

```bash
CLAWSQLITE_SCRAPE_CMD="node <workspace>/clawfetch/clawfetch.js --auto-install"
```

---

## 3. Runtime contract

The runtime entry `run_clawknowledge.py`:

- Reads a JSON object from stdin
- Inspects the `action` field
- Dispatches to a handler
- Calls `python -m clawsqlite_cli knowledge ...` under the hood
- Writes a JSON result to stdout

Common fields:

- `root` (optional): override the knowledge root directory
- `action`: one of the supported actions below

All handlers return a JSON object with at least:

- `ok: true|false`
- `data: ...` on success, or `error` / `exit_code` / `stdout` / `stderr` on failure
- `next: [...]` when the underlying CLI emits NEXT hints
- `error_kind` on failures (e.g., missing scraper / vec / permission)

---

## 4. Supported actions

### 4.1 `ingest_url`

Ingest a web article via URL.

**Payload example:**

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

Notes:

- Actual scraping is done by `clawsqlite knowledge ingest --url ...` using
  the configured `CLAWSQLITE_SCRAPE_CMD` (recommended: the `clawfetch`
  skill/CLI).
- `ingest_url` only wraps that CLI call and returns the JSON result.

### 4.2 `ingest_text`

Ingest a note/idea/quote as plain text.

**Payload example:**

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

This is the path for:

- spontaneous ideas
- quotes from books/novels
- short notes you dictate to an agent

The underlying `clawsqlite knowledge ingest --text ...` call will:

- Generate a long summary (up to ~800 characters, soft‑truncated)
- Extract tags using jieba/heuristics
- Optionally embed the summary (when embedding is configured)
- Store a markdown file with a pinyin/ASCII slug filename

### 4.3 `search`

Search the knowledge base.

**Payload example:**

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

Semantics:

- `mode=hybrid`:
  - If embeddings + vec table are available: use vec + FTS hybrid
  - If not: automatically downgrade to FTS‑only
- Filters by `category`, `tag`, optional `since`/`priority`

The result is a list of hits with `id`, `title`, `category`, `score`,
`created_at`, etc.

### 4.4 `show`

Retrieve a single record by id.

**Payload example:**

```json
{
  "action": "show",
  "id": 3,
  "full": true,
  "root": "/home/node/.openclaw/workspace/knowledge_data"
}
```

When `full=true`, the handler uses `clawsqlite knowledge show --full`
under the hood and returns the markdown content as well.

### 4.5 `maintenance_preview`

Preview maintenance (no deletions).

**Payload example:**

```json
{
  "action": "maintenance_preview",
  "days": 3,
  "root": "/home/node/.openclaw/workspace/knowledge_data"
}
```

This runs `clawsqlite knowledge maintenance gc --days N --dry-run` and
returns:

- `orphans`: files without DB records
- `bak_to_delete`: old `.bak_YYYYMMDD` files
- `broken_records`: DB rows pointing to missing files

### 4.6 `maintenance_apply`

Apply maintenance (delete orphans and old backups, run VACUUM).

**Payload example:**

```json
{
  "action": "maintenance_apply",
  "days": 7,
  "root": "/home/node/.openclaw/workspace/knowledge_data"
}
```

This runs `clawsqlite knowledge maintenance gc --days N` and returns a
summary of deletions and whether a VACUUM ran.

> Use this action carefully; it is best suited for admin/cron flows, not
> frequent interactive calls.

---

## 5. Error handling & NEXT hints

The underlying `clawsqlite` CLI is designed for agents and prints
navigation‑style error hints, e.g.:

```text
ERROR: db not found at /path/to/db. Check --root/--db or .env configuration.
NEXT: set --root/--db (or CLAWSQLITE_ROOT/CLAWSQLITE_DB) to an existing knowledge_data directory, or run an ingest command first to initialize the DB.
```

`run_clawknowledge.py` captures non‑zero exit codes and returns them in the
JSON response so agents can inspect and act on these hints.
It also surfaces `NEXT` hints as a structured `next` array and adds an
`error_kind` field so agents can decide the next action (e.g., missing
scraper, vec extension, or permissions).

---

## 6. When to use this skill vs. clawsqlite directly

Use **clawknowledge** when:

- You are inside ClawHub/OpenClaw and want a high‑level knowledge base
  skill for agents.
- You mostly need:
  - URL/text ingest
  - search
  - show
  - light maintenance

Use **clawsqlite (PyPI/CLI)** when:

- You want full flexibility over the knowledge DB and pipelines.
- You need plumbing commands like:
  - `clawsqlite db schema/exec/backup/vacuum`
  - `clawsqlite index check/rebuild`
  - `clawsqlite fs list-orphans/gc`
  - `clawsqlite embed column`
- You are writing new applications beyond a single personal KB.
