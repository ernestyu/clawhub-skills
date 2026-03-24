---
name: clawsqlite-knowledge
description: Knowledge base skill that wraps the clawsqlite knowledge CLI for ingest/search/maintenance.
version: 0.1.6
metadata: {"openclaw":{"homepage":"https://github.com/ernestyu/clawsqlite","tags":["knowledge","sqlite","search","cli"],"requires":{"bins":["python"],"env":[]},"install":[{"id":"clawsqlite_knowledge_bootstrap","kind":"python","label":"Install clawsqlite from PyPI","script":"bootstrap_deps.py"}],"runtime":{"entry":"run_clawknowledge.py"}}}
---

# clawsqlite-knowledge (OpenClaw Skill)

`clawsqlite-knowledge` is a knowledge base Skill built around the PyPI package **clawsqlite**.

It is a **thin wrapper**:

- it does not vendor the source code and does not git clone any repository;
- during installation, it installs `clawsqlite>=0.1.0` (with a workspace-prefix fallback when the runtime env is not writable);
- during runtime, it operates the knowledge base only through the `clawsqlite knowledge ...` CLI.

Its main capabilities are grouped into three areas:

1. **Ingestion**
   - ingest from a URL (together with an existing fetch tool such as clawfetch);
   - ingest from a piece of text, an idea, or an excerpt (marked as a local source).
2. **Retrieval**
   - hybrid retrieval (hybrid / FTS / vec with automatic fallback)
   - show a full record by id (including full content).
3. **Maintenance**
   - preview orphan files, backups, and path issues;
   - apply one cleanup pass plus VACUUM.

---

## Installation (performed by ClawHub / OpenClaw)

Prerequisites:

- Python 3.10+ is available in the Skill runtime environment;
- the environment can access PyPI to install the `clawsqlite` package.

The installation steps are declared by `manifest.yaml`:

```yaml
install:
  - id: clawsqlite_knowledge_bootstrap
    kind: python
    label: Install clawsqlite from PyPI
    script: bootstrap_deps.py
````

The content of `bootstrap_deps.py` is intentionally simple and can be audited in full:

```python
cmd = [sys.executable, "-m", "pip", "install", "clawsqlite>=0.1.0"]
proc = subprocess.run(cmd)
if proc.returncode != 0:
    subprocess.run([...,"--prefix=.clawsqlite-venv"])
```

The Skill itself will not:

* clone any git repository;
* install undeclared extra packages during installation.

Note: The underlying `clawsqlite` CLI **will** read and write files under the
configured knowledge storage directory (SQLite DB file + markdown articles).
This Skill forwards the optional `root` field in the payload directly to the
CLI (mapped to `--root`), so callers control where those files live. In
ClawHub deployments, this is expected to be a dedicated data directory for
this skill.

If the workspace-prefix fallback is used, the runtime auto-adds the prefix
site-packages directory to `PYTHONPATH` before invoking the CLI.

---

## Runtime entry

The Skill runtime calls `run_clawknowledge.py`. This script:

* reads a JSON payload from stdin;
* routes by the `action` field to the matching handler;
* calls `python -m clawsqlite_cli knowledge ...` to perform the actual operation;
* writes the result JSON back to stdout.

All CLI calls are centralized in one function:

```python
cmd = [sys.executable, "-m", "clawsqlite_cli", "knowledge"] + args
subprocess.run(cmd, cwd=...)
```

If the underlying CLI emits `NEXT:` hints, this runtime surfaces them as a
structured `next` array in the JSON response. On failure, it also includes an
`error_kind` field for quick classification.

---

## Supported actions

### 1. `ingest_url`

Ingest an article from a URL. The actual fetching logic is determined by the environment variable `CLAWSQLITE_SCRAPE_CMD`
(recommended: the clawfetch CLI). This Skill does not fetch web pages directly.

**Example payload:**

```json
{
  "action": "ingest_url",
  "url": "https://mp.weixin.qq.com/s/UzgKeQwWWoV4v884l_jcrg",
  "title": "WeChat article: Ground Station project",   // optional
  "category": "web",                                   // optional (default: web)
  "tags": "wechat,ground-station",                     // optional
  "gen_provider": "openclaw",                          // optional: openclaw|llm|off (default: openclaw)
  "root": "/data/clawsqlite-knowledge"  // optional storage directory
}
```

**Behavior:**

* calls `clawsqlite knowledge ingest --url ...`;
* by default uses `provider=openclaw`:

  * generates a long summary with heuristics (first ~800 characters, cut by sentence/paragraph boundaries);
  * generates tags with jieba or a lightweight algorithm;
  * if embedding configuration is complete, generates an embedding for the long summary and stores it in the vec table;
* filenames use pinyin plus an English slug for easier cross-platform storage;
* the database keeps the original Chinese title and `source_url`.

**Returns:**

```json
{
  "ok": true,
  "data": { "id": 1, "title": "...", "local_file_path": "...", ... }
}
```

### 2. `ingest_text`

Ingest a piece of text, an idea, or an excerpt, marked as a local source (`source = Local`).

**Example payload:**

```json
{
  "action": "ingest_text",
  "text": "Today I had an idea about a web scraping architecture...",
  "title": "Notes on web scraping architecture",   // optional; auto-generated if omitted
  "category": "idea",                              // optional (default: note)
  "tags": "crawler,architecture",                  // optional
  "gen_provider": "openclaw",                      // optional
  "root": "/data/clawsqlite-knowledge"          // optional storage directory
}
```

**Behavior:**

* calls `clawsqlite knowledge ingest --text ...`;
* generates long summary, tags, and embedding the same way as in the URL case, depending on configuration;
* `source_url` will be `Local`;
* filenames use pinyin / English slug for easier cross-platform handling.

### 3. `search`

Search the knowledge base by keyword, vector, or hybrid retrieval.

**Example payload:**

```json
{
  "action": "search",
  "query": "web scraping architecture",
  "mode": "hybrid",               // optional: hybrid|fts|vec (default: hybrid)
  "topk": 10,                     // optional
  "category": "idea",             // optional
  "tag": "crawler",               // optional
  "include_deleted": false,       // optional
  "root": "/data/clawsqlite-knowledge"   // optional storage directory
}
```

**Behavior:**

* calls `clawsqlite knowledge search ...`;
* when embeddings are enabled and the vec table exists, `mode=hybrid` combines vector search and FTS;
* when embeddings are not enabled, `mode=hybrid` automatically falls back to pure FTS;
* supports filtering by `category` / `tag`, and whether to include soft-deleted records.

**Returns:**

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

Show one record from the knowledge base by id, optionally including full content.

**Example payload:**

```json
{
  "action": "show",
  "id": 3,
  "full": true,                   // optional, default: true
  "root": "/data/clawsqlite-knowledge"   // optional storage directory
}
```

**Behavior:**

* calls `clawsqlite knowledge show --id ... --full --json`;
* returns full metadata and optional body content (the `content` field).

---

## Maintenance (CLI only)

This skill intentionally does **not** expose destructive maintenance actions
via its JSON API. To clean up orphan files, old backups, or compact the
knowledge database, use the `clawsqlite` CLI directly from a trusted
administrative context, for example:

```bash
# Preview maintenance (no deletions)
clawsqlite knowledge maintenance gc \
  --root /data/clawsqlite-knowledge \
  --days 3 \
  --dry-run \
  --json

# Apply maintenance (delete orphans + old backups, then VACUUM)
clawsqlite knowledge maintenance gc \
  --root /data/clawsqlite-knowledge \
  --days 7 \
  --json
```

Only administrators or scheduled automation should run these commands. Agents
using the `clawsqlite-knowledge` skill have access only to ingestion,
retrieval, and show operations.

---

## Security and auditability

* The Skill depends only on the `clawsqlite` package from PyPI;
* it does not vendor source code, does not git clone, and does not download extra binaries;
* all knowledge base operations are performed through explicit `clawsqlite knowledge ...` CLI calls, and their `stdout/stderr` can be fully audited in logs.
