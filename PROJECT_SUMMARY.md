# FIFA World Cup 2026 — Project Summary

## Project Goal

Build a complete data science notebook that:
1. Explores and tells the story of World Cup history through EDA
2. Trains an ML model to predict which teams will advance deep into the 2026 tournament
3. Simulates the full 2026 bracket match-by-match to produce a predicted champion

The notebook is structured as: **EDA → Feature Engineering → Modeling → Simulation → Predictions**

---

## Datasets (all in `DataSets_Clean/`)

| File | Rows | Purpose |
|---|---|---|
| `teams_combined.csv` | 240 | Core ML dataset — 192 labeled historical rows (2002–2022) + 48 unlabeled 2026 teams |
| `results_clean.csv` | 49,477 | All international matches 1872–2026 — form features + match simulator training |
| `goalscorers_clean.csv` | 47,767 | Individual goals — EDA/storytelling only |
| `shootouts_clean.csv` | 678 | Penalty shootout history — feature enrichment + knockout simulator |
| `fifa_ranking_clean.csv` | 67,472 | FIFA rankings 1992–2024 — EDA + rank validation |
| `world_cup_matches_clean.csv` | 900 | WC match results 1930–2018 — EDA + head-to-head history |
| `world_cups_clean.csv` | 21 | WC tournament summaries 1930–2022 — EDA/storytelling |
| `international_matches_clean.csv` | 17,769 | Matches with home stadium flag — home advantage analysis |
| `former_names.csv` | 36 | Country name changes reference |
| `final_teams.csv` | 240 | teams_combined + 9 engineered features — primary ML input |
| `final_matches.csv` | 17,494 | Competitive matches 1993–2026 with pre-match rankings — match simulator training |
| `wc_history.csv` | 489 | Per-team per-edition WC stats 1930–2022 — EDA/storytelling |
| `groups_2026.csv` | 48 | 2026 group assignments (A–L) — simulation bracket |
| `standings_2026.csv` | 48 | Live 2026 group standings from completed matches — simulation starting state |

### Key facts about `teams_combined.csv`

- **Target columns (4):** `winner`, `finalist`, `semi_finalist`, `quarter_finalist` — binary, hierarchical (winner is also finalist, etc.)
- **Feature columns (20):** form stats, historical WC stats, squad quality, FIFA ranking
- **2026 test set:** 48 teams, target columns empty (to predict)
- **Train split:** 6 WCs × 32 teams = 192 rows covering 2002, 2006, 2010, 2014, 2018, 2022

### Feature columns explained

| Column | Description |
|---|---|
| `version` | World Cup year |
| `team` | Team name |
| `continent` | Confederation |
| `is_host` | 1 if hosting nation |
| `goals_scored_last_4y` | Goals scored in all internationals in prior 4 years |
| `goals_received_last_4y` | Goals conceded in prior 4 years |
| `wins_last_4y` | Wins in prior 4 years |
| `losses_last_4y` | Losses in prior 4 years |
| `draws_last_4y` | Draws in prior 4 years |
| `world_cup_titles_before` | Number of WC titles before this tournament |
| `squad_total_market_value_eur` | Total squad market value in EUR (Transfermarkt) |
| `fifa_rank_pre_tournament` | FIFA rank just before the tournament |
| `fifa_points_pre_tournament` | FIFA points just before the tournament |
| `squad_avg_age` | Average squad age |
| `world_cup_participations_before` | Number of WC appearances before this edition |
| `groups_passed_before` | Times advanced past group stage historically |
| `round16_before` | Times reached Round of 16 historically |
| `quarterfinals_before` | Times reached Quarter-finals historically |
| `semifinals_before` | Times reached Semi-finals historically |
| `finals_before` | Times reached the Final historically |

---

## Step-by-Step Plan

### DONE — Data Engineering
- [x] Step 1: Moved all source files into `DataSets/`
- [x] Step 2: Full audit of all 13 datasets (shapes, nulls, date ranges, name mismatches)
- [x] Step 3: Fixed all data quality issues:
  - 2014 historical WC stats (all-zeros bug) — recomputed from `world_cup_matches_clean.csv`
  - 2002 missing market values — imputed with continent medians
  - Name normalization: China PR→China, Serbia and Montenegro→Serbia (via `former_names.csv`)
  - Encoding fix: Curaçao across all files
  - FIFA ranking name mapping: IR Iran→Iran, Korea Republic→South Korea, Côte d'Ivoire→Ivory Coast, Czechia→Czech Republic, Congo DR→DR Congo, Cabo Verde→Cape Verde, USA→United States
  - Merged `train_fixed.csv` + `test_fixed.csv` → `teams_combined.csv`
- [x] All 9 clean files saved to `DataSets_Clean/`

---

### DONE — Feature Engineering (Step 4)

Enrich `teams_combined.csv` with new features computed from `results_clean.csv` and `shootouts_clean.csv`.

- [x] `shootout_wins_before`, `shootout_losses_before`, `shootout_win_rate`
- [x] `goal_difference_last_4y`, `win_rate_last_4y`, `clean_sheets_last_4y`
- [x] `tournament_win_rate_last_4y`, `goals_scored_last_2y`, `wins_last_2y`

**Output:** `DataSets_Clean/final_teams.csv` — (240, 33), zero feature nulls

---

### DONE — Match Simulator Dataset (Step 5)

- [x] Filtered to competitive matches 1993+ (dropped friendlies, pre-ranking era)
- [x] As-of join with FIFA ranking via `pd.merge_asof` — pre-match rank for both teams
- [x] Added: `rank_diff`, `points_diff`, `is_neutral`, `goal_diff`, `outcome`, `outcome_code`
- [x] Tournament tier: T1=WC (6,801 matches), T2=continental (8,176), T3=other (2,517)

**Output:** `DataSets_Clean/final_matches.csv` — (17,494, 17), zero nulls

Outcome distribution: H=48.5%, D=22.4%, A=29.1%

---

### DONE — WC History + 2026 Structure (Step 6)

- [x] `wc_history.csv` (489, 8) — per team per WC edition 1930-2022: stage reached, goals, matches
- [x] `groups_2026.csv` (48, 2) — 2026 group assignments A-L (4 teams each), derived from match data
- [x] `standings_2026.csv` (48, 10) — live group standings computed from completed matches

---

### TODO — EDA Section (Notebook)

Charts and insights to build:
- Goals scored per WC over time (from `world_cups_clean`)
- Top scorers of all time (from `goalscorers_clean`)
- WC winners by continent/era
- Home advantage quantification (from `international_matches_clean`)
- FIFA rank vs. actual result correlation
- Biggest upsets in WC history (low-ranked team beats high-ranked)
- 2026 team profiles: radar charts of key features

---

### TODO — ML Modeling Section (Notebook)

**Model type:** Multi-label classification (predict 4 binary targets simultaneously)

**Approach options (ranked by suitability):**
1. Random Forest / XGBoost — handles small dataset well, interpretable feature importance
2. Logistic Regression per target — simple baseline
3. Neural network — probably overkill for 192 training rows

**Key challenge:** Only 192 training rows (6 WCs × 32 teams). Use cross-validation carefully — leave-one-WC-out is the correct strategy (train on 5 WCs, validate on 1).

**Steps:**
- Encode categorical features (`continent`)
- Scale numerical features
- Handle class imbalance (very few winners/finalists vs. group-stage exits)
- Train model, evaluate with ROC-AUC per target
- Generate predictions for all 48 test teams

---

### TODO — Tournament Simulation Section (Notebook)

**2026 format (48 teams):**
- 12 groups of 4 teams → top 2 per group (24) + 8 best 3rd-place = 32 teams advance
- Round of 32 → Round of 16 → Quarter-finals → Semi-finals → Final
- Group stage: 72 matches total (12 × 6)

**Simulation approach:**
- Train a match-outcome model on `final_matches.csv`
- For each match, predict win probability for each team
- Run N Monte Carlo simulations of the full bracket
- Report: probability each team wins the tournament / reaches each stage

**Shootout tie-breaking:** use `shootout_win_rate` from Step 4

---

## Important Technical Notes

- **2026 FIFA ranks in `teams_combined`** come from a 2026 pre-tournament snapshot (more recent than our `fifa_ranking_clean.csv` which ends June 2024). Do NOT overwrite them with the ranking file.
- **Leave-one-WC-out CV** is mandatory — using random train/test split would cause data leakage since teams appear in multiple WCs.
- **Class imbalance:** Only 6 winners, 12 finalists, 24 semi-finalists in 192 rows. Use `class_weight='balanced'` or SMOTE.
- **2026 is 48 teams vs 32** — the quarter-finalist rate changes from 25% to 17%. Account for this in predictions.
- **Norway and Curaçao** have zero shootout history — they get `shootout_win_rate = 0`.

---

## File Structure

```
wc/
├── DataSets/               # Original raw files (keep for reference)
├── DataSets_Clean/         # Clean files — use only these in the notebook
│   ├── teams_combined.csv
│   ├── results_clean.csv
│   ├── goalscorers_clean.csv
│   ├── shootouts_clean.csv
│   ├── fifa_ranking_clean.csv
│   ├── world_cup_matches_clean.csv
│   ├── world_cups_clean.csv
│   ├── international_matches_clean.csv
│   └── former_names.csv
├── fix_datasets.py           # Step 3: fix train/test source files
├── build_clean_datasets.py   # Step 3: builds DataSets_Clean/ from raw files
├── feature_engineering.py    # Step 4: builds final_teams.csv (240×33)
├── build_final_matches.py    # Step 5: builds final_matches.csv (17494×17)
├── build_step6.py            # Step 6: builds wc_history, groups_2026, standings_2026
├── fifa-world-cup-2026.ipynb  # Main notebook
└── PROJECT_SUMMARY.md        # This file
```
