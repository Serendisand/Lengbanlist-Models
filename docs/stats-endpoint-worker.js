/**
 * Lengbanlist 模型统计聚合端点 (Cloudflare Worker)
 * ----------------------------------------------
 * 协议（与 Lengbanlist 插件 / rotate_featured.py 对齐）:
 *   POST /  body: {"server":"<uuid>","model":"hutao","version":"2.0.4"}
 *         → 记录一次"采纳"（每服每月每模型只计一次,防刷）
 *   GET  /?month=2026-08
 *         → 返回该月被采纳最多的模型: {"top":{"model":"hutao"}}
 *   GET  /?month=2026-08&verbose=1 → 附带完整排行 {"models":{"hutao":3,...}}
 *
 * 部署后配置:
 *   插件 config.yml  → models-cloud.stats.url: https://你的worker域名
 *   模型仓库 Action  → Secrets: STATS_API_URL 同上
 */

// KV 命名空间绑定名（wrangler.toml 中配置为 STATS_KV）
const KV = STATS_KV;

export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      const month = url.searchParams.get('month');
      if (request.method === 'POST') {
        return await handlePost(request, env);
      }
      if (request.method === 'GET' && month) {
        return await handleGet(env, month, url.searchParams.has('verbose'));
      }
      return new Response(JSON.stringify({ error: 'unsupported' }), {
        status: 400, headers: { 'content-type': 'application/json' },
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: String(e) }), {
        status: 500, headers: { 'content-type': 'application/json' },
      });
    }
  },
};

async function handlePost(request, env) {
  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad json' }, 400); }
  const { server, model } = body || {};
  if (!server || !model || !/^[a-z0-9-]{1,32}$/.test(model) || model.length > 64) {
    return json({ error: 'invalid payload' }, 400);
  }
  // 当前月(UTC)
  const now = new Date();
  const month = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}`;
  // 每服每月每模型去重(只计首次),防刷
  const dedupKey = `s:${month}:${model}:${server.slice(0, 64)}`;
  const exists = await env.KV.get(dedupKey);
  if (!exists) {
    await env.KV.put(dedupKey, '1', { expirationTtl: 90 * 24 * 3600 }); // 3 个月后自然过期
    const countKey = `c:${month}:${model}`;
    const cur = Number(await env.KV.get(countKey)) || 0;
    await env.KV.put(countKey, String(cur + 1));
  }
  return json({ ok: true });
}

async function handleGet(env, month, verbose) {
  // 遍历 c:<month>:<model> 前缀聚合排行
  const prefix = `c:${month}:`;
  const counts = {};
  let cursor;
  do {
    const list = await env.KV.list({ prefix, cursor });
    for (const key of list.keys) {
      const model = key.name.slice(prefix.length);
      counts[model] = Number(await env.KV.get(key.name)) || 0;
    }
    cursor = list.cursor;
  } while (cursor);
  if (!Object.keys(counts).length) {
    return json({ top: null });
  }
  // 取 count 最大者(并列时按名字排序保证稳定)
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0];
  const resp = { top: { model: top[0], count: top[1] } };
  if (verbose) resp.models = counts;
  return json(resp);
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status, headers: { 'content-type': 'application/json' },
  });
}
