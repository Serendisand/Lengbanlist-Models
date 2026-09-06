#!/usr/bin/env python3
"""index.json 自动同步脚本（push 时由 GitHub Action 调用,作者无需手改 index.json）。

规则:
- 扫描 models/<id>/<id>.yml,提取 name / version（yml 内嵌键）
- 新增模型自动追加条目;版本号变更自动同步;目录删除自动移除条目
- 保留条目中的 author/description/tags（作者在 index.json 维护一次即可）
- featured 仅在指向已删除模型时回退到第一个可用模型
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
INDEX = ROOT / "index.json"

NAME_RE = re.compile(r'(?m)^name:\s*"([^"]+)"')
VER_RE = re.compile(r'(?m)^version:\s*"?([\w.+-]+)"?')


def parse_model_file(yml: Path):
    """从模型 yml 提取 name 与 version;失败返回 None。"""
    text = yml.read_text(encoding="utf-8")
    name_m = NAME_RE.search(text)
    ver_m = VER_RE.search(text)
    if not name_m:
        print("skip (no name):", yml)
        return None
    return {
        "id": yml.parent.name,
        "name": name_m.group(1),
        "version": ver_m.group(1) if ver_m else "0.0.0",
    }


def main() -> int:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    existing = {m["id"]: m for m in data.get("models", [])}
    base_url = ("https://raw.githubusercontent.com/Serendisand/"
                "Lengbanlist-Models/main/models/{id}/{id}.yml")

    new_models = []
    seen = set()
    for yml in sorted(MODELS_DIR.glob("*/*.yml")):
        info = parse_model_file(yml)
        if not info:
            continue
        mid = info["id"]
        seen.add(mid)
        old = existing.get(mid, {})
        entry = {
            "id": mid,
            "name": info["name"],
            "version": info["version"],
            "author": old.get("author", "Serendisand"),
            "description": old.get("description", ""),
            "tags": old.get("tags", []),
            "url": base_url.format(id=mid),
        }
        if old.get("version") != info["version"]:
            print("version %s -> %s : %s" % (old.get("version"), info["version"], mid))
        new_models.append(entry)

    removed = [mid for mid in existing if mid not in seen]
    if removed:
        print("removed from index:", removed)

    data["models"] = new_models
    # featured 指向的模型被删则回退
    feat = data.get("featured") or {}
    if feat.get("modelId") not in seen and new_models:
        feat = {
            "month": feat.get("month", ""),
            "modelId": new_models[0]["id"],
            "title": "本月精选 — " + new_models[0]["name"],
            "description": new_models[0].get("description", ""),
        }
    data["featured"] = feat
    data["updated"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")

    INDEX.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("index.json synced: %d models" % len(new_models))
    return 0


if __name__ == "__main__":
    sys.exit(main())
