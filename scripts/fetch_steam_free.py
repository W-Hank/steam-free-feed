#!/usr/bin/env python3
"""抓 Steam 商店「限时免费 / 周末免费」列表，输出 data/steam-free.json
运行环境：GitHub Actions（境外，能直连 store.steampowered.com）
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone

URL = (
    "https://store.steampowered.com/search/"
    "?specials=1&maxprice=free&cc=cn&l=zh&sort_by=Price_ASC"
)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)


def fetch() -> str:
    req = urllib.request.Request(URL, headers={
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    })
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def parse(html: str):
    items = []
    chunks = re.split(r'data-ds-appid="', html)[1:]
    for ch in chunks:
        appid = ch.split('"', 1)[0].strip()
        if not appid.isdigit():
            continue
        row = ch.split('data-ds-appid="')[0]

        m_title = re.search(r'<span class="title">(.*?)</span>', row, re.S)
        if not m_title:
            continue
        name = re.sub(r"<[^>]+>", "", m_title.group(1)).strip()
        if not name:
            continue

        m_img = re.search(r'<img\s+src="([^"]+)"', row)
        image = m_img.group(1) if m_img else ""

        m_pct = re.search(r'class="discount_pct">\s*-?(\d+)%', row)
        pct = int(m_pct.group(1)) if m_pct else 0
        if pct != 100:
            continue

        items.append({
            "appid": appid,
            "name": name,
            "image": image,
            "url": "https://store.steampowered.com/app/%s/" % appid,
            "discount": pct,
        })

    seen, out = set(), []
    for it in items:
        if it["appid"] in seen:
            continue
        seen.add(it["appid"])
        out.append(it)
    return out


def main():
    try:
        html = fetch()
    except Exception as e:
        print("fetch failed:", e, file=sys.stderr)
        sys.exit(1)

    items = parse(html)
    if len(items) == 0:
        print("DEBUG html_len=", len(html))
        with open("data/debug.html", "w", encoding="utf-8") as f:
            f.write(html)

    data = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": URL,
        "count": len(items),
        "items": items,
    }
    with open("data/steam-free.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("items:", len(items))


if __name__ == "__main__":
    main()
