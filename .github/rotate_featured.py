#!/usr/bin/env python3
"""Lengbanlist-Models 月度精选轮换脚本。

轮换策略（两级）:
1. 若配置了聚合统计端点 STATS_API_URL（环境变量,可选）,读取上月各模型安装排行,
   选安装数最多的模型作为本月精选 —— 插件侧 stats 开关开启并配置 url 后自动参与。
2. 未配置端点或端点不可用时: 顺序轮换当前 featured 的下一个已上架模型。

端点协议: GET {STATS_API_URL}?month=YYYY-MM → 期望 JSON:
  {"model": "hutao"}  或  {"top": {"model": "hutao"}}
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.json"
STATS_API_URL = __import__("os").environ.get("STATS_API_URL", "").strip()
# Cloudflare 把 urllib 默认的 "Python-urllib/3.x" 当自动化流量, 打到 *.workers.dev 直接 403
UA = "Lengbanlist-Bot/1.0 (+https://github.com/Serendisand/Lengbanlist-Models)"


def fetch_top_by_api(month: str):
    """从聚合端点获取上个月下载/安装最多的模型 id;失败返回 None。"""
    if not STATS_API_URL:
        return None
    url = STATS_API_URL + ("" if STATS_API_URL.endswith("?") or "?" in STATS_API_URL else "?") + "month=" + month
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if isinstance(data, dict):
            if isinstance(data.get("top"), dict) and data["top"].get("model"):
                return data["top"]["model"]
            if data.get("model"):
                return data["model"]
        print("stats api returned unexpected shape:", data)
    except Exception as e:
        print("stats api unavailable (%s), fallback to round-robin" % e)
    return None


def main() -> int:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    models = data.get("models", [])
    pool = [m for m in models if m.get("version") not in (None, "", "0.0.0")]
    if not pool:
        print("no available models to rotate")
        return 1

    now = datetime.now(timezone.utc)
    this_month = now.strftime("%Y-%m")
    # 上个月(评选用)与本月(展示用) —— 端点通常统计上月;若端点返回本月数据则直接用
    prev_month = now.replace(day=1)
    if prev_month.month == 1:
        prev_month = prev_month.replace(year=prev_month.year - 1, month=12)
    else:
        prev_month = prev_month.replace(month=prev_month.month - 1)
    prev_month_str = prev_month.strftime("%Y-%m")

    next_id = None
    api_picked = fetch_top_by_api(prev_month_str)
    if api_picked:
        if any(m["id"] == api_picked for m in pool):
            next_id = api_picked
            print("featured by stats api: %s (month %s)" % (next_id, prev_month_str))
        else:
            print("stats api returned unknown model %s, fallback" % api_picked)

    if not next_id:
        current_id = (data.get("featured") or {}).get("modelId")
        order = [m["id"] for m in pool]
        if current_id in order:
            next_id = order[(order.index(current_id) + 1) % len(order)]
        else:
            next_id = order[0]
        print("featured by round-robin: %s" % next_id)

    next_model = next(m for m in pool if m["id"] == next_id)
    data["featured"] = {
        "month": this_month,
        "modelId": next_model["id"],
        "title": "本月精选 — " + next_model["name"],
        "description": next_model.get("description", ""),
    }
    INDEX.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
