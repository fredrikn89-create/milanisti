# Milanisti-tippen: oppsett

Tippingen lagrer tips og poeng i Supabase (gratis). Siden selv er fortsatt statisk.
Selve siden og tippeboksen bygges av `_build/tipgen.py` og `_build/tipping.js` i prosjektmappen, og er av til
`_build/data/tipping.json` har adresse og nøkkel.

## Én gang (Fredrik, ca. 10 minutter)
1. Lag konto og et nytt prosjekt på supabase.com (gratisplanen holder). Velg region i Europa, f.eks. Frankfurt eller Stockholm.
2. **SQL Editor → New query**: lim inn hele `tipping/schema.sql` og trykk Run.
3. **Authentication → Sign In / Providers**: slå på **Allow anonymous sign-ins** (folk tipper med kallenavn, uten e-post).
4. **Project Settings → API Keys**: kopier *Project URL* og den offentlige nøkkelen (*publishable* / *anon*). Disse er laget for å stå i nettsiden og kan sendes i tråden.
5. **GitHub → milanisti → Settings → Secrets and variables → Actions**: legg inn
   - `SUPABASE_URL` = Project URL
   - `SUPABASE_SERVICE_KEY` = den hemmelige nøkkelen (*secret* / *service_role*). Denne skal aldri stå i koden eller sendes i chat.

Deretter legges URL og offentlig nøkkel i `_build/data/tipping.json`, siden bygges og publiseres, og tippingen er på.

## Slik virker det
- `build.py` skriver `tipping/kamper.json` fra `fixtures.json`. Når den endres på main, sender workflowen `tipping.yml` kampene (og resultater) til Supabase.
- Resultat føres i `fixtures.json` som `"score": [2, 1]` dagen etter kampen. Poengtabellen regnes ut i databasen (viewet `tip_table`).
- Poeng: riktig resultat 3, riktig utfall 1. Tips kan endres til avspark; databasen avviser tips etter avspark og skjuler andres tips til kampen har startet.
- Rette et resultat eller fjerne et støtende kallenavn: Supabase → Table Editor → `tip_matches` / `tip_players`.
- Gratisprosjekter settes på pause etter en uke uten trafikk. Besøk på siden holder det i gang.
