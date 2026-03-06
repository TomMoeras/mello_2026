import streamlit as st
import json
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Mello 2026 Predictions",
    page_icon="\U0001f1f8\U0001f1ea",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONTESTANTS = [
    {
        "artist": "A*Teens",
        "song": "Iconic",
        "order": 1,
        "photo": "https://mellopedia.svt.se/images/thumb/3/3e/A%2ATeens_Melodifestivalen_2026.jpg/300px-A%2ATeens_Melodifestivalen_2026.jpg",
    },
    {
        "artist": "Meira Omar",
        "song": "Dooset Daram",
        "order": 2,
        "photo": "https://mellopedia.svt.se/images/thumb/4/43/Meira_Omar_Melodifestivalen_2026.jpg/300px-Meira_Omar_Melodifestivalen_2026.jpg",
    },
    {
        "artist": "Lilla Al-Fadji",
        "song": "Delulu",
        "order": 3,
        "photo": "https://mellopedia.svt.se/images/thumb/4/49/Lilla_Al-Fadji_Melodifestivalen_2026.jpg/300px-Lilla_Al-Fadji_Melodifestivalen_2026.jpg",
    },
    {
        "artist": "Saga Ludvigsson",
        "song": "Ain't Today",
        "order": 4,
        "photo": "https://mellopedia.svt.se/images/thumb/b/b7/Saga_Ludvigsson_Melodifestivalen_2026.jpg/300px-Saga_Ludvigsson_Melodifestivalen_2026.jpg",
    },
    {
        "artist": "Smash Into Pieces",
        "song": "Hollow",
        "order": 5,
        "photo": "https://mellopedia.svt.se/images/thumb/a/ab/Smash_Into_Pieces_2024.jpg/300px-Smash_Into_Pieces_2024.jpg",
    },
    {
        "artist": "Cimberly",
        "song": "Eternity",
        "order": 6,
        "photo": "https://mellopedia.svt.se/images/thumb/2/26/Cimberly_Melodifestivalen_2026.jpg/300px-Cimberly_Melodifestivalen_2026.jpg",
    },
    {
        "artist": "Medina",
        "song": "Viva l'amor",
        "order": 7,
        "photo": "https://mellopedia.svt.se/images/thumb/e/e7/Medina_Melodifestivalen_2026.jpg/300px-Medina_Melodifestivalen_2026.jpg",
    },
    {
        "artist": "Greczula",
        "song": "Half of Me",
        "order": 8,
        "photo": "https://mellopedia.svt.se/images/thumb/5/5b/Greczula_Melodifestivalen_2026.jpg/300px-Greczula_Melodifestivalen_2026.jpg",
    },
    {
        "artist": "Robin Bengtsson",
        "song": "Honey Honey",
        "order": 9,
        "photo": "https://mellopedia.svt.se/images/thumb/c/c6/Robin_Bengtsson_Melodifestivalen_2026.jpg/300px-Robin_Bengtsson_Melodifestivalen_2026.jpg",
    },
    {
        "artist": "Felicia",
        "song": "My System",
        "order": 10,
        "photo": "https://mellopedia.svt.se/images/thumb/3/3c/FELICIA_Melodifestivalen_2026.jpg/300px-FELICIA_Melodifestivalen_2026.jpg",
    },
    {
        "artist": "Sanna Nielsen",
        "song": "Waste Your Love",
        "order": 11,
        "photo": "https://mellopedia.svt.se/images/thumb/3/3b/Waste_Your_Love_2026_Sanna_Nielsen.jpg/300px-Waste_Your_Love_2026_Sanna_Nielsen.jpg",
    },
    {
        "artist": "Brandsta City Sl\u00e4ckers",
        "song": "Rakt in i elden",
        "order": 12,
        "photo": "https://mellopedia.svt.se/images/thumb/2/2f/Brandsta_City_Sl%C3%A4ckers_Melodifestivalen_2026.jpg/300px-Brandsta_City_Sl%C3%A4ckers_Melodifestivalen_2026.jpg",
    },
]

ARTIST_NAMES = [c["artist"] for c in CONTESTANTS]
ARTIST_SONGS = {c["artist"]: c["song"] for c in CONTESTANTS}
ARTIST_PHOTOS = {c["artist"]: c["photo"] for c in CONTESTANTS}

# Bookmaker odds (average across Betsson, Bwin, Unibet, CoolBet, SvenskaSpel,
# Bet365, Betano) — sourced pre-final
BOOKMAKER_ODDS = {
    "Felicia":                    {"win_pct": 69,  "avg_odds": 1.22},
    "Greczula":                   {"win_pct": 9,   "avg_odds": 9.00},
    "Medina":                     {"win_pct": 5,   "avg_odds": 15.71},
    "Lilla Al-Fadji":             {"win_pct": 5,   "avg_odds": 17.29},
    "A*Teens":                    {"win_pct": 4,   "avg_odds": 21.29},
    "Smash Into Pieces":          {"win_pct": 4,   "avg_odds": 23.29},
    "Brandsta City Sl\u00e4ckers": {"win_pct": 1,   "avg_odds": 67.71},
    "Sanna Nielsen":              {"win_pct": 1,   "avg_odds": 69.14},
    "Cimberly":                   {"win_pct": 1,   "avg_odds": 145.00},
    "Meira Omar":                 {"win_pct": 1,   "avg_odds": 173.86},
    "Saga Ludvigsson":            {"win_pct": 0.5, "avg_odds": 240.57},
    "Robin Bengtsson":            {"win_pct": 0.5, "avg_odds": 343.43},
}

ODDS_RANKED = sorted(BOOKMAKER_ODDS.keys(), key=lambda a: BOOKMAKER_ODDS[a]["avg_odds"])

DATA_DIR = Path(__file__).parent / "data"
PREDICTIONS_FILE = DATA_DIR / "predictions.json"
RESULTS_FILE = DATA_DIR / "results.json"

SITE_PASSWORD = "pizzamello"
ADMIN_PASSWORD = "mello2026admin6887"

MEDAL = {0: "\U0001f947", 1: "\U0001f948", 2: "\U0001f949"}

# ---------------------------------------------------------------------------
# Scoring — adapted TopHeavyPositionalProximity for Mello top-5
# ---------------------------------------------------------------------------
WINNER_BONUS = 3
BASE_POINTS = 2

TOP3_PROXIMITY = {0: 15, 1: 12, 2: 9, 3: 6, 4: 4, 5: 2, 6: 1.5, 7: 0.75}
LOWER_PROXIMITY = {0: 10, 1: 8, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1, 7: 0.5}
OUTSIDE_TOP5_PROXIMITY = {1: 7, 2: 5, 3: 3, 4: 1.5, 5: 1, 6: 0.5, 7: 0.25}

MAX_DIFF = 7


def calculate_score(prediction: list[str], actual_results: list[str]) -> float:
    """Return total points for *prediction* given the full *actual_results*."""
    score = 0.0
    pos_map = {a.strip().lower(): i for i, a in enumerate(actual_results)}

    if (
        prediction
        and actual_results
        and prediction[0].strip().lower() == actual_results[0].strip().lower()
    ):
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


def get_breakdown(prediction: list[str], actual_results: list[str]) -> list[dict]:
    """Per-artist scoring breakdown."""
    pos_map = {a.strip().lower(): i for i, a in enumerate(actual_results)}
    rows: list[dict] = []

    for pred_pos, artist in enumerate(prediction):
        key = artist.strip().lower()
        row = {
            "pred_pos": pred_pos + 1,
            "artist": artist,
            "song": ARTIST_SONGS.get(artist, ""),
            "actual_pos": None,
            "diff": None,
            "points": 0.0,
            "details": [],
        }

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
                row["details"].append(
                    f"+{prox} (off by {diff}, finished {actual_pos + 1})"
                )
            else:
                row["details"].append(
                    f"0 pts (off by {diff}, finished {actual_pos + 1})"
                )

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

    winner = actual[0]
    top3 = actual[:3]
    top5 = actual[:5]

    _low = lambda s: s.strip().lower()

    winner_correct = sum(
        1
        for d in preds.values()
        if d["prediction"] and _low(d["prediction"][0]) == _low(winner)
    )

    perfect_top3 = sum(
        1
        for d in preds.values()
        if len(d["prediction"]) >= 3
        and all(_low(d["prediction"][i]) == _low(top3[i]) for i in range(3))
    )

    total_exact = 0
    for d in preds.values():
        for i, a in enumerate(d["prediction"]):
            if i < len(actual) and _low(a) == _low(actual[i]):
                total_exact += 1
    total_possible = total * 5
    accuracy_pct = (total_exact / total_possible * 100) if total_possible else 0

    # Most popular #1 pick
    winner_picks: dict[str, int] = {}
    for d in preds.values():
        if d["prediction"]:
            p = d["prediction"][0]
            winner_picks[p] = winner_picks.get(p, 0) + 1
    pop_winner = max(winner_picks, key=winner_picks.get) if winner_picks else None

    # Underdog champion — who predicted artists with the longest odds that
    # actually finished in the top 5?
    underdog_data: dict[str, dict] = {}
    for name, d in preds.items():
        total_odds = 0.0
        picks: list[str] = []
        for artist in d["prediction"]:
            if _low(artist) in [_low(a) for a in top5]:
                odds = BOOKMAKER_ODDS.get(artist, {}).get("avg_odds", 1)
                if odds >= 20:
                    total_odds += odds
                    picks.append(artist)
        underdog_data[name] = {"score": total_odds, "picks": picks}

    underdog_champ = (
        max(underdog_data, key=lambda x: underdog_data[x]["score"])
        if underdog_data
        else None
    )
    underdog_best = underdog_data.get(underdog_champ, {}) if underdog_champ else {}

    # Odds vs reality table
    odds_vs_reality = []
    for bm_rank, artist in enumerate(ODDS_RANKED):
        actual_rank = None
        for i, a in enumerate(actual):
            if _low(a) == _low(artist):
                actual_rank = i + 1
                break
        diff = abs((bm_rank + 1) - actual_rank) if actual_rank else None
        is_upset = (
            actual_rank is not None
            and actual_rank <= 5
            and (bm_rank + 1) > 5
        )
        odds_vs_reality.append(
            {
                "artist": artist,
                "bm_rank": bm_rank + 1,
                "actual_rank": actual_rank,
                "odds": BOOKMAKER_ODDS[artist]["avg_odds"],
                "win_pct": BOOKMAKER_ODDS[artist]["win_pct"],
                "diff": diff,
                "upset": is_upset,
            }
        )

    avg_score = 0.0
    max_score = 0.0
    if total:
        scores = [
            calculate_score(d["prediction"], actual) for d in preds.values()
        ]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)

    return {
        "total": total,
        "winner": winner,
        "top3": top3,
        "top5": top5,
        "winner_correct": winner_correct,
        "winner_pct": (winner_correct / total * 100) if total else 0,
        "perfect_top3": perfect_top3,
        "total_exact": total_exact,
        "accuracy_pct": accuracy_pct,
        "pop_winner": pop_winner,
        "pop_winner_count": winner_picks.get(pop_winner, 0) if pop_winner else 0,
        "underdog_champ": underdog_champ,
        "underdog_best": underdog_best,
        "odds_vs_reality": odds_vs_reality,
        "avg_score": avg_score,
        "max_score": max_score,
    }


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------
def _ensure_data():
    DATA_DIR.mkdir(exist_ok=True)
    if not PREDICTIONS_FILE.exists():
        PREDICTIONS_FILE.write_text("{}")
    if not RESULTS_FILE.exists():
        RESULTS_FILE.write_text(json.dumps({"results": [], "revealed": False}))


def load_predictions() -> dict:
    _ensure_data()
    return json.loads(PREDICTIONS_FILE.read_text())


def save_prediction(name: str, prediction: list[str]):
    _ensure_data()
    data = load_predictions()
    data[name] = {
        "prediction": prediction,
        "timestamp": datetime.now().isoformat(),
    }
    PREDICTIONS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_results() -> dict:
    _ensure_data()
    return json.loads(RESULTS_FILE.read_text())


def save_results(results: list[str], revealed: bool):
    _ensure_data()
    RESULTS_FILE.write_text(
        json.dumps(
            {"results": results, "revealed": revealed},
            indent=2,
            ensure_ascii=False,
        )
    )


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------
def _artist_card_html(photo: str, name: str, song: str, size: int = 72) -> str:
    return (
        f'<div class="artist-card">'
        f'<img src="{photo}" '
        f'style="width:{size}px;height:{size}px;border-radius:50%;'
        f'object-fit:cover" alt="{name}">'
        f'<div class="card-name">{name}</div>'
        f'<div class="card-song">&ldquo;{song}&rdquo;</div>'
        f"</div>"
    )


def _ranking_row_html(
    position: int, photo: str, name: str, song: str, extra: str = ""
) -> str:
    tier = {1: "gold", 2: "silver", 3: "bronze"}.get(position, "plain")
    return (
        f'<div class="mello-rank-row {tier}">'
        f'<div class="rank-num">{position}</div>'
        f'<img class="rank-photo" src="{photo}" alt="{name}">'
        f'<div class="rank-info">'
        f'<div class="rank-artist">{name}</div>'
        f'<div class="rank-song">&ldquo;{song}&rdquo;</div>'
        f"</div>"
        f"{extra}"
        f"</div>"
    )


def _stat_card_html(
    icon: str, title: str, big_value: str, subtitle: str, color: str = "#003DA5"
) -> str:
    return (
        f'<div class="stat-card">'
        f'<div style="font-size:2rem;margin-bottom:4px">{icon}</div>'
        f'<div style="font-size:.8rem;font-weight:600;color:#888;'
        f'text-transform:uppercase;letter-spacing:1px">{title}</div>'
        f'<div style="font-size:2.2rem;font-weight:900;color:{color};'
        f'margin:6px 0 2px">{big_value}</div>'
        f'<div style="font-size:.85rem;color:#555">{subtitle}</div>'
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --mello-blue: #003DA5;
            --mello-gold: #FECC02;
        }
        .mello-title {
            text-align: center;
            padding: 0.6rem 0 0.3rem;
        }
        .mello-title h1 {
            color: var(--mello-blue);
            font-size: 2.2rem;
            margin-bottom: 0;
        }
        .mello-title p {
            color: #555;
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }
        .contestant-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin: 0.8rem 0;
        }
        @media (max-width: 600px) {
            .contestant-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        .score-pill {
            display: inline-block;
            background: var(--mello-blue);
            color: white;
            border-radius: 1rem;
            padding: 2px 10px;
            font-weight: 700;
            font-size: 0.85rem;
            white-space: nowrap;
        }
        div[data-testid="stExpander"] summary span {
            font-size: 1.05rem;
        }
        /* Rank rows */
        .mello-rank-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            margin-bottom: 8px;
            border-radius: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,.06);
            color: #1a1a2e !important;
        }
        .mello-rank-row * { color: inherit; }
        .mello-rank-row .rank-num {
            font-size: 1.5rem;
            font-weight: 900;
            min-width: 28px;
            text-align: center;
        }
        .mello-rank-row .rank-photo {
            width: 48px; height: 48px;
            border-radius: 50%;
            object-fit: cover;
            flex-shrink: 0;
        }
        .mello-rank-row .rank-info { flex: 1; min-width: 0; }
        .mello-rank-row .rank-artist {
            font-weight: 700;
            font-size: .95rem;
            color: #1a1a2e !important;
        }
        .mello-rank-row .rank-song {
            font-size: .8rem;
            color: #555 !important;
            font-style: italic;
        }
        .mello-rank-row.gold   { background: linear-gradient(135deg,#fff9db,#ffeaa0); border: 2px solid #e6b800; }
        .mello-rank-row.gold   .rank-num { color: #b8860b !important; }
        .mello-rank-row.gold   .rank-photo { border: 2px solid #e6b800; }
        .mello-rank-row.silver { background: linear-gradient(135deg,#f4f6f8,#dde2ea); border: 2px solid #b8c0cc; }
        .mello-rank-row.silver .rank-num { color: #7a8799 !important; }
        .mello-rank-row.silver .rank-photo { border: 2px solid #b8c0cc; }
        .mello-rank-row.bronze { background: linear-gradient(135deg,#fff0e8,#ffd4b0); border: 2px solid #c8834a; }
        .mello-rank-row.bronze .rank-num { color: #a0522d !important; }
        .mello-rank-row.bronze .rank-photo { border: 2px solid #c8834a; }
        .mello-rank-row.plain  { background: #f0f2f8; border: 2px solid #dde3f0; }
        .mello-rank-row.plain  .rank-num { color: #003DA5 !important; }
        .mello-rank-row.plain  .rank-photo { border: 2px solid #dde3f0; }
        /* Artist cards */
        .artist-card {
            text-align: center;
            padding: 8px 4px;
            background: #f8f9ff;
            border-radius: 10px;
            border: 1px solid #e8ecf4;
        }
        .artist-card img {
            border: 3px solid #003DA5;
            box-shadow: 0 2px 8px rgba(0,0,0,.12);
        }
        .artist-card .card-name {
            margin-top: 6px;
            font-weight: 700;
            font-size: .82rem;
            line-height: 1.2;
            color: #1a1a2e !important;
        }
        .artist-card .card-song {
            font-size: .75rem;
            color: #555 !important;
            font-style: italic;
        }
        /* Stat cards */
        .stat-card {
            text-align: center;
            padding: 18px 12px;
            background: #f8f9ff;
            border: 1px solid #e0e4ef;
            border-radius: 14px;
            box-shadow: 0 1px 4px rgba(0,0,0,.05);
        }
        .stat-card * { color: inherit; }
        /* Odds table */
        .odds-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: .88rem;
            color: #1a1a2e !important;
        }
        .odds-table th {
            background: #003DA5;
            color: #fff !important;
            padding: 8px 10px;
            font-weight: 700;
            text-align: left;
            font-size: .78rem;
            text-transform: uppercase;
            letter-spacing: .5px;
        }
        .odds-table th:first-child { border-radius: 8px 0 0 0; }
        .odds-table th:last-child  { border-radius: 0 8px 0 0; }
        .odds-table td {
            padding: 7px 10px;
            border-bottom: 1px solid #e8ecf4;
            color: #1a1a2e !important;
        }
        .odds-table tr:last-child td:first-child { border-radius: 0 0 0 8px; }
        .odds-table tr:last-child td:last-child  { border-radius: 0 0 8px 0; }
        .odds-table tr:nth-child(even) td { background: #f5f6fb; }
        .odds-table .upset-row td { background: #fef9c3 !important; font-weight: 600; }
        .upset-badge {
            display: inline-block;
            background: #f59e0b;
            color: #fff !important;
            border-radius: 4px;
            padding: 1px 6px;
            font-size: .72rem;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Prediction tab
# ---------------------------------------------------------------------------
def render_prediction_tab():
    results_data = load_results()
    revealed = results_data.get("revealed", False)

    if revealed:
        st.info(
            "Predictions are closed - the results have been revealed! "
            "Head to the **Leaderboard** tab."
        )
        _render_check_own()
        return

    st.subheader("Submit your top 5")
    st.caption(
        "Pick the 5 artists you think will finish in the top 5, in order from "
        "1st to 5th."
    )

    with st.expander("View all 12 finalists", expanded=False):
        grid_html = '<div class="contestant-grid">'
        for c in CONTESTANTS:
            grid_html += _artist_card_html(c["photo"], c["artist"], c["song"])
        grid_html += "</div>"
        st.markdown(grid_html, unsafe_allow_html=True)

    with st.expander("\u2139\ufe0f How is the ranking calculated?", expanded=False):
        st.markdown(
            """
Your score is based on **how close** your predictions are to the actual
results - not just whether you guessed the right artists, but whether you
put them in the right positions.

**Base points**
- **+2 points** for every artist you pick that actually finishes in the
  top 5 (regardless of position).
- **+3 bonus** if you correctly predict the **winner** (1st place
  exactly right).

**Proximity points** - the closer your predicted position is to the
actual finish, the more points you earn:

| Predicted vs Actual | Top-3 artist | 4th–5th artist | Outside top 5 |
|---|---|---|---|
| Exact position | +15 | +10 | - |
| Off by 1 | +12 | +8 | +7 |
| Off by 2 | +9 | +6 | +5 |
| Off by 3 | +6 | +4 | +3 |
| Off by 4 | +4 | +3 | +1.5 |
| Off by 5 | +2 | +2 | +1 |
| Off by 6 | +1.5 | +1 | +0.5 |
| Off by 7 | +0.75 | +0.5 | +0.25 |

*"Outside top 5"* means you predicted an artist in your top 5 but they
finished 6th-12th - you can still earn proximity points if they weren't
too far off.

**Perfect score: 78 points** (all 5 exact + winner bonus).

*Inspired by the TopHeavyPositionalProximity scoring system.*
"""
        )

    name = st.text_input(
        "Your name", placeholder="Enter your name\u2026", key="pred_name"
    )

    predictions = load_predictions()
    if name and name.strip() in predictions:
        existing = predictions[name.strip()]["prediction"]
        st.warning(
            "You already have a prediction. Submitting again will overwrite it."
        )
        html = ""
        for i, a in enumerate(existing):
            html += _ranking_row_html(
                i + 1, ARTIST_PHOTOS.get(a, ""), a, ARTIST_SONGS.get(a, "")
            )
        st.markdown(html, unsafe_allow_html=True)
        st.divider()

    st.markdown("#### Build your ranking")

    labels = {
        0: "\U0001f947 1st place",
        1: "\U0001f948 2nd place",
        2: "\U0001f949 3rd place",
        3: "4th place",
        4: "5th place",
    }

    chosen: list[str | None] = []
    all_valid = True

    for pos in range(5):
        available = [a for a in ARTIST_NAMES if a not in chosen]
        col_sel, col_photo = st.columns([5, 1])
        with col_sel:
            pick = st.selectbox(
                labels[pos],
                options=["- select -"] + available,
                format_func=lambda x: (
                    f"{x}  -  \"{ARTIST_SONGS[x]}\"" if x in ARTIST_SONGS else x
                ),
                key=f"pick_{pos}",
            )
        with col_photo:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if pick != "- select -":
                st.image(ARTIST_PHOTOS.get(pick, ""), width=52)
        if pick == "- select -":
            all_valid = False
            chosen.append(None)
        else:
            chosen.append(pick)

    valid_picks = [c for c in chosen if c]
    if valid_picks:
        st.markdown("#### Your ranking preview")
        html = ""
        for i, a in enumerate(valid_picks):
            html += _ranking_row_html(
                i + 1, ARTIST_PHOTOS.get(a, ""), a, ARTIST_SONGS.get(a, "")
            )
        st.markdown(html, unsafe_allow_html=True)

    ok = all_valid and bool(name and name.strip())
    if st.button("Submit prediction", type="primary", disabled=not ok):
        save_prediction(name.strip(), valid_picks)
        st.success(f"Prediction saved for **{name.strip()}**!")
        st.balloons()

    st.divider()
    _render_check_own()


def _render_check_own():
    st.subheader("Check your prediction")
    check = st.text_input(
        "Enter your name to look up", placeholder="Your name\u2026", key="chk_name"
    )
    if not check:
        return
    preds = load_predictions()
    key = check.strip()
    if key not in preds:
        st.warning("No prediction found for that name.")
        return
    entry = preds[key]
    ts = entry.get("timestamp", "")[:16].replace("T", " ")
    st.caption(f"Submitted: {ts}")
    html = ""
    for i, a in enumerate(entry["prediction"]):
        html += _ranking_row_html(
            i + 1, ARTIST_PHOTOS.get(a, ""), a, ARTIST_SONGS.get(a, "")
        )
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Leaderboard tab
# ---------------------------------------------------------------------------
def render_leaderboard_tab():
    results_data = load_results()
    if not results_data.get("revealed", False):
        st.info(
            "The leaderboard will appear once the results are revealed. "
            "Stay tuned!"
        )
        return

    actual = results_data.get("results", [])
    if not actual:
        st.warning("No results available yet.")
        return

    # -- Actual top 5 --------------------------------------------------------
    st.subheader("Actual Top 5")
    html = ""
    for i, artist in enumerate(actual[:5]):
        html += _ranking_row_html(
            i + 1,
            ARTIST_PHOTOS.get(artist, ""),
            artist,
            ARTIST_SONGS.get(artist, ""),
        )
    st.markdown(html, unsafe_allow_html=True)

    st.caption(
        "Full result: "
        + " \u203a ".join(f"{i + 1}. {a}" for i, a in enumerate(actual))
    )

    preds = load_predictions()
    if not preds:
        st.warning("No predictions were submitted.")
        return

    # -- Statistics ----------------------------------------------------------
    stats = compute_stats(preds, actual)
    if stats:
        st.divider()
        _render_statistics(stats, preds, actual)

    # -- Leaderboard ---------------------------------------------------------
    st.divider()

    board = []
    for user, data in preds.items():
        pred = data["prediction"]
        score = calculate_score(pred, actual)
        board.append({"name": user, "score": score, "prediction": pred})

    board.sort(key=lambda x: (-x["score"], x["name"]))

    st.subheader("Leaderboard")
    for rank, entry in enumerate(board):
        m = MEDAL.get(rank, f"#{rank + 1}")
        label = f"{m}  **{entry['name']}** - {entry['score']:.1f} points"
        with st.expander(label, expanded=(rank == 0)):
            breakdown = get_breakdown(entry["prediction"], actual)
            for row in breakdown:
                photo = ARTIST_PHOTOS.get(row["artist"], "")
                if row["actual_pos"] is not None:
                    if row["diff"] == 0:
                        badge = (
                            '<span style="background:#16a34a;color:#fff;'
                            "border-radius:6px;padding:1px 8px;font-size:.8rem;"
                            f'font-weight:700">exact!</span>'
                        )
                    elif row["diff"] and row["diff"] <= 2:
                        badge = (
                            '<span style="background:#eab308;color:#fff;'
                            "border-radius:6px;padding:1px 8px;font-size:.8rem;"
                            f'font-weight:700">off by {row["diff"]}</span>'
                        )
                    else:
                        diff_val = row["diff"] if row["diff"] else "?"
                        badge = (
                            '<span style="background:#94a3b8;color:#fff;'
                            "border-radius:6px;padding:1px 8px;font-size:.8rem;"
                            f'font-weight:700">off by {diff_val}</span>'
                        )
                    pos_extra = (
                        f'<div style="text-align:right;min-width:90px">'
                        f'<div style="font-size:.75rem;color:#888">'
                        f'actual #{row["actual_pos"]}</div>'
                        f"{badge}"
                        f"</div>"
                    )
                else:
                    pos_extra = (
                        '<div style="text-align:right;min-width:90px">'
                        '<span style="color:#94a3b8;font-size:.8rem">not in top 12</span>'
                        "</div>"
                    )

                pts_html = (
                    f'<div style="text-align:right;min-width:50px">'
                    f'<span class="score-pill">{row["points"]:.1f}</span>'
                    f"</div>"
                )
                extra = pos_extra + pts_html

                st.markdown(
                    _ranking_row_html(
                        row["pred_pos"], photo, row["artist"], row["song"], extra
                    ),
                    unsafe_allow_html=True,
                )
                if row["details"]:
                    st.caption(
                        "\u00a0\u00a0\u00a0\u00a0"
                        + " | ".join(row["details"])
                    )


def _render_statistics(stats: dict, preds: dict, actual: list[str]):
    st.subheader("Statistics")

    # --- Row 1: three metric cards ------------------------------------------
    c1, c2, c3 = st.columns(3)

    with c1:
        winner = stats["winner"]
        n = stats["winner_correct"]
        t = stats["total"]
        pct = stats["winner_pct"]
        if pct >= 50:
            color = "#16a34a"
        elif pct >= 20:
            color = "#eab308"
        else:
            color = "#dc2626"
        st.markdown(
            _stat_card_html(
                "\U0001f3c6",
                "Predicted the winner",
                f"{n}/{t}",
                f"{pct:.0f}% picked {winner} as #1",
                color,
            ),
            unsafe_allow_html=True,
        )

    with c2:
        n3 = stats["perfect_top3"]
        if n3 > 0:
            color3 = "#16a34a"
            sub3 = "got the exact top 3!"
        else:
            color3 = "#dc2626"
            sub3 = "Nobody nailed the exact top 3"
        st.markdown(
            _stat_card_html(
                "\U0001f3af",
                "Perfect Top 3",
                str(n3),
                sub3,
                color3,
            ),
            unsafe_allow_html=True,
        )

    with c3:
        acc = stats["accuracy_pct"]
        if acc >= 40:
            color_a = "#16a34a"
        elif acc >= 20:
            color_a = "#eab308"
        else:
            color_a = "#dc2626"
        st.markdown(
            _stat_card_html(
                "\U0001f4ca",
                "Exact Position Hits",
                f"{stats['total_exact']}/{stats['total']*5}",
                f"{acc:.0f}% of all positions matched exactly",
                color_a,
            ),
            unsafe_allow_html=True,
        )

    st.write("")

    # --- Row 2: two more cards ----------------------------------------------
    c4, c5 = st.columns(2)

    with c4:
        pop = stats["pop_winner"]
        pop_n = stats["pop_winner_count"]
        if pop:
            pop_pct = pop_n / stats["total"] * 100
            st.markdown(
                _stat_card_html(
                    "\U0001f465",
                    "Most Popular #1 Pick",
                    pop,
                    f"Chosen by {pop_n}/{stats['total']} ({pop_pct:.0f}%)",
                    "#003DA5",
                ),
                unsafe_allow_html=True,
            )

    with c5:
        avg = stats["avg_score"]
        mx = stats["max_score"]
        st.markdown(
            _stat_card_html(
                "\U0001f4c8",
                "Average Score",
                f"{avg:.1f}",
                f"Top score: {mx:.1f} / 78 possible",
                "#003DA5",
            ),
            unsafe_allow_html=True,
        )

    st.write("")

    # --- Underdog champion --------------------------------------------------
    uc = stats.get("underdog_champ")
    ub = stats.get("underdog_best", {})
    if uc and ub.get("score", 0) > 0:
        st.markdown("#### \U0001f525 Underdog Champion")
        picks_str = ", ".join(ub.get("picks", []))
        st.markdown(
            f'<div class="stat-card" style="border-left:4px solid #f59e0b">'
            f'<div style="font-size:1.4rem;font-weight:800;color:#b45309">{uc}</div>'
            f'<div style="font-size:.9rem;color:#555;margin-top:4px">'
            f"Correctly predicted long-shot artists in the top 5:</div>"
            f'<div style="font-size:.95rem;font-weight:600;color:#1a1a2e;margin-top:6px">'
            f"{picks_str}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.write("")

    # --- Odds vs reality table ----------------------------------------------
    st.markdown("#### Bookmakers vs Reality")
    st.caption("How the pre-show favourites compared to the actual result.")

    rows_html = ""
    for r in stats["odds_vs_reality"]:
        cls = ' class="upset-row"' if r["upset"] else ""
        actual_str = f'#{r["actual_rank"]}' if r["actual_rank"] else "-"
        upset_tag = ' <span class="upset-badge">UPSET</span>' if r["upset"] else ""
        rows_html += (
            f"<tr{cls}>"
            f'<td>#{r["bm_rank"]}</td>'
            f"<td>{r['artist']}{upset_tag}</td>"
            f'<td style="text-align:center">{r["win_pct"]}%</td>'
            f'<td style="text-align:center">{r["odds"]:.1f}</td>'
            f'<td style="text-align:center;font-weight:700">{actual_str}</td>'
            f"</tr>"
        )

    st.markdown(
        '<table class="odds-table">'
        "<thead><tr>"
        "<th>Odds Rank</th>"
        "<th>Artist</th>"
        "<th>Win %</th>"
        "<th>Avg Odds</th>"
        "<th>Actual</th>"
        "</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Admin tab
# ---------------------------------------------------------------------------
def render_admin_tab():
    st.subheader("Admin Panel")

    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pwd = st.text_input("Password", type="password", key="admin_pwd")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Wrong password.")
        return

    st.success("Authenticated.")

    results_data = load_results()
    current_results = results_data.get("results", [])
    revealed = results_data.get("revealed", False)

    preds = load_predictions()
    st.subheader("Manage predictions")
    st.write(f"**Predictions received:** {len(preds)}")

    if preds:
        # Download as JSON
        preds_json = json.dumps(preds, indent=2, ensure_ascii=False)
        st.download_button(
            "Download predictions as JSON",
            data=preds_json,
            file_name="mello2026_predictions.json",
            mime="application/json",
        )

        # List with individual delete buttons
        for u in sorted(preds):
            col_name, col_del = st.columns([4, 1])
            with col_name:
                pred_list = ", ".join(preds[u]["prediction"])
                st.write(f"**{u}** - {pred_list}")
            with col_del:
                if st.button("\U0001f5d1", key=f"del_{u}", help=f"Delete {u}"):
                    data = load_predictions()
                    data.pop(u, None)
                    PREDICTIONS_FILE.write_text(
                        json.dumps(data, indent=2, ensure_ascii=False)
                    )
                    st.rerun()

        # Reset all
        st.write("")
        with st.expander("Danger zone", expanded=False):
            st.warning("This will permanently delete **all** predictions.")
            if st.button("Reset all predictions", type="primary", key="reset_all"):
                st.session_state._reset_confirm = True
            if st.session_state.get("_reset_confirm"):
                st.error("Are you sure? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Yes, delete everything", key="confirm_reset"):
                        PREDICTIONS_FILE.write_text("{}")
                        st.session_state._reset_confirm = False
                        st.success("All predictions have been reset.")
                        st.rerun()
                with c2:
                    if st.button("Cancel", key="cancel_reset"):
                        st.session_state._reset_confirm = False
                        st.rerun()
    else:
        st.caption("No predictions yet.")

    st.divider()

    st.subheader("Enter actual results")
    st.caption("Rank all 12 artists from 1st to 12th.")

    if current_results:
        st.write("**Current saved results:**")
        html = ""
        for i, a in enumerate(current_results):
            html += _ranking_row_html(
                i + 1, ARTIST_PHOTOS.get(a, ""), a, ARTIST_SONGS.get(a, "")
            )
        st.markdown(html, unsafe_allow_html=True)
        if not st.checkbox("Edit results", key="edit_res"):
            _render_reveal_toggle(current_results, revealed)
            return

    picks: list[str | None] = []
    valid = True
    for pos in range(12):
        available = [a for a in ARTIST_NAMES if a not in picks]
        pick = st.selectbox(
            f"Position {pos + 1}",
            options=["- select -"] + available,
            format_func=lambda x: (
                f"{x}  -  \"{ARTIST_SONGS[x]}\"" if x in ARTIST_SONGS else x
            ),
            key=f"res_{pos}",
        )
        if pick == "- select -":
            valid = False
            picks.append(None)
        else:
            picks.append(pick)

    if st.button("Save results", type="primary", disabled=not valid):
        clean = [p for p in picks if p]
        save_results(clean, revealed)
        st.success("Results saved!")
        st.rerun()

    st.divider()
    _render_reveal_toggle(current_results, revealed)


def _render_reveal_toggle(current_results: list[str], revealed: bool):
    st.subheader("Reveal leaderboard")
    if revealed:
        st.write("Leaderboard is currently **visible** to everyone.")
        if st.button("Hide leaderboard"):
            save_results(current_results, False)
            st.rerun()
    else:
        st.write("Leaderboard is currently **hidden**.")
        if st.button("Reveal leaderboard", type="primary"):
            if not current_results:
                st.error("Save the actual results first.")
            else:
                save_results(current_results, True)
                st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    _ensure_data()
    inject_css()

    # -- Site-wide password gate ---------------------------------------------
    if "site_auth" not in st.session_state:
        st.session_state.site_auth = False

    if not st.session_state.site_auth:
        st.markdown(
            '<div class="mello-title">'
            "<h1>\U0001f1f8\U0001f1ea Melodifestivalen 2026</h1>"
            "<p>Prediction Game \u00b7 Saturday 7 March \u00b7 Strawberry Arena, Stockholm</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.write("")
        pwd = st.text_input(
            "Enter the password to access the site",
            type="password",
            key="site_pwd",
        )
        if st.button("Enter", type="primary"):
            if pwd == SITE_PASSWORD:
                st.session_state.site_auth = True
                st.rerun()
            else:
                st.error("Wrong password.")
        return

    # -- Authenticated -------------------------------------------------------
    st.markdown(
        '<div class="mello-title">'
        "<h1>\U0001f1f8\U0001f1ea Melodifestivalen 2026</h1>"
        "<p>Prediction Game \u00b7 Saturday 7 March \u00b7 Strawberry Arena, Stockholm</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    tab_predict, tab_board, tab_admin = st.tabs(
        ["\U0001f3a4 Predict", "\U0001f3c6 Leaderboard", "\u2699\ufe0f Admin"]
    )

    with tab_predict:
        render_prediction_tab()
    with tab_board:
        render_leaderboard_tab()
    with tab_admin:
        render_admin_tab()


if __name__ == "__main__":
    main()
