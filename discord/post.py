"""Poster nye artikler i Discord. Webhook-adresser kommer fra GitHub Secrets (miljøvariabler), aldri fra filer."""
import json, os, urllib.request

D = os.path.dirname(os.path.abspath(__file__))
HOOKS = {'no': 'DISCORD_WEBHOOK_NO', 'en': 'DISCORD_WEBHOOK_EN', 'it': 'DISCORD_WEBHOOK_IT'}
queue = json.load(open(os.path.join(D, 'queue.json'), encoding='utf-8'))
path = os.path.join(D, 'posted.json')
done = set(json.load(open(path)))
for a in queue:
    if a['id'] in done:
        continue
    complete = True
    for lang, env in HOOKS.items():
        if f"{a['id']}:{lang}" in done:
            continue
        hook = os.environ.get(env)
        if not hook:
            print(f'Mangler {env}, hopper over {a["id"]} ({lang}); prøves igjen neste kjøring')
            complete = False
            continue
        t = a[lang]
        payload = {'username': 'Milanisti', 'embeds': [{'title': t['title'], 'description': t['ingress'], 'url': t['url'],
                                                         'footer': {'text': t['badge']}, 'color': 0xC8102E}]}
        req = urllib.request.Request(hook, json.dumps(payload).encode(), {'Content-Type': 'application/json', 'User-Agent': 'milanisti'})
        urllib.request.urlopen(req, timeout=20).read()
        print('postet', a['id'], lang)
        done.add(f"{a['id']}:{lang}")
    if complete:
        done.add(a['id'])
json.dump(sorted(done), open(path, 'w'), indent=0)
