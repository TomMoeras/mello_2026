#!/usr/bin/env python3
"""Generate a self-contained HTML leaderboard page from a predictions JSON
file and the actual results.

Usage:
    python src/generate_leaderboard.py predictions.json RESULT1 RESULT2 ... RESULT12

    python src/generate_leaderboard.py predictions.json \\
        Felicia Greczula Medina "A*Teens" "Lilla Al-Fadji" \\
        "Smash Into Pieces" "Robin Bengtsson" "Sanna Nielsen" \\
        Cimberly "Meira Omar" "Saga Ludvigsson" "Brandsta City Släckers"

The HTML file is written to the current directory as
``mello2026_leaderboard.html``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from html import escape

# ---------------------------------------------------------------------------
# Constants (mirrored from app.py)
# ---------------------------------------------------------------------------
CONTESTANTS = [
    {"artist": "A*Teens", "song": "Iconic",
     "photo": "https://mellopedia.svt.se/images/thumb/3/3e/A%2ATeens_Melodifestivalen_2026.jpg/300px-A%2ATeens_Melodifestivalen_2026.jpg"},
    {"artist": "Meira Omar", "song": "Dooset Daram",
     "photo": "https://mellopedia.svt.se/images/thumb/4/43/Meira_Omar_Melodifestivalen_2026.jpg/300px-Meira_Omar_Melodifestivalen_2026.jpg"},
    {"artist": "Lilla Al-Fadji", "song": "Delulu",
     "photo": "https://mellopedia.svt.se/images/thumb/4/49/Lilla_Al-Fadji_Melodifestivalen_2026.jpg/300px-Lilla_Al-Fadji_Melodifestivalen_2026.jpg"},
    {"artist": "Saga Ludvigsson", "song": "Ain't Today",
     "photo": "https://mellopedia.svt.se/images/thumb/b/b7/Saga_Ludvigsson_Melodifestivalen_2026.jpg/300px-Saga_Ludvigsson_Melodifestivalen_2026.jpg"},
    {"artist": "Smash Into Pieces", "song": "Hollow",
     "photo": "https://mellopedia.svt.se/images/thumb/a/ab/Smash_Into_Pieces_2024.jpg/300px-Smash_Into_Pieces_2024.jpg"},
    {"artist": "Cimberly", "song": "Eternity",
     "photo": "https://mellopedia.svt.se/images/thumb/2/26/Cimberly_Melodifestivalen_2026.jpg/300px-Cimberly_Melodifestivalen_2026.jpg"},
    {"artist": "Medina", "song": "Viva l'amor",
     "photo": "https://mellopedia.svt.se/images/thumb/e/e7/Medina_Melodifestivalen_2026.jpg/300px-Medina_Melodifestivalen_2026.jpg"},
    {"artist": "Greczula", "song": "Half of Me",
     "photo": "https://mellopedia.svt.se/images/thumb/5/5b/Greczula_Melodifestivalen_2026.jpg/300px-Greczula_Melodifestivalen_2026.jpg"},
    {"artist": "Robin Bengtsson", "song": "Honey Honey",
     "photo": "https://mellopedia.svt.se/images/thumb/c/c6/Robin_Bengtsson_Melodifestivalen_2026.jpg/300px-Robin_Bengtsson_Melodifestivalen_2026.jpg"},
    {"artist": "Felicia", "song": "My System",
     "photo": "https://mellopedia.svt.se/images/thumb/3/3c/FELICIA_Melodifestivalen_2026.jpg/300px-FELICIA_Melodifestivalen_2026.jpg"},
    {"artist": "Sanna Nielsen", "song": "Waste Your Love",
     "photo": "https://mellopedia.svt.se/images/thumb/3/3b/Waste_Your_Love_2026_Sanna_Nielsen.jpg/300px-Waste_Your_Love_2026_Sanna_Nielsen.jpg"},
    {"artist": "Brandsta City Sl\u00e4ckers", "song": "Rakt in i elden",
     "photo": "https://mellopedia.svt.se/images/thumb/2/2f/Brandsta_City_Sl%C3%A4ckers_Melodifestivalen_2026.jpg/300px-Brandsta_City_Sl%C3%A4ckers_Melodifestivalen_2026.jpg"},
]

ARTIST_SONGS = {c["artist"]: c["song"] for c in CONTESTANTS}
ARTIST_PHOTOS = {c["artist"]: c["photo"] for c in CONTESTANTS}

BOOKMAKER_ODDS = {
    "Felicia":                     {"win_pct": 69,  "avg_odds": 1.22},
    "Greczula":                    {"win_pct": 9,   "avg_odds": 9.00},
    "Medina":                      {"win_pct": 5,   "avg_odds": 15.71},
    "Lilla Al-Fadji":              {"win_pct": 5,   "avg_odds": 17.29},
    "A*Teens":                     {"win_pct": 4,   "avg_odds": 21.29},
    "Smash Into Pieces":           {"win_pct": 4,   "avg_odds": 23.29},
    "Brandsta City Sl\u00e4ckers": {"win_pct": 1,   "avg_odds": 67.71},
    "Sanna Nielsen":               {"win_pct": 1,   "avg_odds": 69.14},
    "Cimberly":                    {"win_pct": 1,   "avg_odds": 145.00},
    "Meira Omar":                  {"win_pct": 1,   "avg_odds": 173.86},
    "Saga Ludvigsson":             {"win_pct": 0.5, "avg_odds": 240.57},
    "Robin Bengtsson":             {"win_pct": 0.5, "avg_odds": 343.43},
}

ODDS_RANKED = sorted(BOOKMAKER_ODDS, key=lambda a: BOOKMAKER_ODDS[a]["avg_odds"])

WINNER_BONUS = 3
BASE_POINTS = 2
TOP3_PROXIMITY = {0: 15, 1: 12, 2: 9, 3: 6, 4: 4, 5: 2, 6: 1.5, 7: 0.75}
LOWER_PROXIMITY = {0: 10, 1: 8, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1, 7: 0.5}
OUTSIDE_TOP5_PROXIMITY = {1: 7, 2: 5, 3: 3, 4: 1.5, 5: 1, 6: 0.5, 7: 0.25}
MAX_DIFF = 7

MEDAL = {0: "\U0001f947", 1: "\U0001f948", 2: "\U0001f949"}

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def calculate_score(prediction: list[str], actual: list[str]) -> float:
    score = 0.0
    pos_map = {a.strip().lower(): i for i, a in enumerate(actual)}
    if (prediction and actual
            and prediction[0].strip().lower() == actual[0].strip().lower()):
        score += WINNER_BONUS
    for pred_pos, artist in enumerate(prediction):
        key = artist.strip().lower()
        if key not in pos_map:
            continue
        actual_pos = pos_map[key]
        diff = abs(pred_pos - actual_pos)
        if actual_pos < 5:
            score += BASE_POINTS
            table = TOP3_PROXIMITY if actual_pos < 3 else LOWER_PROXIMITY
            if diff <= MAX_DIFF:
                score += table.get(diff, 0)
        else:
            if diff <= MAX_DIFF:
                score += OUTSIDE_TOP5_PROXIMITY.get(diff, 0)
    return score


def get_breakdown(prediction: list[str], actual: list[str]) -> list[dict]:
    pos_map = {a.strip().lower(): i for i, a in enumerate(actual)}
    rows: list[dict] = []
    for pred_pos, artist in enumerate(prediction):
        key = artist.strip().lower()
        row = {"pred_pos": pred_pos + 1, "artist": artist,
               "song": ARTIST_SONGS.get(artist, ""),
               "actual_pos": None, "diff": None, "points": 0.0, "details": []}
        if key not in pos_map:
            row["details"].append("Not in results")
            rows.append(row)
            continue
        actual_pos = pos_map[key]
        diff = abs(pred_pos - actual_pos)
        row["actual_pos"] = actual_pos + 1
        row["diff"] = diff
        pts = 0.0
        if pred_pos == 0 and actual_pos == 0:
            pts += WINNER_BONUS
            row["details"].append(f"+{WINNER_BONUS} winner bonus")
        if actual_pos < 5:
            pts += BASE_POINTS
            row["details"].append(f"+{BASE_POINTS} in top 5")
            table = TOP3_PROXIMITY if actual_pos < 3 else LOWER_PROXIMITY
            tier = "top 3" if actual_pos < 3 else "4th-5th"
            if diff <= MAX_DIFF:
                prox = table.get(diff, 0)
                pts += prox
                lbl = "exact" if diff == 0 else f"off by {diff}"
                row["details"].append(f"+{prox} proximity ({lbl}, {tier})")
            else:
                row["details"].append(f"0 proximity (off by {diff})")
        else:
            if diff <= MAX_DIFF:
                prox = OUTSIDE_TOP5_PROXIMITY.get(diff, 0)
                pts += prox
                row["details"].append(f"+{prox} (off by {diff}, finished {actual_pos+1})")
            else:
                row["details"].append(f"0 pts (off by {diff}, finished {actual_pos+1})")
        row["points"] = pts
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
def compute_stats(preds: dict, actual: list[str]) -> dict:
    total = len(preds)
    if total == 0 or not actual:
        return {}
    _low = lambda s: s.strip().lower()
    winner = actual[0]
    top3 = actual[:3]
    top5 = actual[:5]

    winner_correct = sum(
        1 for d in preds.values()
        if d["prediction"] and _low(d["prediction"][0]) == _low(winner))
    perfect_top3 = sum(
        1 for d in preds.values()
        if len(d["prediction"]) >= 3
        and all(_low(d["prediction"][i]) == _low(top3[i]) for i in range(3)))
    total_exact = sum(
        1 for d in preds.values()
        for i, a in enumerate(d["prediction"])
        if i < len(actual) and _low(a) == _low(actual[i]))
    total_possible = total * 5
    accuracy_pct = (total_exact / total_possible * 100) if total_possible else 0

    winner_picks: dict[str, int] = {}
    for d in preds.values():
        if d["prediction"]:
            p = d["prediction"][0]
            winner_picks[p] = winner_picks.get(p, 0) + 1
    pop_winner = max(winner_picks, key=winner_picks.get) if winner_picks else None

    underdog_data: dict[str, dict] = {}
    for name, d in preds.items():
        tot_odds = 0.0
        picks: list[str] = []
        for artist in d["prediction"]:
            if _low(artist) in [_low(a) for a in top5]:
                odds = BOOKMAKER_ODDS.get(artist, {}).get("avg_odds", 1)
                if odds >= 20:
                    tot_odds += odds
                    picks.append(artist)
        underdog_data[name] = {"score": tot_odds, "picks": picks}
    underdog_champ = max(underdog_data, key=lambda x: underdog_data[x]["score"]) if underdog_data else None
    underdog_best = underdog_data.get(underdog_champ, {}) if underdog_champ else {}

    odds_vs_reality = []
    for bm_rank, artist in enumerate(ODDS_RANKED):
        actual_rank = None
        for i, a in enumerate(actual):
            if _low(a) == _low(artist):
                actual_rank = i + 1
                break
        is_upset = actual_rank is not None and actual_rank <= 5 and (bm_rank + 1) > 5
        odds_vs_reality.append({
            "artist": artist, "bm_rank": bm_rank + 1,
            "actual_rank": actual_rank,
            "odds": BOOKMAKER_ODDS[artist]["avg_odds"],
            "win_pct": BOOKMAKER_ODDS[artist]["win_pct"],
            "upset": is_upset,
        })

    scores = [calculate_score(d["prediction"], actual) for d in preds.values()]
    return {
        "total": total, "winner": winner, "top3": top3, "top5": top5,
        "winner_correct": winner_correct,
        "winner_pct": (winner_correct / total * 100) if total else 0,
        "perfect_top3": perfect_top3,
        "total_exact": total_exact, "accuracy_pct": accuracy_pct,
        "pop_winner": pop_winner,
        "pop_winner_count": winner_picks.get(pop_winner, 0) if pop_winner else 0,
        "underdog_champ": underdog_champ, "underdog_best": underdog_best,
        "odds_vs_reality": odds_vs_reality,
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
    }


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------
def _e(s: str) -> str:
    return escape(str(s))


def generate_html(preds: dict, actual: list[str]) -> str:
    stats = compute_stats(preds, actual)

    board = []
    for user, data in preds.items():
        pred = data["prediction"]
        score = calculate_score(pred, actual)
        board.append({"name": user, "score": score, "prediction": pred})
    board.sort(key=lambda x: (-x["score"], x["name"]))

    parts: list[str] = []
    p = parts.append

    p("<!DOCTYPE html>")
    p('<html lang="en"><head><meta charset="UTF-8">')
    p('<meta name="viewport" content="width=device-width,initial-scale=1">')
    p("<title>Melodifestivalen 2026 - Leaderboard</title>")
    p("<style>")
    p(CSS)
    p("</style></head><body>")

    # Header
    p('<div class="page">')
    p('<div class="header">')
    p("<h1>\U0001f1f8\U0001f1ea Melodifestivalen 2026</h1>")
    p("<p>Prediction Game - Leaderboard</p>")
    p("</div>")

    # Actual top 5
    p('<h2>Actual Top 5</h2>')
    for i, artist in enumerate(actual[:5]):
        photo = ARTIST_PHOTOS.get(artist, "")
        song = ARTIST_SONGS.get(artist, "")
        tier = {0: "gold", 1: "silver", 2: "bronze"}.get(i, "plain")
        p(_rank_row(i + 1, tier, photo, artist, song))

    p(f'<p class="full-result">{" > ".join(f"{i+1}. {a}" for i, a in enumerate(actual))}</p>')

    # Statistics
    if stats:
        p('<h2>Statistics</h2>')
        p('<div class="stats-grid">')
        _stat(p, "\U0001f3c6", "Predicted the winner",
              f'{stats["winner_correct"]}/{stats["total"]}',
              f'{stats["winner_pct"]:.0f}% picked {_e(stats["winner"])} as #1')
        _stat(p, "\U0001f3af", "Perfect Top 3",
              str(stats["perfect_top3"]),
              "got the exact top 3!" if stats["perfect_top3"] > 0
              else "Nobody nailed the exact top 3")
        _stat(p, "\U0001f4ca", "Exact Position Hits",
              f'{stats["total_exact"]}/{stats["total"]*5}',
              f'{stats["accuracy_pct"]:.0f}% of positions matched exactly')
        if stats.get("pop_winner"):
            _stat(p, "\U0001f465", "Most Popular #1 Pick",
                  _e(stats["pop_winner"]),
                  f'Chosen by {stats["pop_winner_count"]}/{stats["total"]}')
        _stat(p, "\U0001f4c8", "Average Score",
              f'{stats["avg_score"]:.1f}',
              f'Top score: {stats["max_score"]:.1f} / 78 possible')
        p("</div>")  # stats-grid

        uc = stats.get("underdog_champ")
        ub = stats.get("underdog_best", {})
        if uc and ub.get("score", 0) > 0:
            picks_str = ", ".join(ub.get("picks", []))
            p('<div class="underdog-card">')
            p(f'<h3>\U0001f525 Underdog Champion: {_e(uc)}</h3>')
            p(f'<p>Correctly predicted long-shot artists: <strong>{_e(picks_str)}</strong></p>')
            p("</div>")

        # Odds table
        p("<h3>Bookmakers vs Reality</h3>")
        p('<table class="odds-table"><thead><tr>')
        p("<th>Odds Rank</th><th>Artist</th><th>Win %</th><th>Avg Odds</th><th>Actual</th>")
        p("</tr></thead><tbody>")
        for r in stats["odds_vs_reality"]:
            cls = ' class="upset"' if r["upset"] else ""
            actual_str = f'#{r["actual_rank"]}' if r["actual_rank"] else "-"
            upset_tag = ' <span class="upset-badge">UPSET</span>' if r["upset"] else ""
            p(f'<tr{cls}><td>#{r["bm_rank"]}</td><td>{_e(r["artist"])}{upset_tag}</td>'
              f'<td>{r["win_pct"]}%</td><td>{r["odds"]:.1f}</td>'
              f'<td><strong>{actual_str}</strong></td></tr>')
        p("</tbody></table>")

    # Leaderboard
    p("<h2>Leaderboard</h2>")
    for rank, entry in enumerate(board):
        medal = MEDAL.get(rank, f"#{rank + 1}")
        p(f'<div class="lb-entry">')
        p(f'<div class="lb-header">')
        p(f'<span class="lb-medal">{medal}</span>')
        p(f'<span class="lb-name">{_e(entry["name"])}</span>')
        p(f'<span class="lb-score">{entry["score"]:.1f} pts</span>')
        p("</div>")

        breakdown = get_breakdown(entry["prediction"], actual)
        p('<div class="lb-breakdown">')
        for row in breakdown:
            photo = ARTIST_PHOTOS.get(row["artist"], "")
            if row["actual_pos"] is not None:
                if row["diff"] == 0:
                    badge_cls = "badge-exact"
                    badge_txt = "exact!"
                elif row["diff"] <= 2:
                    badge_cls = "badge-close"
                    badge_txt = f"off by {row['diff']}"
                else:
                    badge_cls = "badge-far"
                    badge_txt = f"off by {row['diff']}"
                pos_info = f'actual #{row["actual_pos"]} <span class="{badge_cls}">{badge_txt}</span>'
            else:
                pos_info = '<span class="badge-far">not in results</span>'

            detail_str = " | ".join(row["details"])
            p(f'<div class="bd-row">')
            p(f'<img src="{photo}" class="bd-photo" alt="{_e(row["artist"])}">')
            p(f'<div class="bd-info">')
            p(f'<strong>{row["pred_pos"]}. {_e(row["artist"])}</strong>'
              f' <em>"{_e(row["song"])}"</em>')
            p(f'<br><small>{pos_info}</small>')
            p(f'<br><small class="bd-detail">{_e(detail_str)}</small>')
            p("</div>")
            p(f'<div class="bd-pts">{row["points"]:.1f}</div>')
            p("</div>")
        p("</div>")  # lb-breakdown
        p("</div>")  # lb-entry

    p('<div class="footer">Melodifestivalen 2026 - Saturday 7 March 2026 - Strawberry Arena, Stockholm</div>')
    p("</div>")  # page
    p("</body></html>")
    return "\n".join(parts)


def _rank_row(pos: int, tier: str, photo: str, name: str, song: str) -> str:
    return (
        f'<div class="rank-row {tier}">'
        f'<div class="rank-num">{pos}</div>'
        f'<img class="rank-photo" src="{photo}" alt="{_e(name)}">'
        f'<div class="rank-info"><strong>{_e(name)}</strong>'
        f'<br><em>"{_e(song)}"</em></div>'
        f"</div>"
    )


def _stat(p, icon: str, title: str, value: str, subtitle: str):
    p(f'<div class="stat-card">'
      f'<div class="stat-icon">{icon}</div>'
      f'<div class="stat-title">{_e(title)}</div>'
      f'<div class="stat-value">{value}</div>'
      f'<div class="stat-sub">{subtitle}</div>'
      f"</div>")


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
:root { --blue: #003DA5; --gold: #FECC02; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', sans-serif; background: #f5f6fb; color: #1a1a2e; }
.page { max-width: 720px; margin: 0 auto; padding: 24px 16px; }
.header { text-align: center; margin-bottom: 24px; padding-bottom: 16px;
           border-bottom: 3px solid var(--gold); }
.header h1 { color: var(--blue); font-size: 2rem; }
.header p { color: #555; font-size: .95rem; margin-top: 4px; }
h2 { color: var(--blue); margin: 28px 0 12px; font-size: 1.3rem; }
h3 { color: var(--blue); margin: 20px 0 10px; font-size: 1.1rem; }
.full-result { font-size: .8rem; color: #888; margin: 8px 0 0; }

/* Rank rows */
.rank-row { display: flex; align-items: center; gap: 12px; padding: 10px 14px;
            margin-bottom: 8px; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
.rank-row.gold   { background: linear-gradient(135deg,#fff9db,#ffeaa0); border: 2px solid #e6b800; }
.rank-row.gold .rank-num { color: #b8860b; }
.rank-row.silver { background: linear-gradient(135deg,#f4f6f8,#dde2ea); border: 2px solid #b8c0cc; }
.rank-row.silver .rank-num { color: #7a8799; }
.rank-row.bronze { background: linear-gradient(135deg,#fff0e8,#ffd4b0); border: 2px solid #c8834a; }
.rank-row.bronze .rank-num { color: #a0522d; }
.rank-row.plain  { background: #f0f2f8; border: 2px solid #dde3f0; }
.rank-row.plain .rank-num { color: var(--blue); }
.rank-num { font-size: 1.5rem; font-weight: 900; min-width: 28px; text-align: center; }
.rank-photo { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.rank-info { flex: 1; }
.rank-info strong { font-size: .95rem; }
.rank-info em { font-size: .8rem; color: #555; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
              gap: 12px; margin: 12px 0; }
.stat-card { text-align: center; padding: 16px 10px; background: #fff; border: 1px solid #e0e4ef;
             border-radius: 14px; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.stat-icon { font-size: 1.8rem; }
.stat-title { font-size: .72rem; font-weight: 700; color: #888; text-transform: uppercase;
              letter-spacing: .8px; margin-top: 2px; }
.stat-value { font-size: 1.8rem; font-weight: 900; color: var(--blue); margin: 4px 0; }
.stat-sub { font-size: .82rem; color: #555; }

.underdog-card { background: #fff; border: 1px solid #e0e4ef; border-left: 4px solid #f59e0b;
                 border-radius: 14px; padding: 16px; margin: 12px 0; }
.underdog-card h3 { margin: 0 0 6px; color: #b45309; }

/* Odds table */
.odds-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: .85rem;
              margin-bottom: 16px; }
.odds-table th { background: var(--blue); color: #fff; padding: 8px 10px; text-align: left;
                 font-size: .75rem; text-transform: uppercase; letter-spacing: .5px; }
.odds-table th:first-child { border-radius: 8px 0 0 0; }
.odds-table th:last-child  { border-radius: 0 8px 0 0; }
.odds-table td { padding: 6px 10px; border-bottom: 1px solid #e8ecf4; }
.odds-table tr:nth-child(even) td { background: #f5f6fb; }
.odds-table tr.upset td { background: #fef9c3; font-weight: 600; }
.upset-badge { display: inline-block; background: #f59e0b; color: #fff; border-radius: 4px;
               padding: 1px 6px; font-size: .7rem; font-weight: 700; margin-left: 4px; }

/* Leaderboard */
.lb-entry { background: #fff; border: 1px solid #e0e4ef; border-radius: 14px;
            margin-bottom: 14px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.lb-header { display: flex; align-items: center; gap: 10px; padding: 14px 16px;
             border-bottom: 1px solid #eee; }
.lb-medal { font-size: 1.4rem; }
.lb-name { flex: 1; font-weight: 800; font-size: 1.05rem; }
.lb-score { font-weight: 800; font-size: 1.1rem; color: var(--blue);
            background: #eef1fa; padding: 4px 12px; border-radius: 1rem; }
.lb-breakdown { padding: 10px 16px; }
.bd-row { display: flex; align-items: center; gap: 10px; padding: 6px 0;
          border-bottom: 1px solid #f0f2f8; }
.bd-row:last-child { border-bottom: none; }
.bd-photo { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.bd-info { flex: 1; font-size: .88rem; }
.bd-info em { color: #555; }
.bd-info small { color: #888; }
.bd-detail { color: #aaa; }
.bd-pts { font-weight: 800; font-size: 1rem; color: var(--blue); min-width: 44px;
          text-align: right; }
.badge-exact { display: inline-block; background: #16a34a; color: #fff; border-radius: 4px;
               padding: 0 6px; font-size: .72rem; font-weight: 700; }
.badge-close { display: inline-block; background: #eab308; color: #fff; border-radius: 4px;
               padding: 0 6px; font-size: .72rem; font-weight: 700; }
.badge-far   { display: inline-block; background: #94a3b8; color: #fff; border-radius: 4px;
               padding: 0 6px; font-size: .72rem; font-weight: 700; }
.footer { text-align: center; font-size: .8rem; color: #888; margin-top: 32px; padding-top: 12px;
          border-top: 2px solid var(--gold); }
@media print { body { background: #fff; } .page { max-width: 100%; } }
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate a Mello 2026 leaderboard HTML from predictions JSON + actual results."
    )
    parser.add_argument(
        "predictions",
        help="Path to the predictions JSON file (downloaded from the admin panel)",
    )
    parser.add_argument(
        "results",
        nargs=12,
        metavar="ARTIST",
        help="The 12 artists in actual finishing order (1st to 12th)",
    )
    parser.add_argument(
        "-o", "--output",
        default="mello2026_leaderboard.html",
        help="Output HTML file (default: mello2026_leaderboard.html)",
    )

    args = parser.parse_args()

    preds_path = Path(args.predictions)
    if not preds_path.exists():
        print(f"Error: {preds_path} not found", file=sys.stderr)
        sys.exit(1)

    preds = json.loads(preds_path.read_text())
    actual = args.results

    # Validate artist names
    known = {a.lower() for a in ARTIST_SONGS}
    for a in actual:
        if a.lower() not in known:
            print(f"Warning: '{a}' not recognized as a contestant", file=sys.stderr)

    # Print summary to terminal
    board = []
    for user, data in preds.items():
        score = calculate_score(data["prediction"], actual)
        board.append((user, score, data["prediction"]))
    board.sort(key=lambda x: (-x[1], x[0]))

    print(f"\nMelodifestivalen 2026 - Leaderboard")
    print(f"{'='*42}")
    print(f"Actual top 5: {', '.join(actual[:5])}")
    print(f"Participants:  {len(preds)}")
    print()
    for rank, (name, score, pred) in enumerate(board):
        medal = MEDAL.get(rank, f"#{rank+1:>2}")
        print(f"  {medal} {name:<20s} {score:6.1f} pts   ({', '.join(pred)})")
    print()

    stats = compute_stats(preds, actual)
    if stats:
        print(f"Winner predicted correctly: {stats['winner_correct']}/{stats['total']}")
        print(f"Perfect top 3:             {stats['perfect_top3']}")
        print(f"Average score:             {stats['avg_score']:.1f}")
        print(f"Top score:                 {stats['max_score']:.1f} / 78")
        if stats.get("underdog_champ") and stats.get("underdog_best", {}).get("score", 0) > 0:
            print(f"Underdog champion:         {stats['underdog_champ']}")
        print()

    # Write HTML
    html = generate_html(preds, actual)
    out = Path(args.output)
    out.write_text(html, encoding="utf-8")
    print(f"HTML leaderboard written to: {out.resolve()}")


if __name__ == "__main__":
    main()
