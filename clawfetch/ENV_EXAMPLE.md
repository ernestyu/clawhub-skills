# clawfetch environment examples

This skill wraps the `clawfetch` npm CLI. The CLI itself reads configuration
from the **process environment**, not from a `.env` file in this directory.

In OpenClaw/ClawHub deployments you typically configure these env vars on
the **Agent** (or host) so all skills and CLIs share the same settings.

Below are example env vars relevant to `clawfetch`.

```env
# --- FlareSolverr / JS backend for Cloudflare / bot challenges (optional) ---
# If set, clawfetch can call this backend when it detects a Cloudflare or
# similar bot-block page. The endpoint must implement a FlareSolverr-
# compatible `/v1` API (cmd=request.get).
#
# FLARESOLVERR_URL=http://127.0.0.1:8191

# --- Playwright / Chromium configuration (optional) ---
# In most OpenClaw environments you don't need to touch these, but they can
# be useful when debugging or running in custom containers.
#
# PLAYWRIGHT_BROWSERS_PATH=/path/to/custom/playwright-browsers
# NODE_OPTIONS=--max-old-space-size=4096

# --- clawfetch-specific flags (via env, optional) ---
# The CLI primarily uses command-line flags, but you can set defaults via
# env in your agent runtime if desired.
#
# CLAWFETCH_MAX_COMMENTS=50
# CLAWFETCH_DISABLE_REDDIT_RSS=0
```

> Note: this file is only an example. `clawfetch` does **not** parse
> `ENV_EXAMPLE.md` or `.env` files under this directory directly. Configure
> these variables in your OpenClaw agent or host environment.
