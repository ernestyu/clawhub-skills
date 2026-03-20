# clawfetch（ClawHub Skill 中文说明）

`clawfetch` 是一个 **网页 → markdown 抓取 CLI 工具**，主要是为
[OpenClaw](https://github.com/openclaw/openclaw) 的 Agent / Skill 场景设计的。

这个 skill 只是对已发布的 `clawfetch` npm 包做了一层 **很薄的封装**，
让 OpenClaw 可以用一个可信、易审计的方式调用它，而不是在每个 skill
里重复造一套爬虫逻辑。

它在补丁版 OpenClaw Docker 镜像 `ernestyu/openclaw-patched` 中体验最佳，
主要用途是作为 **知识库（例如 `clawsqlite` / Clawkb）之前的一层前处理**：

- 给定一个 URL → 输出带元数据头部的标准化 markdown
- 再由本地 SQLite / KB 工具去做索引 / 分片 / 检索
- 避免在 Agent 里面到处散落 ad-hoc 的爬虫脚本

底层 CLI 依赖：

- Playwright（无头 Chromium）
- Mozilla Readability（正文抽取）
- Turndown（HTML → markdown）

输入：单个 `http/https` URL

输出：带 `--- METADATA ---` 头部的标准化 markdown，例如：

```text
--- METADATA ---
Title: ...
Author: ...
Site: ...
FinalURL: ...
Extraction: readability|fallback-container|body-innerText|github-raw-fast-path|reddit-rss
FallbackSelector: ...   # 仅在非 readability 模式下出现
--- MARKDOWN ---
<markdown>
```

它的目标不是做一个“又一个通用爬虫库”，而是做一个 **OpenClaw 优先、知识库友好** 的
“URL → markdown + metadata” 工具：

- 输出格式固定、易于机器解析
- 对 GitHub / Reddit 提供协议层面的快速路径
- 错误信息带 `NEXT:` 提示，方便 Agent 决策下一步

---

## 1. 为什么需要这个 skill？

虽然抓网页的库已经很多，但在 OpenClaw + KB 的场景里有几个特殊诉求：

- Agent 通常运行在 Docker（比如 `ernestyu/openclaw-patched`）里
- 希望有一个统一的 CLI，用来做 “URL → markdown + metadata”
- 希望输出是干净 markdown，适合喂给 SQLite / 向量库
- 希望行为简单可审计，不出现各种隐蔽脚本 / git clone

这个 skill 的设计是：

- 重活都交给已经发布的 `clawfetch` npm 包
- skill 自身只包含最核心的 3 个文件，体积小、结构简单
- 让 Agent 可以直接在 skill 目录下调用 `clawfetch`，作为统一的抓取入口

如果你在搭 OpenClaw + `clawsqlite` / Clawkb 的知识库，这个 skill 是推荐的网页入口方式。

---

## 2. 通过 ClawHub 安装

在 OpenClaw 环境中安装本 skill：

```bash
clawhub install clawfetch
```

安装过程大致会做两件事：

1. 把 skill artifact 下载到你的 workspace（例如
   `~/.openclaw/workspace/skills/clawfetch`）。
2. 运行 skill 级安装脚本：

   ```bash
   set -e && cd {baseDir} && bash bootstrap_deps.sh
   ```

`bootstrap_deps.sh` 设计得非常克制、易审计，只做一件事：

```bash
npm install clawfetch@0.1.3
```

不会在运行时：

- git clone 任意仓库
- 安装额外无关包
- 修改全局 npm 配置

这跟 `clawhealth-garmin` 走的模型是一样的：

- 逻辑代码在主仓库（或 npm / PyPI 包）里维护
- ClawHub skill 只做“薄封装 + 安装 hook”

---

## 3. 运行方式（从 skill 目录调用）

安装完成后，CLI 的入口在 skill 目录里：

```bash
cd ~/.openclaw/workspace/skills/clawfetch
node node_modules/clawfetch/clawfetch.js <url> [--max-comments N] [--no-reddit-rss] [--auto-install]
```

常见用法：

### 3.1 一般文章 / 文档

```bash
node node_modules/clawfetch/clawfetch.js https://example.com/some-article > article.md
```

- 通过 Playwright 启动无头 Chromium；
- 等待页面文本长度稳定；
- 用 Readability 抽取主体内容；
- 如果失败则尝试常见容器，再不行退回 `body.innerText`；
- 最终输出 markdown + METADATA 头部。

### 3.2 GitHub 仓库

```bash
node node_modules/clawfetch/clawfetch.js https://github.com/owner/repo > repo-readme.md
```

对于形如 `https://github.com/owner/repo` 的仓库主页 URL：

- `clawfetch` 会优先尝试从 `raw.githubusercontent.com` 获取 README：
  - 常见文件名如 `README.md` / `README_zh.md`；
  - 成功时：
    - `Extraction: github-raw-fast-path`
    - `FinalURL` 为 raw 地址；
    - markdown 部分就是 README 内容。
- 如果所有 raw 路径都失败，则回退到浏览器模式抓取。

同时，它会提示：

- 如果你想深入看代码，不建议继续用网页抓取；
- 推荐用 git：

  ```bash
  git clone git@github.com:owner/repo.git
  cd repo
  ```

### 3.3 Reddit 帖子

```bash
node node_modules/clawfetch/clawfetch.js \
  "https://www.reddit.com/r/reinforcementlearning/comments/tsv55f/r_reinforcement_learning_in_finance_project/" \
  --max-comments 5 > reddit-thread.md
```

对于 Reddit 帖子：

- 默认使用 Atom/RSS 快速路径：
  - 把 `<url>` 转成 `<url>.rss`；
  - 用正常桌面浏览器 User-Agent 去抓取 Atom feed；
  - 把 feed 解析成结构化的“主帖 + 评论” markdown：

    ```markdown
    ## Post: ...
    by /u/... at ...

    <主帖正文>

    ---

    ### Comment by /u/... at ...

    <评论正文>
    ```

- 评论数量由 `--max-comments` 控制（默认 50；传 0 表示不限制）。
- 如需调试浏览器模式，可以加 `--no-reddit-rss` 禁用 RSS 快速路径。

这类输出非常适合作为“Reddit → KB 文本”的输入。

---

## 4. 依赖与缺失依赖时的行为

skill 自身除了 `bootstrap_deps.sh` 里的 `npm install clawfetch@0.1.3` 外，
不会再主动调用 `npm`。

运行时的行为完全由 `clawfetch` CLI 决定：

- 它会用 `require()` 检查以下依赖是否存在：
  - `playwright-core`（或 `playwright`）
  - `@mozilla/readability`
  - `jsdom`
  - `turndown`
- 如果缺少依赖且 **没有使用 `--auto-install`**：
  - 打印缺失包列表；
  - 打印推荐的 `npm install` 命令（全局或本地）；
  - 退出并返回非零状态码；
- 如果加了 `--auto-install`：
  - 会在 `clawfetch.js` 所在目录尝试一次本地 `npm install`；
  - 失败时仍然只打印 `NEXT:` 提示，让人工/上层决定下一步。

skill 不会在背后静默安装其它东西。

---

## 5. 安全与信任模型

为了避免在 ClawHub 上触发“可疑代码”标签，这个 skill 遵守几个约束：

- skill 里 **不** 内置 `clawfetch` 源码；
- **不** 在运行时 git clone 任意仓库；
- **不** 执行任何 `curl | bash` 类型脚本；
- 唯一一次 `npm install` 发生在显式的安装阶段，脚本短小可审计；
- 真正的逻辑全部来自公开的 npm 包 `clawfetch`（Apache-2.0 许可）。

你可以非常容易地 review 本 skill：

- 只看 `clawfetch` 目录下的 3 个文件：`SKILL.md`、`manifest.yaml`、`bootstrap_deps.sh`；
- 如果需要深入了解实现，再去看主仓库 `ernestyu/clawfetch`。

---

## 6. 许可证

本 skill 以 MIT 许可证发布；底层 `clawfetch` npm 包以 Apache-2.0 许可证发布。

具体条款请参考各自仓库中的 LICENSE 文件。
