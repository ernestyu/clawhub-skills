# clawsqlite-knowledge environment examples

This Skill itself does not read a `.env` file directly, but in
OpenClaw/ClawHub deployments you will typically configure the underlying
`clawsqlite` via environment variables on the Agent.

Below are examples of env vars that are relevant for
`clawsqlite-knowledge`.

```env
# --- Knowledge root (usually configured at the agent level) ---
# CLAWSQLITE_ROOT=/home/node/.openclaw/workspace/knowledge_data
# CLAWSQLITE_DB=/home/node/.openclaw/workspace/knowledge_data/knowledge.sqlite3
# CLAWSQLITE_ARTICLES_DIR=/home/node/.openclaw/workspace/knowledge_data/articles

# --- Embedding service (vector search) ---
# EMBEDDING_BASE_URL=https://embed.example.com/v1
# EMBEDDING_MODEL=your-embedding-model
# EMBEDDING_API_KEY=sk-your-embedding-key
# CLAWSQLITE_VEC_DIM=1024

# --- FTS/jieba fallback (CJK) ---
# CLAWSQLITE_FTS_JIEBA=auto   # auto: only when libsimple is missing AND jieba is installed
#                             # on: force jieba pre-segmentation; off: disable
#                             # if you change this, rebuild: clawsqlite knowledge reindex --rebuild --fts

# --- URL scraper (recommended: clawfetch) ---
# CLAWSQLITE_SCRAPE_CMD="node /home/node/.openclaw/workspace/clawfetch/clawfetch.js --auto-install"
```

> In practice, these variables should be configured on the OpenClaw agent,
> not by creating a `.env` file inside the Skill directory. This file is
> purely an example.
