# clawfeedradar environment examples

This file lists environment variables that are relevant when using the
`clawfeedradar` skill. The skill itself does not read a `.env` file
inside its own directory; instead it relies on the upstream
`clawfeedradar` and `clawsqlite` CLIs, which both support project‑level
`.env`.

In OpenClaw/ClawHub deployments you typically configure these env vars
on the **agent** (or host) so that:

- clawsqlite
- clawsqlite-knowledge
- clawfeedradar (CLI and skill)

all share the same configuration.

Below is a consolidated example, adapted from the upstream
`clawfeedradar` and `clawsqlite` `ENV.example` files.

```env
# --- Knowledge base (clawsqlite) ---
# Root directory for the knowledge base
# CLAWSQLITE_ROOT=/home/node/.openclaw/workspace/knowledge_data
# Explicit DB path (optional, overrides default under ROOT)
# CLAWSQLITE_DB=/home/node/.openclaw/workspace/knowledge_data/clawkb.sqlite3

# --- Embedding service (shared between clawsqlite & clawfeedradar) ---
# EMBEDDING_BASE_URL=https://embed.example.com/v1
# EMBEDDING_MODEL=your-embedding-model-name
# EMBEDDING_API_KEY=sk-your-embedding-key
# Vector dimension (must match the embedding model)
# CLAWSQLITE_VEC_DIM=1024

# --- Small LLM (optional: summaries / tags / bilingual body) ---
# SMALL_LLM_BASE_URL=https://llm.example.com/v1
# SMALL_LLM_MODEL=your-small-llm
# SMALL_LLM_API_KEY=sk-your-small-llm-key

# --- Interest clusters (configured on clawsqlite side) ---
# Cluster algo: kmeans++ | hierarchical
# CLAWSQLITE_INTEREST_CLUSTER_ALGO=kmeans++
# Mix summary/tag embeddings into an interest vector
# CLAWSQLITE_INTEREST_TAG_WEIGHT=0.75
# Optional PCA for clustering stage only
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

# --- Fulltext scraping ---
# Command used to fetch fulltext for candidate URLs
# CLAWFEEDRADAR_SCRAPE_CMD="/home/node/.openclaw/workspace/clawfetch_wrapper.sh"
# Cross-host parallelism; per-host remains serial
# CLAWFEEDRADAR_SCRAPE_WORKERS=4

# --- Output ---
# Directory where RSS XML + JSON sidecars are written
# CLAWFEEDRADAR_OUTPUT_DIR=/home/node/.openclaw/workspace/clawfeedradar/feeds

# --- Scoring ---
# Sigmoid steepness around 0.5 for interest_raw
# CLAWFEEDRADAR_INTEREST_SIGMOID_K=4.0
# Recency/popularity weights
# CLAWFEEDRADAR_W_RECENCY=0.05
# CLAWFEEDRADAR_W_POPULARITY=0.05
# Half-life for recency in days
# CLAWFEEDRADAR_RECENCY_HALF_LIFE_DAYS=3

# --- LLM (summaries + bilingual body) ---
# Approximate context budget in tokens; internally converted to chars
# CLAWFEEDRADAR_LLM_CONTEXT_TOKENS=8096
# Max chars per bilingual paragraph when splitting long bodies
# CLAWFEEDRADAR_LLM_MAX_PARAGRAPH_CHARS=2400
# Max tags per item when using LLM for tag generation
# CLAWFEEDRADAR_LLM_TAG_MAX_PER_ITEM=12
# Sleep between LLM calls (ms) to avoid rate limits
# CLAWFEEDRADAR_LLM_SLEEP_BETWEEN_MS=500
# Source/target languages (bilingual body)
# CLAWFEEDRADAR_LLM_SOURCE_LANG=auto
# CLAWFEEDRADAR_LLM_TARGET_LANG=zh

# --- Git publish (optional: GitHub/Gitee Pages) ---
# CLAWFEEDRADAR_PUBLISH_GIT_REPO=git@github.com:yourname/clawfeedradar-feed.git
# CLAWFEEDRADAR_PUBLISH_GIT_BRANCH=gh-pages
# CLAWFEEDRADAR_PUBLISH_GIT_PATH=feeds
```

> In practice: configure these on the OpenClaw agent/host rather than
> creating a `.env` inside the skill directory. This file exists to keep
> the skill documentation in sync with the upstream projects.
