# Future Weavers — Phase 0 PoC (v3 character-driven pipeline)

A CLI that generates one year of future history at a time, populated by named
characters with wants and obstacles. Designed to prove whether the prose is
good enough to justify building the web app on top of it.

- Design history: `../concepts/v2_storytelling_pipeline.md` (v2, essay-shaped)
- Current plan:   `../concepts/plan.md` (v3, character-driven; Phase 1 implemented)

## Pipeline (per year)

```
chosen_fork
   -> 5 specialists in parallel        (ecology/economy/geopolitics/society/culture)
   -> state merger
   -> summarizer                       (balanced summary of ALL 5 facets)
   -> cross-interference analyst       (cross-domain interactions)
   -> cast plan (5a)                   (3-6 main characters, positioned on faultlines)
   -> character dossiers (5b, parallel) (want, obstacle, beats, quotable lines — JSON)
   -> beat sheet (5c)                  (structured scaffolding, not prose)
   -> storyteller                      (Asimov-inspired; weaves world + characters)
   -> editor                           (polish)
   -> fork proposer                    (3 drastic forks, 3 different domains)
```

A one-time **cast bootstrap** runs once at startup after the baseline summary:
it seeds 3 founding characters from the seed JSON so year +1 has a cast to
call on.

## Setup

```powershell
cd poc
pip install -r requirements.txt
# open .env and paste your key after OPENAI_API_KEY=
python poc.py
```

## What you'll see

1. A **baseline summary** of the seed year 2026 (so the first generated year has
   something to compare against).
2. Three **initial forks** for 2027 — each from a different domain (e.g. one
   geopolitical, one ecological, one cultural), each tagged with a drasticness
   level.
3. You type `1`, `2`, or `3` — the chosen fork seeds the epoch.
4. Five specialists run in parallel. Each saves a rich JSON document.
5. The summarizer reads all five and produces a balanced per-facet summary.
6. The cross-interference stage identifies how developments in different
   domains are interacting.
7. The storyteller streams 800–1200 words of Asimov-voice historical prose,
   comparing last year's summary with this year's.
8. The editor streams a polished final version.
9. Three new drastic forks appear. Pick one, or `q` to quit.

## Output layout

Every run produces its own folder:

```
poc/runs/<timestamp>/
  cast.json                           # persistent cast register
  characters/
    char_<id>_arc.md                  # one per named character; appended each epoch
  year_2026_seed.json
  year_2026_summary.json              # baseline summary of the seed
  year_2026_cast_bootstrap.json       # founding 3 characters (NEW)
  year_2027_initial_forks.json        # forks offered from the seed
  year_2027/
    01_fork.json                      # which fork was chosen
    02_specialist_ecology.json        # deep per-domain analysis
    02_specialist_economy.json
    02_specialist_geopolitics.json
    02_specialist_society.json
    02_specialist_culture.json
    03_state.json                     # merged world state
    04_summary.json                   # balanced, all-5-facets summary
    05_crossinterference.json         # cross-domain interactions
    06a_cast_plan.json                # NEW: who appears this epoch (3-6)
    06b_dossier_<id>.json             # NEW: per-character JSON dossier
    06c_beat_sheet.json               # NEW: structured mastermind scaffold
    06_story_draft.md                 # storyteller draft
    07_story_final.md                 # editor's polish
    08_forks.json                     # forks proposed for year 2028
  year_2028/
    ...
```

Numbered prefixes mirror pipeline order — an `ls` of any `year_YYYY/` folder
reads top-to-bottom in generation order.

## Tweaking

- **Models:** `MODELS` dict at the top of `poc.py`. Each tier is a fallback
  list; the first model that works wins. Swap in whatever your account
  supports.
- **Asimov voice:** edit `style_asimov.md`. It's injected into the storyteller
  and editor prompts.
- **Specialist depth:** edit `prompts.py`. Each specialist's `brief` is its
  character; the `SPECIALIST_SYSTEM_TEMPLATE` governs the shape of its output.
- **Seed:** edit `seed_2026.json` to start from a different "now".
- **Cost per year:** roughly $0.25–0.40 at 2026 OpenAI prices — up from ~$0.07
  in v1 but the output is dramatically richer. See the concept doc for a
  napkin breakdown.

## What this PoC is NOT

No DB, no web UI, no tree view, no auth, no caching, no moderation, no AI
images. All deferred to Phase 1+.
