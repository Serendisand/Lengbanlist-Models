#!/usr/bin/env python3
"""Lengbanlist-Models 月度精选轮换脚本。

规则:
- 从 index.json 的 models 中挑选已上架(version != 0.0.0)的模型
- 轮换策略: 顺序取当前 featured 的下一个;若当前 featured 不在池中,取池中第一个
- 更新 featured.month 为运行当月 (脚本在每月 1 号由 GitHub Action 触发)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.json"


def main() -> int:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    models = data.get("models", [])
    pool = [m for m in models if m.get("version") not in (None, "", "0.0.0")]
    if not pool:
        print("no available models to rotate")
        return 1

    current_id = (data.get("featured") or {}).get("modelId")
    # 找到当前 featured 在池中的位置,取下一个;否则取第一个
    order = [m["id"] for m in pool]
    if current_id in order:
        next_id = order[(order.index(current_id) + 1) % len(order)]
    else:
        next_id = order[0]
    next_model = next(m for m in pool if m["id"] == next_id)

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    data["featured"] = {
        "month": month,
        "modelId": next_model["id"],
        "title": "本月精选 — " + next_model["name"],
        "description": next_model.get("description", ""),
    }
    INDEX.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("rotated to %s (%s)" % (next_id, month))
    return 0


if __name__ == "__main__":
    sys.exit(main())
