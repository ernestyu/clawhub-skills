# clawsqlite-knowledge environment examples

This Skill itself does not read a `.env` file directly. Instead, it relies
on the underlying `clawsqlite` CLI, which supports project-level `.env`
files (see the `ENV.example` shipped with the `clawsqlite` package).

In OpenClaw/ClawHub deployments you typically configure these env vars on
the **Agent** (or the host environment) so both the Skill and any direct
CLI usage share the same configuration.

Below is a consolidated example of env vars that are relevant for
`clawsqlite-knowledge`. They are a **subset** of the full `ENV.example`
shipped with the `clawsqlite` CLI, focused on what typical OpenClaw
agents need.

```env
# --- Knowledge root (usually configured at the agent level) ---
# CLAWSQLITE_ROOT=/home/node/.openclaw/workspace/knowledge_data
# CLAWSQLITE_DB=/home/node/.openclaw/workspace/knowledge_data/knowledge.sqlite3
# CLAWSQLITE_ARTICLES_DIR=/home/node/.openclaw/workspace/knowledge_data/articles

# --- Embedding service (vector search) ---
# Base URL of the embedding API (OpenAI-compatible)
# EMBEDDING_BASE_URL=https://embed.example.com/v1
# EMBEDDING_MODEL=your-embedding-model-name
# EMBEDDING_API_KEY=sk-your-embedding-key
# Vector dimension for this embedding model (e.g. 1024 for BAAI/bge-m3).
# CLAWSQLITE_VEC_DIM=1024

# --- Small LLM (optional, for query_refine/query_tags & summaries/tags) ---
# SMALL_LLM_BASE_URL=https://llm.example.com/v1
# SMALL_LLM_MODEL=your-small-llm-name
# SMALL_LLM_API_KEY=sk-your-small-llm-key

# --- FTS/jieba fallback (CJK) ---
# CLAWSQLITE_FTS_JIEBA=auto   # auto: only when libsimple is missing AND jieba is installed
#                             # on: force jieba pre-segmentation; off: disable
#                             # if you change this, rebuild:
#                             #   clawsqlite knowledge reindex --rebuild --fts

# --- Search query planning (query_refine/query_tags) ---
# How many query tags to generate for search (LLM or heuristic fallback).
# CLAWSQLITE_SEARCH_QUERY_TAG_MIN=8
# CLAWSQLITE_SEARCH_QUERY_TAG_MAX=12

# --- Hybrid search score weights (4 capability modes) ---
# Capability modes are determined at runtime by:
# - Whether embeddings are enabled (and vec index exists)
# - Whether SMALL_LLM is enabled AND you call search with `--gen-provider llm`
#   and `--llm-keywords != off` (then we use LLM to build query_refine/query_tags)
#
# Mode1: LLM + Embedding
# CLAWSQLITE_SCORE_WEIGHTS_MODE1=vec=0.45,fts=0.25,tag=0.15,priority=0.03,recency=0.02
# Mode2: LLM + no Embedding
# CLAWSQLITE_SCORE_WEIGHTS_MODE2=fts=0.60,tag=0.25,priority=0.08,recency=0.07
# Mode3: no LLM + Embedding
# CLAWSQLITE_SCORE_WEIGHTS_MODE3=vec=0.45,fts=0.25,tag=0.15,priority=0.03,recency=0.02
# Mode4: no LLM + no Embedding
# CLAWSQLITE_SCORE_WEIGHTS_MODE4=fts=0.60,tag=0.25,priority=0.08,recency=0.07
#
# Tag channel knobs:
# - When embeddings are enabled, tag score = frac * tag_vec + (1-frac) * tag_lex
# CLAWSQLITE_TAG_VEC_FRACTION=0.70
# - Log-compress lexical tag scores: ln(1 + a*x) / ln(1 + a); a<=0 disables
# CLAWSQLITE_TAG_FTS_LOG_ALPHA=5.0

# Legacy/global overrides (optional):
# - For embedding modes (mode1/mode3):
#   CLAWSQLITE_SCORE_WEIGHTS=vec=0.45,fts=0.25,tag=0.15,priority=0.03,recency=0.02
# - For no-embedding modes (mode2/mode4):
#   CLAWSQLITE_SCORE_WEIGHTS_TEXT=fts=0.60,tag=0.25,priority=0.08,recency=0.07

# --- Interest clustering (optional, via CLI) ---
# These are only needed if you plan to use `build-interest-clusters` and
# `report-interest` directly against the same DB.
# CLAWSQLITE_INTEREST_CLUSTER_ALGO=kmeans++        # or hierarchical
# CLAWSQLITE_INTEREST_TAG_WEIGHT=0.75              # interest_vec from summary/tag mix
# CLAWSQLITE_INTEREST_USE_PCA=true
# CLAWSQLITE_INTEREST_PCA_EXPLAINED_VARIANCE_THRESHOLD=0.95
# CLAWSQLITE_INTEREST_MIN_SIZE=8
# CLAWSQLITE_INTEREST_MAX_CLUSTERS=50
# CLAWSQLITE_INTEREST_KMEANS_RANDOM_STATE=42
# CLAWSQLITE_INTEREST_KMEANS_N_INIT=10
# CLAWSQLITE_INTEREST_KMEANS_MAX_ITER=300
# CLAWSQLITE_INTEREST_ENABLE_POST_MERGE=true
# CLAWSQLITE_INTEREST_MERGE_DISTANCE=0.06
# CLAWSQLITE_INTEREST_HIERARCHICAL_LINKAGE=average
# CLAWSQLITE_INTEREST_HIERARCHICAL_DISTANCE_THRESHOLD=0.20
# CLAWSQLITE_INTEREST_MERGE_ALPHA=0.40

# --- URL scraper (recommended: clawfetch skill/CLI) ---
# CLAWSQLITE_SCRAPE_CMD="node /home/node/.openclaw/workspace/clawfetch/clawfetch.js --auto-install"
```

> In practice, these variables should be configured on the OpenClaw agent
> (or host environment), not by creating a `.env` file inside the Skill
> directory. This file is purely an example to keep `clawsqlite-knowledge`
> in sync with the `ENV.example` shipped by the `clawsqlite` CLI.
