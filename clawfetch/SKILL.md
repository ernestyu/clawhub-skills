---
name: clawfetch
description: Web page → Markdown scraper skill that wraps the clawfetch Node CLI to fetch articles, GitHub READMEs, and Reddit threads into normalized markdown with metadata for OpenClaw agents.
version: 0.1.0
metadata: {"openclaw":{"homepage":"https://github.com/ernestyu/clawfetch","tags":["web","scraper","markdown","cli"],"requires":{"bins":["node","npm"],"env":[]},"install":[{"id":"clawfetch_npm","kind":"shell","label":"Install clawfetch npm package locally into this skill directory","script":"set -e && cd {baseDir} && bash bootstrap_deps.sh"}]}}
---

# clawfetch (OpenClaw Skill)

Use the published **clawfetch** npm CLI to convert a single web page into
normalized markdown with a small metadata header.

This skill is a **thin wrapper** around the public `clawfetch` package:

- It does **not** vendor the clawfetch source code.
- It does **not** perform any hidden git clones.
- It only installs the `clawfetch` npm package in this skill directory via
  the explicit install hook.

Typical use cases for agents:

- Fetch a WeChat / blog / docs article into markdown for later indexing.
- Fetch a GitHub repository README (raw) and store it into a knowledge base.
- Fetch a Reddit thread as a structured "post + comments" markdown document.

The CLI emits a header like:

```text
--- METADATA ---
Title: ...
Author: ...
Site: ...
FinalURL: ...
Extraction: readability|fallback-container|body-innerText|github-raw-fast-path|reddit-rss
FallbackSelector: ...   # only when not readability
--- MARKDOWN ---
<markdown>
```

## Installation (skill-level)

This skill assumes:

- `node` / `npm` are available in the OpenClaw container.
- Network access to npm to install the `clawfetch` package and its dependencies.

To install the CLI into the skill directory, the OpenClaw skill installer will
run:

```bash
set -e && cd {baseDir} && bash bootstrap_deps.sh
```

The `bootstrap_deps.sh` script is small and reviewable; it only calls
`npm install clawfetch@0.1.3` in the skill directory. No other packages or
git repositories are fetched by this skill.

## Runtime usage (for agents)

After installation, agents can invoke the CLI from this directory as:

```bash
node node_modules/clawfetch/clawfetch.js <url> [--max-comments N] [--no-reddit-rss]
```

Recommended patterns:

- **General articles / docs**
  - Use the default mode, which launches headless Chromium via Playwright,
    then uses Readability + Turndown to extract the main article body.
- **GitHub repositories**
  - Pass the repository URL (e.g. `https://github.com/owner/repo`).
  - clawfetch will attempt a raw README fast-path from
    `raw.githubusercontent.com` before falling back to browser mode.
- **Reddit threads**
  - Pass the thread URL (e.g. `https://www.reddit.com/r/.../comments/.../`).
  - By default, clawfetch will:
    - Convert the URL to `.rss` and fetch the Atom feed using a normal
      desktop browser User-Agent.
    - Render the first entry as the main post (`## Post: ...`).
    - Render subsequent entries as comments (`### Comment by ...`), limited
      by `--max-comments` (default 50; `0` means no limit).
  - Use `--no-reddit-rss` to force browser scraping instead of RSS.

## Safety / non-suspicious behaviour

- This skill does not:
  - Clone any git repositories at runtime.
  - Download arbitrary source trees into the skill directory.
  - Run hidden package managers beyond `npm install clawfetch@0.1.3` in the
    explicit install step.
- All heavy work (Playwright, Readability, Turndown) comes from the
  published `clawfetch` package and its declared npm dependencies.

Agents should treat this skill as a **read-mostly web → markdown tool** and
avoid using it for arbitrary scripting or filesystem operations beyond its
intended CLI interface.
