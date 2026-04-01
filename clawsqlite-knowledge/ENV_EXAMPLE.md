# clawsqlite-knowledge environment examples

This Skill itself does not read a `.env` file directly. Instead, it relies
on the underlying `clawsqlite` CLI, which supports project-level `.env`
files (see the `ENV.example` shipped with the `clawsqlite` package).

In OpenClaw/ClawHub deployments you typically configure these env vars on
the **Agent** (or the host environment) so both the Skill and any direct
CLI usage share the same configuration.

Below is a consolidated example of env vars that are relevant for
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

# --- Small LLM (optional, for title/summary/tags & query keyword expansion) ---
# SMALL_LLM_BASE_URL=https://llm.example.com/v1
# SMALL_LLM_MODEL=your-small-llm
# SMALL_LLM_API_KEY=sk-your-small-llm-key

# --- FTS/jieba fallback (CJK) ---
# CLAWSQLITE_FTS_JIEBA=auto   # auto: only when libsimple is missing AND jieba is installed
#                             # on: force jieba pre-segmentation; off: disable
#                             # if you change this, rebuild:
#                             #   clawsqlite knowledge reindex --rebuild --fts

# --- Tag generation & semantic rerank (clawsqlite>=0.1.8) ---
# Controls how tags are generated from article content.
#   auto (default): use TextRank/TF-IDF + optional semantic centrality when
#                   embeddings + jieba are available; otherwise fall back to
#                   pure TextRank/TF-IDF (with jieba) or a lightweight
#                   keyword extractor.
#   on:  force semantic centrality when embeddings + jieba are available.
#   off: disable semantic rerank; always use non-semantic behavior.
# CLAWSQLITE_TAGS_SEMANTIC=auto

# --- Hybrid search score weights (clawsqlite>=0.1.8) ---
# Default weights inside clawsqlite are:
#   0.55 for vector similarity
#   0.25 for FTS (BM25) score
#   0.15 for tag match score
#   0.03 for priority bonus
#   0.02 for recency bonus
# You can override them by setting all five keys in one string, e.g.:
# CLAWSQLITE_SCORE_WEIGHTS=vec=0.55,fts=0.25,tag=0.15,priority=0.03,recency=0.02

# --- URL scraper (recommended: clawfetch) ---
# CLAWSQLITE_SCRAPE_CMD="node /home/node/.openclaw/workspace/clawfetch/clawfetch.js --auto-install"
```

> In practice, these variables should be configured on the OpenClaw agent
> (or host environment), not by creating a `.env` file inside the Skill
> directory. This file is purely an example to keep `clawsqlite-knowledge`
> in sync with the `ENV.example` shipped by the `clawsqlite` CLI.
