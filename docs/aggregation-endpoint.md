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

## 一、创建 Worker

1. 注册 [Cloudflare](https://dash.cloudflare.com/sign-up)（免费）
2. 安装 Node 后装工具：`npm i -g wrangler`
3. 初始化并部署：
```bash
mkdir lengbanlist-stats && cd lengbanlist-stats
wrangler init            # 选 TypeScript/JavaScript 均可，选"无 worker 模板"即可
# 把本仓库 docs/stats-endpoint-worker.js 的内容覆盖到 src/index.js（或 .ts）
```

4. 创建 KV 命名空间（免费的）：
```bash
wrangler kv namespace create STATS_KV
# 输出里的 id 记下来
```

5. `wrangler.toml` 加绑定：
```toml
name = "lengbanlist-stats"
main = "src/index.js"
compatibility_date = "2024-01-01"

[[kv_namespaces]]
binding = "STATS_KV"
id = "这里填上一步输出的 id"
```

6. 部署：
```bash
wrangler deploy
# 输出形如 https://lengbanlist-stats.你的用户名.workers.dev
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

> `rotate_featured.py` 已支持：自动读 `STATS_API_URL`，端点不可用时回退顺序轮换，
> 不影响任何功能。

## 三、自测

```bash
# 模拟上报两条（不同 server 代表两台服务器都装了 hutao）
curl -X POST https://你的域名.workers.dev -H 'content-type: application/json' \
     -d '{"server":"server-a","model":"hutao","version":"2.0.4"}'
curl -X POST https://你的域名.workers.dev -H 'content-type: application/json' \
     -d '{"server":"server-b","model":"hutao","version":"2.0.4"}'

# 查当月排行（应该返回 hutao 2 次）
curl "https://你的域名.workers.dev/?month=$(date +%Y-%m)"
# → {"top":{"model":"hutao","count":2}}
```

## 四、防刷说明

- 每台服务器（按自动生成的 server-id）**每月每模型只计一次**，重复安装不会刷数
- KV key 3 个月自动过期，无需维护
- Worker 代码在 `docs/stats-endpoint-worker.js`，可随意审查/自托管

## 五、若不想用 Cloudflare

端点协议极简（一个 POST + 一个 GET），任何平台都行：
- **Vercel/Netlify** 函数 + Upstash Redis（免费额度）—— 改写 ~20 行
- **自己的 VPS**：Nginx + 一个 30 行的 Python 文件即可
- 甚至先不搭：轮换工作流自动回退"顺序轮换"，精选功能仍可用
