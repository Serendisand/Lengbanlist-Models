// 本地冒烟测试：用内存版 KV 跑一遍 Worker 逻辑，无需登录 Cloudflare
// 用法: node worker/smoke-test.mjs
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const mod = await import(pathToFileURL(process.argv[2] || resolve(here, 'src/index.js')).href);
const worker = mod.default;

function fakeKV() {
  const store = new Map();
  return {
    async get(k) { return store.has(k) ? store.get(k) : null; },
    async put(k, v) { store.set(k, v); },
    async list({ prefix = '', cursor } = {}) {
      const names = [...store.keys()].filter((k) => k.startsWith(prefix)).sort();
      const start = cursor ? Number(cursor) : 0;
      const page = names.slice(start, start + 2); // 故意分页，验证 cursor 循环
      const done = start + 2 >= names.length;
      return { keys: page.map((name) => ({ name })), list_complete: done, cursor: done ? undefined : String(start + 2) };
    },
  };
}

const env = { STATS_KV: fakeKV() };
const month = new Date().toISOString().slice(0, 7);
let pass = 0, fail = 0;
const post = (body, e = env) =>
  worker.fetch(new Request('https://x.workers.dev/', {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
  }), e);
const get = (qs, e = env) => worker.fetch(new Request(`https://x.workers.dev/?${qs}`, { method: 'GET' }), e);

async function check(label, res, expectStatus, expectBody) {
  const text = await res.text();
  const okStatus = res.status === expectStatus;
  const okBody = expectBody === undefined || text.includes(expectBody);
  if (okStatus && okBody) { pass++; console.log(`  ok   ${label} -> ${res.status} ${text}`); }
  else { fail++; console.log(`  FAIL ${label} -> ${res.status} ${text} (期望 ${expectStatus} / ${expectBody})`); }
}

console.log(`月份=${month}`);
await check('上报 hutao@server-a', await post({ server: 'server-a', model: 'hutao', version: '2.0.4' }), 200, '"ok":true');
await check('重复上报去重', await post({ server: 'server-a', model: 'hutao' }), 200, '"ok":true');
await check('上报 hutao@server-b', await post({ server: 'server-b', model: 'hutao' }), 200, '"ok":true');
await check('上报 furina@server-a', await post({ server: 'server-a', model: 'furina' }), 200, '"ok":true');
await check('非法模型名(大写)', await post({ server: 's', model: 'HuTao' }), 400, 'invalid payload');
await check('缺字段', await post({ model: 'hutao' }), 400, 'invalid payload');
await check('非法 JSON', await worker.fetch(new Request('https://x.workers.dev/', { method: 'POST', body: '{oops' }), env), 400, 'bad json');
await check('排行 top', await get(`month=${month}`), 200, '"model":"hutao","count":2');
await check('verbose 排行', await get(`month=${month}&verbose=1`), 200, '"furina":1');
await check('非法 month', await get('month=2026-99'), 400, 'bad month');
await check('存活探针', await get(''), 200, '"service":"lengbanlist-stats"');
await check('空月份无数据', await get('month=2020-01'), 200, '"top":null');
await check('KV 绑定缺失', await post({ server: 's', model: 'hutao' }, {}), 500, 'KV binding STATS_KV missing');

console.log(`\n通过 ${pass} / 失败 ${fail}`);
process.exit(fail ? 1 : 0);
