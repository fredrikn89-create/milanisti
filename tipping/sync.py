"""Sender kampene i tipping/kamper.json til Supabase (tabellen tip_matches).

Kjøres av GitHub Actions når kamper.json endres. Trenger SUPABASE_URL og SUPABASE_SERVICE_KEY (secrets).
Resultat sendes bare når det finnes, så et resultat lagt inn for hånd i Supabase blir aldri nullstilt.
"""
import json, os, sys, urllib.request

url = os.environ.get('SUPABASE_URL', '').rstrip('/')
key = os.environ.get('SUPABASE_SERVICE_KEY', '')
if not url or not key:
    sys.exit('Mangler SUPABASE_URL eller SUPABASE_SERVICE_KEY')

matches = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kamper.json'), encoding='utf-8'))
cols = ('id', 'kickoff', 'home', 'away', 'comp')
plain = [{k: m[k] for k in cols} for m in matches if m.get('home_goals') is None]
scored = [{k: m[k] for k in cols + ('home_goals', 'away_goals')} for m in matches if m.get('home_goals') is not None]

for rows in (plain, scored):
    if not rows:
        continue
    headers = {'apikey': key, 'Content-Type': 'application/json', 'Prefer': 'resolution=merge-duplicates,return=minimal'}
    if key.startswith('eyJ'):  # gammel service_role-nøkkel (JWT); nye sb_secret_-nøkler går bare i apikey
        headers['Authorization'] = f'Bearer {key}'
    req = urllib.request.Request(f'{url}/rest/v1/tip_matches?on_conflict=id', data=json.dumps(rows).encode(), method='POST', headers=headers)
    with urllib.request.urlopen(req) as r:
        print(r.status, len(rows), 'kamper')
