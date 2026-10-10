"""Poster nye artikler på X. Nøkler kommer fra GitHub Secrets (miljøvariabler), aldri fra filer.
Leser samme kø som Discord (discord/queue.json) og fører egen liste i x/posted.json.
Hvilke språk som postes, og til hvilken konto, styres av x/config.json.
X_DRY_RUN=1 skriver ut innleggene uten å sende noe."""
import base64, hashlib, hmac, json, os, secrets, time, urllib.parse, urllib.request

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(D)
API = 'https://api.x.com/2/tweets'
KEYS = ('API_KEY', 'API_SECRET', 'ACCESS_TOKEN', 'ACCESS_SECRET')
URL_LEN = 23  # X teller alle lenker som 23 tegn
LIMIT = 280
DRY = os.environ.get('X_DRY_RUN') == '1'


def q(s):
    return urllib.parse.quote(str(s), safe='~-._')


def oauth_header(method, url, k):
    """OAuth 1.0a (HMAC-SHA1). JSON-body inngår ikke i signaturen."""
    p = {'oauth_consumer_key': k['API_KEY'], 'oauth_nonce': secrets.token_hex(16),
         'oauth_signature_method': 'HMAC-SHA1', 'oauth_timestamp': str(int(time.time())),
         'oauth_token': k['ACCESS_TOKEN'], 'oauth_version': '1.0'}
    base = '&'.join([method, q(url), q('&'.join(f'{q(a)}={q(b)}' for a, b in sorted(p.items())))])
    key = f"{q(k['API_SECRET'])}&{q(k['ACCESS_SECRET'])}"
    p['oauth_signature'] = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    return 'OAuth ' + ', '.join(f'{q(a)}="{q(b)}"' for a, b in sorted(p.items()))


def text(t):
    """Merke, tittel og lenke. Kortes ned hvis det blir over 280 tegn."""
    head = f"{t['badge']}: {t['title']}" if t.get('badge') and t['badge'] != 'Milanisti' else t['title']
    room = LIMIT - URL_LEN - 2
    if len(head) > room:
        head = head[:room - 1].rstrip() + '…'
    return f"{head}\n\n{t['url']}"


def post(body, k):
    req = urllib.request.Request(API, json.dumps({'text': body}).encode(), method='POST', headers={
        'Authorization': oauth_header('POST', API, k), 'Content-Type': 'application/json', 'User-Agent': 'milanisti'})
    return json.loads(urllib.request.urlopen(req, timeout=20).read())


def main():
    cfg = json.load(open(os.path.join(D, 'config.json'), encoding='utf-8'))
    queue = json.load(open(os.path.join(ROOT, 'discord', 'queue.json'), encoding='utf-8'))
    path = os.path.join(D, 'posted.json')
    done = set(json.load(open(path)))
    budget = cfg.get('max_per_run', 3)  # vern mot å tømme hele køen på en gang
    for a in queue:
        for lang, account in cfg['accounts'].items():
            tag = f"{a['id']}:{lang}"
            if tag in done or budget <= 0:
                continue
            k = {n: os.environ.get(f'X_{account}_{n}') for n in KEYS}
            body = text(a[lang])
            if DRY:
                print(f'--- {tag} -> {account}\n{body}')
                continue
            if not all(k.values()):
                print(f'Mangler nøkler for X_{account}, hopper over {tag}; prøves igjen neste kjøring')
                continue
            try:
                r = post(body, k)
            except urllib.error.HTTPError as e:
                print(f'Feil fra X for {tag}: {e.code} {e.read()[:300]!r}')
                continue
            print('postet', tag, r.get('data', {}).get('id'))
            done.add(tag)
            budget -= 1
    if not DRY:
        json.dump(sorted(done), open(path, 'w'), indent=0)


if __name__ == '__main__':
    main()
