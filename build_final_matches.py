"""
Step 5 — Match Simulator Dataset
Build DataSets_Clean/final_matches.csv from results_clean.csv + fifa_ranking_clean.csv.
Each row is one match with pre-match FIFA ranking features for both teams.
"""
import pandas as pd

CLEAN = r'C:\Users\Mon Pc\Desktop\wc\DataSets_Clean'

# Same name map used across all scripts
NAME_MAP = {
    'IR Iran': 'Iran',
    'Korea Republic': 'South Korea',
    "Côte d'Ivoire": 'Ivory Coast',
    'Czechia': 'Czech Republic',
    'Congo DR': 'DR Congo',
    'Cabo Verde': 'Cape Verde',
    'USA': 'United States',
    'Curacao': 'Curaçao',
}

# ── LOAD ──────────────────────────────────────────────────────────────────────
results = pd.read_csv(f'{CLEAN}/results_clean.csv', parse_dates=['date'])
ranking = pd.read_csv(f'{CLEAN}/fifa_ranking_clean.csv', parse_dates=['rank_date'])

# Normalise ranking country names
ranking['country_full'] = ranking['country_full'].replace(NAME_MAP)

# ── FILTER RESULTS ─────────────────────────────────────────────────────────────
# Drop future / unplayed matches (null scores)
results = results[results['home_score'].notna() & results['away_score'].notna()].copy()
results['home_score'] = results['home_score'].astype(int)
results['away_score'] = results['away_score'].astype(int)

# Rankings start 1992-12-31 — only keep matches from 1993 onward
results = results[results['date'] >= '1993-01-01']

# Drop pure friendlies (low signal for tournament prediction)
results = results[results['tournament'] != 'Friendly'].copy()

print(f'Competitive matches 1993+: {len(results)}')

# ── TOURNAMENT TIER ─────────────────────────────────────────────────────────────
# Tier 1 = World Cup (highest stakes)
# Tier 2 = continental finals / qualifiers / nations leagues
# Tier 3 = everything else competitive (regional cups, invitational tournaments)
TIER1_KEYWORDS = ['FIFA World Cup']
TIER2_KEYWORDS = [
    'Copa América', 'UEFA Euro', 'AFC Asian Cup', 'African Cup of Nations',
    'CONCACAF Gold Cup', 'Gold Cup', 'Nations League', 'Confederations Cup',
    'Olympic', 'CONMEBOL', 'CONCACAF Nations', 'CAF', 'AFF',
]

def tier(t):
    if any(k in t for k in TIER1_KEYWORDS):
        return 1
    if any(k in t for k in TIER2_KEYWORDS):
        return 2
    return 3

results['tournament_tier'] = results['tournament'].apply(tier)
print('Tournament tier breakdown:')
print(results['tournament_tier'].value_counts().sort_index().to_dict())

# ── AS-OF JOIN: FIFA RANKING ───────────────────────────────────────────────────
# For each match, attach the most recent published ranking for each team
# before the match date using pandas merge_asof (sorted by date, grouped by team).

results = results.sort_values('date').reset_index(drop=True)
ranking = ranking.sort_values('rank_date')

rank_cols = ['rank_date', 'country_full', 'rank', 'total_points']

home_rank = ranking[rank_cols].rename(columns={
    'country_full': 'home_team',
    'rank':         'home_rank',
    'total_points': 'home_points',
})
away_rank = ranking[rank_cols].rename(columns={
    'country_full': 'away_team',
    'rank':         'away_rank',
    'total_points': 'away_points',
})

matches = pd.merge_asof(
    results, home_rank,
    left_on='date', right_on='rank_date',
    by='home_team', direction='backward',
)
matches = pd.merge_asof(
    matches, away_rank,
    left_on='date', right_on='rank_date',
    by='away_team', direction='backward',
)

# ── DROP ROWS WITH NO RANKING DATA ────────────────────────────────────────────
before = len(matches)
matches = matches.dropna(subset=['home_rank', 'away_rank']).copy()
dropped = before - len(matches)
print(f'\nDropped {dropped} rows ({100*dropped/before:.1f}%) — ranking not available for one or both teams')
print(f'Kept {len(matches)} rows')

# ── DERIVED FEATURES ──────────────────────────────────────────────────────────
matches['home_rank']    = matches['home_rank'].astype(int)
matches['away_rank']    = matches['away_rank'].astype(int)
matches['home_points']  = matches['home_points'].round(2)
matches['away_points']  = matches['away_points'].round(2)

# rank_diff > 0  means home team is ranked LOWER (worse) than away team
matches['rank_diff']    = matches['home_rank']   - matches['away_rank']
matches['points_diff']  = matches['home_points'] - matches['away_points']
matches['is_neutral']   = matches['neutral'].astype(int)
matches['goal_diff']    = matches['home_score']  - matches['away_score']
matches['outcome']      = matches['goal_diff'].apply(
    lambda x: 'H' if x > 0 else ('D' if x == 0 else 'A')
)
matches['outcome_code'] = matches['outcome'].map({'H': 0, 'D': 1, 'A': 2})

# ── SELECT & SAVE ──────────────────────────────────────────────────────────────
COLS = [
    'date', 'home_team', 'away_team',
    'tournament', 'tournament_tier',
    'home_score', 'away_score', 'goal_diff',
    'outcome', 'outcome_code',
    'is_neutral',
    'home_rank', 'home_points',
    'away_rank', 'away_points',
    'rank_diff', 'points_diff',
]
final = matches[COLS].copy()
final.to_csv(f'{CLEAN}/final_matches.csv', index=False, encoding='utf-8')

# ── VALIDATION ────────────────────────────────────────────────────────────────
print('\n=== Validation ===')
print(f'Shape: {final.shape}')
print(f'Date range: {final["date"].min().date()} - {final["date"].max().date()}')
print(f'Nulls: {final.isnull().sum()[final.isnull().sum()>0].to_dict()}')

print('\n--- Outcome distribution ---')
print(final['outcome'].value_counts().to_dict())

print('\n--- By tournament tier ---')
print(final.groupby('tournament_tier')[['date']].count().rename(columns={'date':'matches'}).to_string())

print('\n--- Neutral vs non-neutral ---')
print(final['is_neutral'].value_counts().rename({0:'home venue', 1:'neutral'}).to_dict())

print('\n--- Rank diff sanity check (World Cup finals only) ---')
wc = final[final['tournament'] == 'FIFA World Cup'].copy()
print(f'WC matches: {len(wc)}')
print(f'Home win rate in WC (neutral=1 usually): {(wc["outcome"]=="H").mean():.3f}')
print(f'Draw rate: {(wc["outcome"]=="D").mean():.3f}')
print(f'Away win rate: {(wc["outcome"]=="A").mean():.3f}')

print('\n--- Sample: recent World Cup matches ---')
sample = final[final['tournament']=='FIFA World Cup'].tail(10)
print(sample[['date','home_team','away_team','home_score','away_score','home_rank','away_rank','rank_diff']].to_string(index=False))

print('\n[OK] final_matches.csv saved.')
