"""
Step 6 — WC History + 2026 Group Structure
Builds:
  - DataSets_Clean/wc_history.csv      : per-team per-edition WC stats (EDA)
  - DataSets_Clean/groups_2026.csv     : 2026 group assignments (A-L, 4 teams each)
  - DataSets_Clean/standings_2026.csv  : live group standings from completed matches
"""
import pandas as pd
import string
from collections import defaultdict

CLEAN = r'C:\Users\Mon Pc\Desktop\wc\DataSets_Clean'

NAME_MAP = {
    'IR Iran':          'Iran',
    'Korea Republic':   'South Korea',
    "Côte d'Ivoire":    'Ivory Coast',
    'Czechia':          'Czech Republic',
    'Congo DR':         'DR Congo',
    'Cabo Verde':       'Cape Verde',
    'USA':              'United States',
    'Curacao':          'Curaçao',
    # Historical WC names
    'Germany FR':       'Germany',
    'West Germany':     'Germany',
    'Soviet Union':     'Russia',     # closest modern equivalent for EDA labels
    'Czechoslovakia':   'Czech Republic',
    'Yugoslavia':       'Yugoslavia', # keep as-is (no modern single successor)
    'Dutch East Indies':'Indonesia',
    'Turkey':           'Turkey',
}

# ── 1. WC HISTORY (1930-2022) ─────────────────────────────────────────────────

# Stage rank: higher = further into the tournament
STAGE_RANK = {
    'First round':         0,
    'Group stage':         0,
    'First group stage':   0,
    'Second group stage':  1,  # 1974-1982 second group round
    'Final round':         1,  # 1950 deciding group (4 teams — treated like R16)
    'Round of 16':         1,
    'Quarter-finals':      2,
    'Semi-finals':         3,
    'Third place':         4,  # refined below to 3rd or 4th
    'Final':               5,  # refined below to winner or finalist
}

STAGE_LABEL = {0: 'group_stage', 1: 'round_of_16', 2: 'quarter_finals',
               3: 'semi_finals', 4: 'fourth_place', 5: 'third_place',
               6: 'finalist', 7: 'winner'}

wc_matches = pd.read_csv(f'{CLEAN}/world_cup_matches_clean.csv')
wc_summary = pd.read_csv(f'{CLEAN}/world_cups_clean.csv')

# Normalise column names
wc_matches.columns = [c.lower().replace(' ', '_') for c in wc_matches.columns]

def norm(name):
    name = str(name).strip()
    return NAME_MAP.get(name, name)

records = {}

def update(key, gf, ga, stage_r):
    if key not in records:
        records[key] = {'year': key[0], 'team': key[1],
                        'goals_for': 0, 'goals_against': 0,
                        'matches': 0, 'max_stage': 0}
    records[key]['goals_for']     += gf
    records[key]['goals_against'] += ga
    records[key]['matches']       += 1
    records[key]['max_stage']      = max(records[key]['max_stage'], stage_r)

for _, row in wc_matches.iterrows():
    year = int(row['year'])
    s    = STAGE_RANK.get(row['stage'], 0)
    ht   = norm(row['home_team'])
    at   = norm(row['away_team'])
    hg, ag = int(row['home_goals']), int(row['away_goals'])
    update((year, ht), hg, ag, s)
    update((year, at), ag, hg, s)

# 2022 WC (not in world_cup_matches_clean — use results_clean)
results = pd.read_csv(f'{CLEAN}/results_clean.csv', parse_dates=['date'])
wc22 = results[(results['date'].dt.year == 2022) &
               (results['tournament'] == 'FIFA World Cup') &
               results['home_score'].notna()].copy()
wc22['home_score'] = wc22['home_score'].astype(int)
wc22['away_score'] = wc22['away_score'].astype(int)

def stage_2022(d):
    if d.date() <= pd.Timestamp('2022-12-02').date(): return 0   # group
    elif d.date() <= pd.Timestamp('2022-12-06').date(): return 1  # R16
    elif d.date() <= pd.Timestamp('2022-12-10').date(): return 2  # QF
    elif d.date() <= pd.Timestamp('2022-12-14').date(): return 3  # SF
    elif d.date() <= pd.Timestamp('2022-12-17').date(): return 4  # 3rd place
    else: return 5                                                  # Final

for _, row in wc22.iterrows():
    s = stage_2022(row['date'])
    ht, at = norm(row['home_team']), norm(row['away_team'])
    hg, ag = row['home_score'], row['away_score']
    update((2022, ht), hg, ag, s)
    update((2022, at), ag, hg, s)

# Refine winner / finalist / 3rd / 4th using world_cups_clean
# 2022 is not in world_cups_clean so we hardcode it
WC_TOP4 = {}
for _, ws in wc_summary.iterrows():
    year = int(ws['Year'])
    WC_TOP4[year] = {
        'winner':   norm(ws['Winner']),
        'finalist': norm(ws['Runners-Up']),
        'third':    norm(ws['Third']),
        'fourth':   norm(ws['Fourth']),
    }

# Add 2022 manually (Argentina won on pens vs France; Croatia 3rd, Morocco 4th)
WC_TOP4[2022] = {'winner': 'Argentina', 'finalist': 'France',
                 'third': 'Croatia',    'fourth': 'Morocco'}

for year, top4 in WC_TOP4.items():
    for team, stage in [(top4['winner'], 7), (top4['finalist'], 6),
                        (top4['third'],  5), (top4['fourth'],  4)]:
        # Match by year and normalised name (case-insensitive fallback)
        key = (year, team)
        if key in records:
            records[key]['max_stage'] = max(records[key]['max_stage'], stage)
        else:
            # Try case-insensitive match for old team names
            for k in records:
                if k[0] == year and k[1].lower() == team.lower():
                    records[k]['max_stage'] = max(records[k]['max_stage'], stage)
                    break

# Assemble
df_hist = pd.DataFrame(list(records.values()))
df_hist['stage_num'] = df_hist['max_stage']
df_hist['stage']     = df_hist['max_stage'].map(STAGE_LABEL)
df_hist['goal_diff'] = df_hist['goals_for'] - df_hist['goals_against']
df_hist = df_hist[['year', 'team', 'stage', 'stage_num',
                   'goals_for', 'goals_against', 'goal_diff', 'matches']].copy()
df_hist = df_hist.sort_values(['year', 'stage_num'],
                               ascending=[True, False]).reset_index(drop=True)

df_hist.to_csv(f'{CLEAN}/wc_history.csv', index=False, encoding='utf-8')
print(f'[OK] wc_history.csv  — {df_hist.shape}')
print('Stage distribution:')
print(df_hist['stage'].value_counts().sort_index().to_dict())

print('\nSample top performers:')
print(df_hist[df_hist['stage'] == 'winner'][['year','team','goals_for','goals_against','matches']].to_string(index=False))

# ── 2. GROUPS_2026 ─────────────────────────────────────────────────────────────

wc26 = results[(results['date'].dt.year == 2026) &
               (results['tournament'] == 'FIFA World Cup')].copy()

# All June 2026 WC matches are group stage (knockouts start in July)
# Use graph connected components to find each group of 4
adj = defaultdict(set)
for _, row in wc26.iterrows():
    h, a = norm(row['home_team']), norm(row['away_team'])
    adj[h].add(a)
    adj[a].add(h)

visited = set()
group_list = []
for team in sorted(adj.keys()):
    if team not in visited:
        comp = set()
        queue = [team]
        while queue:
            t = queue.pop()
            if t not in visited:
                visited.add(t)
                comp.add(t)
                queue.extend(adj[t] - visited)
        group_list.append(sorted(comp))

# Sort groups by earliest match date in each group
def earliest_match(group_teams):
    mask = (wc26['home_team'].apply(norm).isin(group_teams)) | \
           (wc26['away_team'].apply(norm).isin(group_teams))
    return wc26[mask]['date'].min()

group_list.sort(key=lambda g: earliest_match(g))

group_rows = []
for i, group in enumerate(group_list):
    letter = string.ascii_uppercase[i]
    for team in group:
        group_rows.append({'group': letter, 'team': team})

df_groups = pd.DataFrame(group_rows)
df_groups.to_csv(f'{CLEAN}/groups_2026.csv', index=False, encoding='utf-8')
print(f'\n[OK] groups_2026.csv — {df_groups.shape}')
print('Groups:')
for letter, grp in df_groups.groupby('group'):
    print(f'  Group {letter}: {list(grp["team"])}')

# ── 3. STANDINGS_2026 ────────────────────────────────────────────────────────

# Compute from completed (non-null) matches only
played = wc26[wc26['home_score'].notna()].copy()
played['home_score'] = played['home_score'].astype(int)
played['away_score'] = played['away_score'].astype(int)

stand_records = {}
for _, row in played.iterrows():
    h, a = norm(row['home_team']), norm(row['away_team'])
    hs, as_ = row['home_score'], row['away_score']

    for team, gf, ga in [(h, hs, as_), (a, as_, hs)]:
        if team not in stand_records:
            stand_records[team] = {'team': team, 'played': 0, 'wins': 0,
                                   'draws': 0, 'losses': 0,
                                   'goals_for': 0, 'goals_against': 0}
        stand_records[team]['played']       += 1
        stand_records[team]['goals_for']    += gf
        stand_records[team]['goals_against'] += ga
        if gf > ga:
            stand_records[team]['wins']   += 1
        elif gf == ga:
            stand_records[team]['draws']  += 1
        else:
            stand_records[team]['losses'] += 1

df_stand = pd.DataFrame(list(stand_records.values()))
df_stand['goal_diff'] = df_stand['goals_for'] - df_stand['goals_against']
df_stand['points']    = df_stand['wins'] * 3 + df_stand['draws']

# Add group label
team_to_group = dict(zip(df_groups['team'], df_groups['group']))
df_stand['group'] = df_stand['team'].map(team_to_group)
df_stand = df_stand[['group', 'team', 'played', 'wins', 'draws', 'losses',
                      'goals_for', 'goals_against', 'goal_diff', 'points']]
df_stand = df_stand.sort_values(['group', 'points', 'goal_diff'],
                                 ascending=[True, False, False]).reset_index(drop=True)

df_stand.to_csv(f'{CLEAN}/standings_2026.csv', index=False, encoding='utf-8')
print(f'\n[OK] standings_2026.csv — {df_stand.shape}')
print('\nCurrent standings (top team per group):')
top = df_stand.groupby('group').first().reset_index()
print(top[['group','team','played','wins','draws','losses','goal_diff','points']].to_string(index=False))
