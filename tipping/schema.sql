-- Milanisti-tippen: tabeller, tilgangsregler og poengtabell for Supabase.
-- Kjør hele filen én gang i Supabase: SQL Editor > New query > lim inn > Run.
-- Poeng: riktig resultat 3, riktig utfall (H/U/B) 1, ellers 0.

create table if not exists public.tip_matches (
  id text primary key,                 -- f.eks. 2026-27-milan-inter-serie-a (lages av build.py)
  kickoff timestamptz not null,        -- tipping stenger her
  home text not null,
  away text not null,
  comp text not null,
  home_goals smallint,                 -- null til kampen er spilt
  away_goals smallint
);

create table if not exists public.tip_players (
  id uuid primary key default auth.uid() references auth.users on delete cascade,
  name text not null check (char_length(btrim(name)) between 2 and 24),
  created_at timestamptz not null default now()
);
create unique index if not exists tip_players_name_key on public.tip_players (lower(btrim(name)));

create table if not exists public.tips (
  user_id uuid not null default auth.uid() references public.tip_players on delete cascade,
  match_id text not null references public.tip_matches on delete cascade,
  home_goals smallint not null check (home_goals between 0 and 20),
  away_goals smallint not null check (away_goals between 0 and 20),
  updated_at timestamptz not null default now(),
  primary key (user_id, match_id)
);

create or replace function public.tip_touch() returns trigger language plpgsql as $$
begin new.updated_at := now(); return new; end $$;
drop trigger if exists tips_touch on public.tips;
create trigger tips_touch before insert or update on public.tips for each row execute function public.tip_touch();

-- Åpen for tipping så lenge kampen ikke har startet
create or replace function public.tip_open(m text) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.tip_matches where id = m and kickoff > now())
$$;

alter table public.tip_matches enable row level security;
alter table public.tip_players enable row level security;
alter table public.tips enable row level security;

-- Kampene kan alle lese; bare synk-jobben (service role) skriver
drop policy if exists "les kamper" on public.tip_matches;
create policy "les kamper" on public.tip_matches for select using (true);

-- Navnene er offentlige (vises i tabellen); hver bruker lager og endrer bare sitt eget
drop policy if exists "les navn" on public.tip_players;
create policy "les navn" on public.tip_players for select using (true);
drop policy if exists "eget navn" on public.tip_players;
create policy "eget navn" on public.tip_players for insert to authenticated with check (id = auth.uid());
drop policy if exists "endre navn" on public.tip_players;
create policy "endre navn" on public.tip_players for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- Egne tips ser du alltid; andres først når kampen har startet (ingen kopiering)
drop policy if exists "les tips" on public.tips;
create policy "les tips" on public.tips for select using (user_id = auth.uid() or not public.tip_open(match_id));
drop policy if exists "nytt tips" on public.tips;
create policy "nytt tips" on public.tips for insert to authenticated with check (user_id = auth.uid() and public.tip_open(match_id));
drop policy if exists "endre tips" on public.tips;
create policy "endre tips" on public.tips for update to authenticated
  using (user_id = auth.uid() and public.tip_open(match_id)) with check (user_id = auth.uid() and public.tip_open(match_id));
drop policy if exists "slett tips" on public.tips;
create policy "slett tips" on public.tips for delete to authenticated using (user_id = auth.uid() and public.tip_open(match_id));

create or replace function public.tip_points(th int, ta int, rh int, ra int) returns int language sql immutable as $$
  select case when rh is null or ra is null then null
              when th = rh and ta = ra then 3
              when sign(th - ta) = sign(rh - ra) then 1
              else 0 end
$$;

-- Poengtabellen: bare spilte kamper teller
create or replace view public.tip_table as
select p.id, p.name,
       coalesce(sum(public.tip_points(t.home_goals, t.away_goals, m.home_goals, m.away_goals)), 0)::int as points,
       count(*) filter (where public.tip_points(t.home_goals, t.away_goals, m.home_goals, m.away_goals) = 3)::int as exact,
       count(*) filter (where m.home_goals is not null)::int as played
from public.tip_players p
left join public.tips t on t.user_id = p.id
left join public.tip_matches m on m.id = t.match_id
group by p.id, p.name;

grant select on public.tip_matches, public.tip_players, public.tip_table to anon, authenticated;
grant select, insert, update, delete on public.tips to authenticated;
grant insert, update on public.tip_players to authenticated;
