#!/usr/bin/env python3
"""Тянет статистику GitFut и пересобирает блок в README.md."""
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote

USER = "Kordebalet67"
COUNTRY = ""
README = Path("README.md")
START, END = "<!-- GITFUT:START -->", "<!-- GITFUT:END -->"


def fetch(user):
    url = f"https://gitfut.com/api/card/{user}"
    req = urllib.request.Request(url, headers={"User-Agent": "gitfut-readme-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def badge(label, value, color, style="flat-square"):
    def esc(s):
        return quote(str(s).replace("-", "--").replace("_", "__"), safe="")
    return f"https://img.shields.io/badge/{esc(label)}-{esc(value)}-{color}?style={style}"


def bar(score, width=10):
    filled = round(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def ovr_color(n):
    if n >= 90: return "ffd700"
    if n >= 80: return "2ea44f"
    if n >= 70: return "007ec6"
    if n >= 60: return "dbab09"
    return "fe7d37"


STAT_META = [
    ("pac", "PAC", "Pace",      "Коммиты за год"),
    ("sho", "SHO", "Shooting",  "Звёзды на репозиториях"),
    ("pas", "PAS", "Passing",   "PR + подписчики"),
    ("dri", "DRI", "Dribbling", "Разнообразие языков"),
    ("def", "DEF", "Defending", "Ревью + issues"),
    ("phy", "PHY", "Physical",  "Вклад за всё время"),
]


def render(c):
    user = c["login"]
    flag = f"?country={COUNTRY}" if COUNTRY else ""
    r = c["report"]
    o = []

    o += ['<div align="center">', "",
          f'<a href="https://gitfut.com/{user}">',
          f'  <img src="https://gitfut.com/{user}.png{flag}" width="260" alt="GitFut card" />',
          "</a>", ""]

    o += [f"![OVR]({badge('OVR', c['overall'], ovr_color(c['overall']), 'for-the-badge')}) "
          f"![POS]({badge('POS', c['position'], '8250df', 'for-the-badge')}) "
          f"![ARCH]({badge(c['archetype'], c['finishLabel'], '007ec6', 'for-the-badge')})"]

    o += ["", f"**{c['archetype']}** — _{c['archetypeBlurb']}_", "", "</div>", ""]

    o += ["### Атрибуты", "",
          "| | Стат | Значение | | Из чего считается |",
          "|:--|:--:|--:|:--|:--|"]
    for key, code, name, src in STAT_META:
        s = c["stats"][key]
        o.append(f"| **{code}** | {name} | **{s}** | `{bar(s)}` | {src} |")

    o += ["", "### Scouting metrics", "",
          "| Метрика | Значение | Оценка |", "|:--|--:|:--|"]
    for m in r["metrics"]:
        o.append(f"| {m['label']} | {m['value']} {m['unit']} | `{bar(m['score'])}` {m['score']} |")

    if r.get("playstyles"):
        o += ["", "### PlayStyles", ""]
        for p in r["playstyles"]:
            plus = "+" if p.get("plus") else ""
            o.append(f"- **{p['name']}{plus}** — {p['reason']}")

    o += ["", "### Профиль игрока", "",
          f"- **Skill moves:** {'★' * r['skillMoves']}{'☆' * (5 - r['skillMoves'])} — {r['reasons']['skillMoves']}",
          f"- **Weak foot:** {'★' * r['weakFoot']}{'☆' * (5 - r['weakFoot'])} — {r['reasons']['weakFoot']}",
          f"- **Work rate:** {r['workRate']['attack']} / {r['workRate']['defense']}",
          f"- **Style:** {r['style']} — {r['reasons']['style']}"]

    if c.get("awards"):
        o += ["", "### Трофеи", ""]
        for a in c["awards"]:
            o.append(f"- **{a.get('name', 'Award')}** — {a.get('reason', '')}")

    o += ["", f"<sub>Обновлено автоматически · "
              f"[полный scout-отчёт →](https://gitfut.com/{user})</sub>"]
    return "\n".join(o)


def main():
    try:
        card = fetch(USER)
    except Exception as e:
        print(f"GitFut недоступен ({e}) — оставляю прежний блок", file=sys.stderr)
        return 0

    block = f"{START}\n{render(card)}\n{END}"
    text = README.read_text(encoding="utf-8")

    if START not in text or END not in text:
        print("Маркеры GITFUT:START/END не найдены в README.md", file=sys.stderr)
        return 1

    new = re.sub(f"{re.escape(START)}.*?{re.escape(END)}",
                 lambda _: block, text, flags=re.S)
    if new != text:
        README.write_text(new, encoding="utf-8")
        print("README обновлён")
    else:
        print("Изменений нет")
    return 0


if __name__ == "__main__":
    sys.exit(main())
