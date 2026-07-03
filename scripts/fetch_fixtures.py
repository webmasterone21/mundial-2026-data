#!/usr/bin/env python3
"""
scripts/fetch_fixtures.py
Genera data/fixtures.json con todos los partidos terminados del Mundial 2026.
Cubre fase de grupos (para Mejores Terceros) y llaves (para marcadores en bracket).
Una sola llamada a la API — 96 calls/día dentro del plan Free (100/día).
"""

import json, os, sys, datetime, urllib.request

API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
LEAGUE  = 1
SEASON  = 2026
RAW_OUT = "data/fixtures_raw.json"
OUT     = "data/fixtures.json"

GRUPOS_FIFA = {
    "Mexico": "Group A",        "South Africa": "Group A",
    "South Korea": "Group A",   "Czech Republic": "Group A", "Czechia": "Group A",
    "Canada": "Group B",        "Bosnia & Herzegovina": "Group B",
    "Bosnia and Herzegovina": "Group B",
    "Qatar": "Group B",         "Switzerland": "Group B",
    "Brazil": "Group C",        "Morocco": "Group C",
    "Scotland": "Group C",      "Haiti": "Group C",
    "United States": "Group D", "USA": "Group D",
    "Australia": "Group D",     "Paraguay": "Group D",
    "Turkey": "Group D",        "Türkiye": "Group D",
    "Germany": "Group E",       "Ivory Coast": "Group E",
    "Cote d'Ivoire": "Group E", "Côte d'Ivoire": "Group E",
    "Ecuador": "Group E",       "Curaçao": "Group E",
    "Netherlands": "Group F",   "Japan": "Group F",
    "Sweden": "Group F",        "Tunisia": "Group F",
    "Belgium": "Group G",       "Egypt": "Group G",
    "Iran": "Group G",          "New Zealand": "Group G",
    "Spain": "Group H",         "Uruguay": "Group H",
    "Cape Verde": "Group H",    "Cape Verde Islands": "Group H",
    "Saudi Arabia": "Group H",
    "France": "Group I",        "Norway": "Group I",
    "Senegal": "Group I",       "Iraq": "Group I",
    "Argentina": "Group J",     "Austria": "Group J",
    "Algeria": "Group J",       "Jordan": "Group J",
    "Colombia": "Group K",      "Portugal": "Group K",
    "DR Congo": "Group K",      "Congo DR": "Group K",
    "Dem. Rep. Congo": "Group K","Uzbekistan": "Group K",
    "England": "Group L",       "Ghana": "Group L",
    "Croatia": "Group L",       "Panama": "Group L",
}

GROUP_ROUNDS    = {"Group Stage - 1", "Group Stage - 2", "Group Stage - 3"}
KNOCKOUT_ROUNDS = {
    "Round of 32", "Round of 16",
    "Quarter-finals", "Semi-finals",
    "3rd Place Final", "Final",
}


def main():
    if not API_KEY:
        print("ERROR: variable API_FOOTBALL_KEY no definida", file=sys.stderr)
        sys.exit(1)

    url = f"https://v3.football.api-sports.io/fixtures?league={LEAGUE}&season={SEASON}"
    print(f"[fetch] GET {url}")
    req  = urllib.request.Request(url, headers={"x-apisports-key": API_KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())

    errors = data.get("errors", {})
    if errors and errors != [] and errors != {}:
        print(f"ERROR API: {errors}", file=sys.stderr)
        sys.exit(1)

    response = data.get("response", [])
    print(f"[fetch] {len(response)} fixtures recibidos")
    if not response:
        print("ERROR: sin fixtures", file=sys.stderr)
        sys.exit(1)

    os.makedirs("data", exist_ok=True)
    with open(RAW_OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))

    output = []
    for f in response:
        status = f["fixture"]["status"]["short"]
        round_ = f["league"].get("round", "")
        group_ = f["league"].get("group", "") or ""
        home   = f["teams"]["home"]["name"]
        away   = f["teams"]["away"]["name"]
        gh     = f["goals"].get("home")
        ga     = f["goals"].get("away")

        if status not in ("FT", "AET", "PEN"):
            continue
        if gh is None or ga is None:
            continue

        is_group    = round_ in GROUP_ROUNDS
        is_knockout = round_ in KNOCKOUT_ROUNDS
        if not is_group and not is_knockout:
            continue

        row = {
            "id": f["fixture"]["id"], "date": f["fixture"]["date"],
            "status": status, "round": round_,
            "home": home, "away": away,
            "goalsH": gh, "goalsA": ga,
        }

        if is_group:
            grp = group_
            if not grp or grp == "Group Stage":
                grp = GRUPOS_FIFA.get(home) or GRUPOS_FIFA.get(away) or ""
            row["group"] = grp

        if status == "PEN":
            pen   = f.get("score", {}).get("penalty", {})
            pen_h = pen.get("home")
            pen_a = pen.get("away")
            if pen_h is not None and pen_a is not None:
                row["penH"] = pen_h
                row["penA"] = pen_a

        output.append(row)

    g = sum(1 for r in output if "group" in r)
    k = sum(1 for r in output if "group" not in r)
    p = sum(1 for r in output if "penH" in r)

    result = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "total": len(output), "group_matches": g,
        "knockout_matches": k, "fixtures": output,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"[ok] {OUT} — Grupos: {g} | Llaves: {k} | Penales: {p}")


if __name__ == "__main__":
    main()
