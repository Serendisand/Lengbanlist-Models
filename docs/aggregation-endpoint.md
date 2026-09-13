# 📊 统计聚合端点搭建指南（免费 · Cloudflare Workers + KV）

用于**自动评选每月精选**：各服务器把模型安装统计上报到这里，模型仓库的轮换工作流
每月从这里拉取"上月被最多服务器采纳的模型"作为本月精选。

> 无需自己的服务器，全程免费（Cloudflare 免费额度：10 万请求/天，KV 读写充足）。

## 架构

```
各服插件 (config.yml 开启 stats)          GitHub 仓库
        │ POST {server,model}                  │ GitHub Action (每月1号)
        ▼                                      ▼ GET ?month=2026-08
   Cloudflare Worker ── 写/读 ──> KV 计数   rotate_featured.py
        │                                      │
        └────────── 返回当月排行 top ◄─────────┘
```

Worker 代码就在本仓库 `worker/`，部署时不需要另外复制粘贴：

```
worker/
├── wrangler.toml.example  ← 配置模板（Worker 名 / 入口 / KV 绑定），复制成 wrangler.toml 再填 id
├── src/index.js           ← Worker 源码（唯一一份，改这里）
└── smoke-test.mjs         ← 本地冒烟测试，无需登录 Cloudflare
```

> `wrangler.toml` 本身已 `.gitignore`（里面的 KV 命名空间 id 属于账号资源标识，不入公开仓库）。

## 一、部署

### 方式 A：命令行（wrangler，推荐）

```bash
npm i -g wrangler        # 或全程用 npx wrangler
wrangler login           # 浏览器里授权你的 Cloudflare 账号

cd worker
cp wrangler.toml.example wrangler.toml      # 本地配置，不入库
wrangler kv namespace create STATS_KV
# 输出形如：id = "a1b2c3..."  → 填进 wrangler.toml 的 id 字段

wrangler deploy
# 输出形如 https://lengbanlist-stats.你的用户名.workers.dev
```

### 方式 B：纯网页（不用命令行）

1. [dash.cloudflare.com](https://dash.cloudflare.com) → Workers & Pages → 创建 Worker，名字填 `lengbanlist-stats`
2. 编辑代码，把 `worker/src/index.js` 全文粘进去
3. 在"存储与数据库 (KV)"里创建一个命名空间（名字随意，例如 `STATS_KV`）
4. 回到 Worker → 设置 → 绑定 → 添加 KV 命名空间绑定：**变量名必须填 `STATS_KV`**，选中刚建的命名空间
5. 部署，拿到 `https://lengbanlist-stats.xxx.workers.dev`

> 变量名写错成别的（如 `KV`）不会报错，但每次上报都会返回 500 —— 请保持 `STATS_KV`。

### 部署前自测（可选，不联网）

```bash
node worker/smoke-test.mjs     # 内存版 KV 跑全流程，13 项断言
```

## 二、两端配置

### 1. 插件端（各服务器 config.yml）
```yaml
models-cloud:
  stats:
    enabled: true                       # 玩家可关(默认开,参与评选)
    url: "https://lengbanlist-stats.你的用户名.workers.dev"   # 填你的 Worker 地址
```
生效：重启或 `/lban reload`。之后每次 `/lban models install/pin` 自动上报。

### 2. 模型仓库端（GitHub）
Settings → Secrets and variables → Actions → New repository secret：
```
Name: STATS_API_URL
Value: https://lengbanlist-stats.你的用户名.workers.dev
```

> `.github/rotate_featured.py` 已支持：自动读 `STATS_API_URL`，端点不可用时回退顺序轮换，
> 不影响任何功能。

## 三、自测

```bash
# 探针：确认 Worker 活着
curl https://你的域名.workers.dev
# → {"ok":true,"service":"lengbanlist-stats"}

# 模拟上报两条（不同 server 代表两台服务器都装了 hutao）
curl -X POST https://你的域名.workers.dev -H 'content-type: application/json' \
     -d '{"server":"server-a","model":"hutao","version":"2.0.4"}'
curl -X POST https://你的域名.workers.dev -H 'content-type: application/json' \
     -d '{"server":"server-b","model":"hutao","version":"2.0.4"}'

# 查当月排行（应该返回 hutao 2 次；重复上报同一 server 不会涨）
curl "https://你的域名.workers.dev/?month=$(date +%Y-%m)"
# → {"top":{"model":"hutao","count":2}}
curl "https://你的域名.workers.dev/?month=$(date +%Y-%m)&verbose=1"
# → {"top":{...},"models":{"hutao":2}}
```

报文约定（与插件、`rotate_featured.py` 对齐）：

| 请求 | 返回 |
| --- | --- |
| `POST /` body `{"server":"<uuid>","model":"hutao","version":"2.0.4"}` | `{"ok":true}`；`model` 只接受 `^[a-z0-9-]{1,32}$` |
| `GET /?month=2026-08` | `{"top":{"model":"hutao","count":2}}`，无数据显示 `{"top":null}` |
| `GET /?month=2026-08&verbose=1` | 额外带 `models` 完整排行 |
| 其余 | `400 {"error":"..."}` |

## 四、防刷说明

- 每台服务器（按自动生成的 server-id）**每月每模型只计一次**，重复安装不会刷数
- 月份按 **UTC** 计，与 `rotate_featured.py` 的 `utcnow()` 对齐
- KV key 3 个月自动过期，无需维护
- 计数是"读改写"非原子：同一瞬间两台不同服务器上报同一模型，极小概率少计 1，月度评选场景可接受
- Worker 代码在 `worker/src/index.js`，可随意审查/自托管

## 五、若不想用 Cloudflare

端点协议极简（一个 POST + 一个 GET），任何平台都行：
- **Vercel/Netlify** 函数 + Upstash Redis（免费额度）—— 改写 ~20 行
- **自己的 VPS**：Nginx + 一个 30 行的 Python 文件即可
- 甚至先不搭：轮换工作流自动回退"顺序轮换"，精选功能仍可用
