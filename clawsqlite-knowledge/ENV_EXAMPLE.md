# clawsqlite-knowledge 环境变量示例

本 Skill 本身不直接读取 `.env` 文件，但在 OpenClaw / ClawHub 环境中，
通常会通过 Agent 的环境变量来配置 clawsqlite 行为。下面是和
`clawsqlite-knowledge` 强相关的几类配置示例。

```env
# --- 知识库根目录（可选，通常由上层统一配置） ---
# CLAWSQLITE_ROOT=/home/node/.openclaw/workspace/knowledge_data
# CLAWSQLITE_DB=/home/node/.openclaw/workspace/knowledge_data/knowledge.sqlite3
# CLAWSQLITE_ARTICLES_DIR=/home/node/.openclaw/workspace/knowledge_data/articles

# --- Embedding 服务（向量检索） ---
# EMBEDDING_BASE_URL=https://embed.example.com/v1
# EMBEDDING_MODEL=your-embedding-model
# EMBEDDING_API_KEY=sk-your-embedding-key
# CLAWSQLITE_VEC_DIM=1024

# --- 中文 FTS 退级：libsimple 缺失时的 jieba 模式 ---
# CLAWSQLITE_FTS_JIEBA=auto   # auto|on|off，详见 clawsqlite README

# --- URL 抓取脚本（推荐使用 clawfetch） ---
# CLAWSQLITE_SCRAPE_CMD="node /home/node/.openclaw/workspace/clawfetch/clawfetch.js --auto-install"
```

> 实际部署时，推荐把这些变量配置在 OpenClaw agent 的环境配置里，
> 而不是直接在 Skill 目录下创建 `.env` 文件。`ENV_EXAMPLE.md` 仅作
> 文档示例使用。
