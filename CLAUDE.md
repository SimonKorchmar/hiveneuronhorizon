# Future Weavers

A generative-storytelling project: a branching tree of possible futures, written one year at a time by a committee of LLM agents. The eventual product is a web app where readers walk the tree and each fork permanently spawns a new branch. The current state of this repo is a **CLI-only Phase 0 PoC** in Python — the goal is to prove that the prose quality is good enough to build the rest of the product on top of.

Core mantra: **state is cheap, prose is expensive, cache everything.** Specialists mutate a structured JSON world state (cheap models). Only the orchestrator + editor render prose (mid/premium). Nodes are immutable once written.

## Layout

- `concept.md` — the original product concept (web app, agents, cost model, roadmap). Read this for the *why*.
- `concepts/` — design docs for successive pipeline versions.
  - `v2_storytelling_pipeline.md` — first pass.
  - `plan.md` — v3, character-driven baseline.
  - `v4_scene_depth_and_spine.md` — v4, fewer-and-deeper scenes + decade dramatic spine. **This is what `poc/` currently implements.**
- `poc/` — the Phase 0 Python CLI. See `poc/README.md` for the full pipeline diagram.
  - `poc.py` — single-file pipeline (~200KB; specialists, summariser, cross-interference, cast/dossier/beats, outline, narrator, editor, continuity pass, fork proposer, readability metrics).
  - `prompts.py` — all prompt templates and schemas.
  - `replay.py` — stage-scoped re-run CLI for iterating on later stages without recomputing earlier ones.
  - `seed_2026.json` — the canonical real-world starting state (year 2026).
  - `style_guide.md` / `style_asimov.md` — voice contracts injected into orchestrator + editor prompts.
  - `runs/<timestamp>/` — every run is a fresh folder; year subfolders contain numbered artefacts (`02_specialist_*.json`, `06d_chapter_outline.json`, `07_story_final.md`, etc.) in pipeline order.
  - `requirements.txt` — `openai`, `python-dotenv`. That's it.

## Running the PoC

```bash
cd poc
pip install -r requirements.txt
# put OPENAI_API_KEY=... in poc/.env
python poc.py             # interactive: pick a fork each year
python replay.py <run_id> --from-stage 07   # rewrite editor + downstream
python replay.py <run_id> --from-stage 09   # readability only, no API key
```

Cost is roughly $0.25–0.40 per generated year at current OpenAI prices. Models are configured in the `MODELS` dict at the top of `poc.py` (each tier is a fallback list).

## Pipeline at a glance (v4)

Per year: `chosen_fork → 5 specialists (parallel) → state merger → summariser (emits year_dilemma) → cross-interference → cast plan → dossiers → beat sheet (declares irreversible_events + typed hooks) → chapter outline (picks a mode + per-scene contract + voice palette) → narrator (premium, streamed) → editor (premium) → continuity pass (audits change/irreversibility/collision/in-scene ratio + hooks/palette/cast) → fork proposer (3 typed irreversible-event forks) → readability metrics`. One-time at run start: baseline summary, cast bootstrap, decade spine.

Key invariants the pipeline enforces:
- ≥1 main character must change per year; 3-year unchanged streak forces retirement or a forced-change arc.
- ≥1 typed `dramatic-seed` hook planted per year; previous dramatic-seeds prioritised for resolution.
- ≥1 `irreversible_event` per year, on-page or with on-page consequence.
- ≥65% of chapter words must be active scene prose, not retrospective exposition.
- When `main_cast >= 3`, at least one collision scene with two mains exercising opposing agency.
- Forks must be discrete events, not trends; ≥1 of the 3 proposed forks must be in a domain not used in the last 2 years.
- Same chapter mode cannot recur within 3 years; `mosaic` capped at ~20% of a run.

## Conventions

- **Nodes/years are immutable.** Never edit a written year — replay creates new artefacts but does not retroactively change the chapter index entry except for the targeted year.
- **Numbered file prefixes mirror pipeline order.** `ls year_YYYY/` reads top-to-bottom in generation order. Keep this property when adding stages.
- **Prompts live in `prompts.py`, code in `poc.py`.** When changing model behavior, prefer prompt edits; reach for code only when the validator or pipeline shape needs to change.
- **Style is a contract, not a suggestion.** `style_guide.md` and `style_asimov.md` are injected into orchestrator + editor. The slop ledger (`runs/<run_id>/slop_ledger.json`) actively bans recurring tics — extend it rather than relaxing the prose.
- **Phase 0 deliberately has no DB, no UI, no auth, no caching, no moderation, no images.** All deferred to Phase 1+. Don't add them here.

## What's *not* in scope right now

The web app (Next.js + Supabase + React Flow) described in `concept.md` is Phase 1. The PoC exists to gate that work on prose quality. If a change would help the eventual web app but doesn't improve what gets written to `07_story_final.md`, it probably belongs in a Phase 1 branch, not here.
