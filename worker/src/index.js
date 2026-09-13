/**
 * Lengbanlist 模型统计聚合端点 (Cloudflare Worker)
 * ----------------------------------------------
 * 协议（与 Lengbanlist 插件 / .github/rotate_featured.py 对齐）:
 *   POST /  body: {"server":"<uuid>","model":"hutao","version":"2.0.4"}
 *         → 记录一次"采纳"（每服每月每模型只计一次,防刷）
 *   GET  /?month=2026-08
 *         → 返回该月被采纳最多的模型: {"top":{"model":"hutao","count":3}}
 *   GET  /?month=2026-08&verbose=1 → 附带完整排行 {"models":{"hutao":3,...}}
 *   GET  /                → 存活探针（部署后自测用）
 *
 * 部署后配置:
 *   插件 config.yml  → models-cloud.stats.url: https://你的worker域名
 *   模型仓库 Action  → Secrets: STATS_API_URL 同上
 */

// KV 绑定名必须是 STATS_KV（见 wrangler.toml），两者写死对齐，不靠默认值
function kvOf(env) {
  const ns = env && env.STATS_KV;
  if (!ns) throw new Error('KV binding STATS_KV missing');
  return ns;
}

export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      if (request.method === 'POST') {
        return await handlePost(request, env);
      }
      if (request.method === 'GET') {
        const month = url.searchParams.get('month');
        if (month) return await handleGet(env, month, url.searchParams.has('verbose'));
        return json({ ok: true, service: 'lengbanlist-stats' });
      }
      return json({ error: 'unsupported' }, 400);
    } catch (e) {
      // 兜底：绑定缺失 / KV 抖动都不该把异常直接抛成 worker 崩溃
      return json({ error: String((e && e.message) || e) }, 500);
    }
  },
};

async function handlePost(request, env) {
  const ns = kvOf(env);
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'bad json' }, 400);
  }
  const server = typeof (body && body.server) === 'string' ? body.server.trim() : '';
  const model = typeof (body && body.model) === 'string' ? body.model.trim() : '';
  // model 只允许小写字母/数字/连字符（仓库命名契约），长度由正则一并卡死
  if (!server || !/^[a-z0-9-]{1,32}$/.test(model)) {
    return json({ error: 'invalid payload' }, 400);
  }

  // 当前月按 UTC 计（与 rotate_featured.py 的 utcnow 对齐，避免时区错位统计到上个月）
  const now = new Date();
  const month = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}`;

  // 每服每月每模型去重（只计首次），防刷
  const dedupKey = `s:${month}:${model}:${server.slice(0, 64)}`;
  if (!(await ns.get(dedupKey))) {
    await ns.put(dedupKey, '1', { expirationTtl: 90 * 24 * 3600 }); // 3 个月后自然过期
    const countKey = `c:${month}:${model}`;
    // 读改写非原子：KV 最终一致，并发上报极小概率少计 1。月度评选场景可接受，不值得上 Durable Object
    const cur = Number(await ns.get(countKey)) || 0;
    await ns.put(countKey, String(cur + 1));
  }
  return json({ ok: true });
}

async function handleGet(env, month, verbose) {
  const ns = kvOf(env);
  // 限制月份格式，避免拿奇怪前缀去扫 KV
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) {
    return json({ error: 'bad month' }, 400);
  }
  const prefix = `c:${month}:`;
  const counts = {};
  let cursor;
  do {
    const list = await ns.list({ prefix, cursor });
    for (const key of list.keys) {
      counts[key.name.slice(prefix.length)] = Number(await ns.get(key.name)) || 0;
    }
    cursor = list.list_complete ? null : list.cursor;
  } while (cursor);

  const entries = Object.entries(counts);
  if (!entries.length) {
    return json({ top: null });
  }
  // 取 count 最大者（并列时按名字排序保证稳定）
  entries.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const resp = { top: { model: entries[0][0], count: entries[0][1] } };
  if (verbose) resp.models = counts;
  return json(resp);
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    // 统计端点无 CDN 缓存价值，避免中间层缓存住旧排行
    headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
  });
}
