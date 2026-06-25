"""
Step 4 — Feature Engineering
Enriches teams_combined.csv with new features from results_clean.csv
and shootouts_clean.csv. Outputs DataSets_Clean/final_teams.csv.
"""
import pandas as pd
import numpy as np

CLEAN = r'C:\Users\Mon Pc\Desktop\wc\DataSets_Clean'

# ── LOAD ──────────────────────────────────────────────────────────────────────
teams     = pd.read_csv(f'{CLEAN}/teams_combined.csv')
results   = pd.read_csv(f'{CLEAN}/results_clean.csv', parse_dates=['date'])
shootouts = pd.read_csv(f'{CLEAN}/shootouts_clean.csv', parse_dates=['date'])

# Drop future unplayed matches (NA scores)
results = results[results['home_score'].notna() & results['away_score'].notna()].copy()
results['home_score'] = results['home_score'].astype(int)
results['away_score'] = results['away_score'].astype(int)

# ── WC TOURNAMENT START DATES ─────────────────────────────────────────────────
WC_START = {
    2002: pd.Timestamp('2002-05-31'),
    2006: pd.Timestamp('2006-06-09'),
    2010: pd.Timestamp('2010-06-11'),
    2014: pd.Timestamp('2014-06-12'),
    2018: pd.Timestamp('2018-06-14'),
    2022: pd.Timestamp('2022-11-20'),
    2026: pd.Timestamp('2026-06-11'),
}

# ── BUILD TEAM-LEVEL MATCH TABLE ──────────────────────────────────────────────
# Convert results into one row per team per match
home = results[['date','home_team','home_score','away_score','tournament']].copy()
home.columns = ['date','team','goals_scored','goals_conceded','tournament']

away = results[['date','away_team','away_score','home_score','tournament']].copy()
away.columns = ['date','team','goals_scored','goals_conceded','tournament']

matches = pd.concat([home, away], ignore_index=True)
matches['win']          = matches['goals_scored'] > matches['goals_conceded']
matches['draw']         = matches['goals_scored'] == matches['goals_conceded']
matches['loss']         = matches['goals_scored'] < matches['goals_conceded']
matches['clean_sheet']  = matches['goals_conceded'] == 0
matches['competitive']  = matches['tournament'] != 'Friendly'

# Pre-sort for slicing efficiency
matches = matches.sort_values('date').reset_index(drop=True)

# ── FEATURE COMPUTATION HELPERS ───────────────────────────────────────────────
def form_features(team, end_date, years):
    """Compute form stats for a team in the N years before end_date."""
    start = end_date - pd.DateOffset(years=years)
    mask  = (matches['team'] == team) & (matches['date'] >= start) & (matches['date'] < end_date)
    df    = matches[mask]
    n     = len(df)
    if n == 0:
        return {'gs': 0, 'gc': 0, 'w': 0, 'd': 0, 'l': 0, 'cs': 0, 'n': 0, 'w_comp': 0, 'n_comp': 0}
    comp  = df[df['competitive']]
    return {
        'gs':     int(df['goals_scored'].sum()),
        'gc':     int(df['goals_conceded'].sum()),
        'w':      int(df['win'].sum()),
        'd':      int(df['draw'].sum()),
        'l':      int(df['loss'].sum()),
        'cs':     int(df['clean_sheet'].sum()),
        'n':      n,
        'w_comp': int(comp['win'].sum()),
        'n_comp': len(comp),
    }

def shootout_features(team, before_year):
    """Compute shootout stats for a team before a given WC year."""
    mask  = (shootouts['date'].dt.year < before_year) & \
            ((shootouts['home_team'] == team) | (shootouts['away_team'] == team))
    df    = shootouts[mask]
    total = len(df)
    wins  = int((df['winner'] == team).sum())
    losses = total - wins
    return {
        'shootout_wins_before':   wins,
        'shootout_losses_before': losses,
        'shootout_win_rate':      round(wins / total, 4) if total > 0 else 0.0,
    }

# ── COMPUTE ALL FEATURES ──────────────────────────────────────────────────────
print('Computing features for', len(teams), 'rows...')
rows = []
for i, row in teams.iterrows():
    team     = row['team']
    year     = row['version']
    wc_start = WC_START[year]

    f4  = form_features(team, wc_start, years=4)
    f2  = form_features(team, wc_start, years=2)
    sh  = shootout_features(team, year)

    rows.append({
        # Derived directly from existing columns (fast cross-check)
        'goal_difference_last_4y':      row['goals_scored_last_4y'] - row['goals_received_last_4y'],
        'win_rate_last_4y':             round(row['wins_last_4y'] / max(row['wins_last_4y'] + row['losses_last_4y'] + row['draws_last_4y'], 1), 4),
        # Computed from results_clean (requires raw data)
        'clean_sheets_last_4y':         f4['cs'],
        'tournament_win_rate_last_4y':  round(f4['w_comp'] / f4['n_comp'], 4) if f4['n_comp'] > 0 else 0.0,
        'goals_scored_last_2y':         f2['gs'],
        'wins_last_2y':                 f2['w'],
        # Shootout stats
        **sh,
    })
    if (i + 1) % 50 == 0:
        print(f'  {i+1}/{len(teams)} done')

print(f'  {len(teams)}/{len(teams)} done')

# ── ASSEMBLE & SAVE ───────────────────────────────────────────────────────────
new_cols    = pd.DataFrame(rows)
final_teams = pd.concat([teams.reset_index(drop=True), new_cols], axis=1)
final_teams.to_csv(f'{CLEAN}/final_teams.csv', index=False, encoding='utf-8')

# ── VALIDATION REPORT ─────────────────────────────────────────────────────────
print('\n=== Validation ===')
print(f'Shape: {final_teams.shape}')
print(f'New columns: {list(new_cols.columns)}')
print(f'Nulls: {final_teams.isnull().sum()[final_teams.isnull().sum()>0].to_dict()}')

print('\n--- Sample: 2022 finalists ---')
cols = ['team','version','goal_difference_last_4y','win_rate_last_4y',
        'clean_sheets_last_4y','tournament_win_rate_last_4y',
        'goals_scored_last_2y','wins_last_2y',
        'shootout_wins_before','shootout_win_rate']
sample = final_teams[final_teams['version']==2022].sort_values('fifa_rank_pre_tournament').head(8)
print(sample[cols].to_string(index=False))

print('\n--- 2026 sample (top 8 by rank) ---')
t26 = final_teams[final_teams['version']==2026].sort_values('fifa_rank_pre_tournament').head(8)
print(t26[cols].to_string(index=False))

print('\n--- Shootout stats: teams with history ---')
sh_sample = final_teams[(final_teams['version']==2026) & (final_teams['shootout_wins_before']>0)]
print(sh_sample[['team','shootout_wins_before','shootout_losses_before','shootout_win_rate']].sort_values('shootout_wins_before', ascending=False).head(10).to_string(index=False))
