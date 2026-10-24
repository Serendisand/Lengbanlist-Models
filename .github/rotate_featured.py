#!/usr/bin/env python3
"""Lengbanlist-Models 月度精选轮换脚本。

数据来源（bStats REST API，只读、免鉴权）:
  GET https://bstats.org/api/v1/plugins/{pluginId}/charts/{chartId}/data

插件通过 bStats 自定义饼图 `modelUsage` 上报"当前使用的模型"，
接口返回每个模型的服务器数: [{"name": "hutao", "y": 3}, ...]

轮换策略（两级）:
1. 在已上架模型里选 bStats 里"最多服务器在用"的那个；
2. 图表没数据 / 接口不可用 / 没有匹配模型时，顺序轮换兜底。

注意：bStats 饼图只保留"当前快照"，没有按月历史。每月 1 号执行时，
读到的是上月末的分布，正好用于评选上月最受欢迎的模型。
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.json"

# 默认指向 Lengbanlist 的 bStats 插件页；可用仓库 Variables 覆盖
PLUGIN_ID = (os.environ.get("BSTATS_PLUGIN_ID") or "33262").strip()
CHART_ID = (os.environ.get("BSTATS_CHART_ID") or "modelUsage").strip()
# bStats 也在 Cloudflare 后面，默认 urllib UA 容易被当自动化流量拦掉
UA = "Lengbanlist-Bot/1.0 (+https://github.com/Serendisand/Lengbanlist-Models)"


def fetch_model_usage() -> dict:
    """从 bStats 拉取模型分布 {model_id: 服务器数}；失败或无数据返回 {}。"""
    if not re.fullmatch(r"\d+", PLUGIN_ID) or not re.fullmatch(r"[A-Za-z0-9_]+", CHART_ID):
        print("invalid bstats plugin/chart id (%r/%r), fallback" % (PLUGIN_ID, CHART_ID))
        return {}

    url = "https://bstats.org/api/v1/plugins/%s/charts/%s/data" % (PLUGIN_ID, CHART_ID)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print("bstats api unavailable (%s), fallback to round-robin" % e)
        return {}

    usage = {}
    if isinstance(data, list):
        # 饼图: [{"name": "hutao", "y": 3}]
        for item in data:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            count = item.get("y", item.get("value"))
            if isinstance(name, str) and isinstance(count, (int, float)):
                usage[name.strip().lower()] = int(count)
    elif isinstance(data, dict):
        # 兼容 {"values": {"hutao": 3}} 这类包装
        values = data.get("values") if isinstance(data.get("values"), dict) else data
        for name, count in values.items():
            if isinstance(name, str) and isinstance(count, (int, float)):
                usage[name.strip().lower()] = int(count)

    if not usage:
        print("bstats chart %s has no usable data yet" % CHART_ID)
    return usage


def main() -> int:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    models = data.get("models", [])
    pool = [m for m in models if m.get("version") not in (None, "", "0.0.0")]
    if not pool:
        print("no available models to rotate")
        return 1

    now = datetime.now(timezone.utc)
    this_month = now.strftime("%Y-%m")

    # 只认已上架模型（插件内置的 default/english 等会被自然过滤掉）
    pool_ids = {m["id"] for m in pool}
    usage = fetch_model_usage()
    ranked = sorted(
        ((mid, count) for mid, count in usage.items() if mid in pool_ids and count > 0),
        key=lambda kv: (-kv[1], kv[0]),
    )

    if ranked:
        next_id, votes = ranked[0]
        print("featured by bstats: %s (%d servers, chart %s)" % (next_id, votes, CHART_ID))
    else:
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
