# Future Weavers v2 — Storytelling Pipeline

> Second iteration of the per-epoch generation pipeline. The original
> (`../concept.md`, §1) treated "one year" as "one dramatic scene written
> around the chosen fork." v2 treats one year as **a slice of history seen
> in the round**, and writes it as history rather than as a scene.

---

## 1. Why v2

Observed from the Phase 0 dry-run:

1. **Specialists were too shallow.** A flat JSON with a few bullet notes
   doesn't give the downstream writer anything to stand on. The prose
   inherited that shallowness.
2. **The orchestrator narrated only the fork's domain.** If the chosen fork
   was geopolitical, that year read as a geopolitics scene, and the
   ecology/society/culture changes merged silently into state without ever
   reaching the page. Over several years, the story lost its sense of a
   world; it became a single thread.
3. **No explicit cross-domain reasoning.** The interesting parts of a year
   are the collisions — a crop failure that feeds a labor crisis that
   re-elects a populist. The old pipeline had no stage whose job was to
   *find* those collisions.
4. **The prose didn't feel like history.** It felt like a scene told from
   inside the year, not a historian looking back.
5. **Forks clustered.** Three forks often turned out to be three flavors of
   the same tension rather than genuinely divergent paths.

---

## 2. Pipeline shape

```
  CHOSEN FORK (from previous year)
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  5 SPECIALISTS (parallel, cheap tier, DEEPER prompts)       │
  │  ecology · economy · geopolitics · society · culture        │
  │  Each returns a rich JSON document:                         │
  │    - headline_developments (named actors, regions)          │
  │    - quantitative_changes (with reasoning)                  │
  │    - regional_breakouts                                     │
  │    - internal_tensions                                      │
  │    - continuity_from_last_year                              │
  │    - notes_for_storyteller (3-6 bullets)                    │
  │    - state_updates  (facet replacement for merged state)    │
  │  Saved per-file: 02_specialist_<name>.json                  │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  STATE MERGER  →  03_state.json                             │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  ORCHESTRATOR #1 — SUMMARIZER (mid tier)                    │
  │  Reads all 5 specialist JSONs + merged state.               │
  │  Produces a BALANCED summary of the whole year:             │
  │    - per_facet_summary (3-5 sentences each, all 5 facets)   │
  │    - year_in_one_paragraph                                  │
  │    - continuities_from_previous_year                        │
  │    - new_threads_emerging                                   │
  │  → 04_summary.json                                          │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  ORCHESTRATOR #2 — CROSS-INTERFERENCE (mid tier)            │
  │  Reads the summary + all 5 specialist JSONs.                │
  │  Finds where changes in DIFFERENT domains interact:         │
  │    - cross_domain_interactions[]                            │
  │        domains_involved, description, trajectory            │
  │        (reinforcing | dampening | contradictory),           │
  │        likely_effects_next_year                             │
  │    - emergent_themes[]                                      │
  │  → 05_crossinterference.json                                │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  STORYTELLER (mid tier, Asimov voice)                       │
  │  Inputs:                                                    │
  │    - previous year's summary                                │
  │    - this year's summary                                    │
  │    - this year's cross-interference JSON                    │
  │    - Asimov style guide                                     │
  │  Writes ~800–1200 words of "history unfolding" prose,       │
  │  comparing the two summaries, weaving in the interference   │
  │  themes. Retrospective historian voice.                     │
  │  → 06_story_draft.md                                        │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  EDITOR (premium tier, Asimov polish)                       │
  │  Tightens the draft, kills slop, enforces Asimov voice.     │
  │  Does not invent new facts.                                 │
  │  → 07_story_final.md                                        │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  FORK PROPOSER (mid tier)                                   │
  │  Proposes 3 DRASTIC forks from 3 DIFFERENT domains.         │
  │  Each: {domain, title, drasticness, flavor}.                │
  │  Rejected and re-prompted if two forks share a domain.      │
  │  → 08_forks.json                                            │
  └─────────────────────────────────────────────────────────────┘
```

---

## 3. Key design decisions

### 3.1 Specialists return rich documents, not patches

The v1 specialist returned `{updates, notes}` and that was it. In v2 a
specialist returns an entire analytical document. The downstream summarizer
and storyteller both read those documents directly. The merged `state` is
still produced (from a `state_updates` field inside each document) but state
is no longer the primary substrate for prose. The specialist documents are.

Implication: specialist output budget grows from ~300 tokens to ~1200–1800
tokens. Still cheap-tier.

### 3.2 Summarizer is the "balance" stage

This is the stage the v1 orchestrator was *implicitly* doing badly. By
making it explicit and JSON-structured, the storyteller is guaranteed to
see all five facets, not just the one the fork touched.

### 3.3 Cross-interference is a first-class stage

Without it, the storyteller has to do both the summary job and the
connection-finding job at once, in prose, while also holding Asimov voice.
Splitting it out means the storyteller can trust a pre-digested list of
"here are the collisions between domains this year" and concentrate on
rendering them well.

### 3.4 Storyteller is comparative, not scenic

The storyteller's prompt makes its job explicit: *compare* the previous
year's summary with this one; describe the *transition*, not the snapshot.
This is what makes it read like history rather than diary.

### 3.5 Asimov is the target voice, not KSR

The original style guide aimed at Kim Stanley Robinson / Ted Chiang. That's
appropriate for scenic, first-person-adjacent near-future fiction. For
*historical* narration — the voice we now want — Asimov's Foundation
narrator is a better fit: confident, retrospective, encyclopedic, dry,
trusting the ideas. See `poc/style_asimov.md`.

### 3.6 Forks are enforced cross-domain

The fork proposer must tag each fork with one of the five domains and the
proposer is re-prompted (or in PoC: the run errors loudly) if two forks
share a domain. This forces the branch tree to explore genuinely different
axes of the future rather than three flavors of the same one.

The `drasticness` tag (`moderate | high | extreme`) lets us later surface
"what if we always pick extreme" tours of the tree.

---

## 4. On-disk layout per epoch

```
runs/<run_id>/
  year_2026_seed.json
  year_2026_summary.json        # baseline summary of the seed, produced once
  year_2027/
    01_fork.json
    02_specialist_ecology.json
    02_specialist_economy.json
    02_specialist_geopolitics.json
    02_specialist_society.json
    02_specialist_culture.json
    03_state.json
    04_summary.json
    05_crossinterference.json
    06_story_draft.md
    07_story_final.md
    08_forks.json
  year_2028/
    ...
```

Numbered prefixes are deliberate: they mirror pipeline order, so `ls` gives
you a reproducible reading order for any year.

---

## 5. Cost delta (napkin)

Per epoch, rough 2026-USD:

| Stage | Tier | In | Out | $ |
|---|---|---|---|---|
| 5 × specialists | mini | ~3k ea | ~1.5k ea | ~$0.03 total |
| Summarizer | mid | ~8k | ~1k | ~$0.04 |
| Cross-interference | mid | ~8k | ~800 | ~$0.04 |
| Storyteller | mid | ~6k | ~1.2k | ~$0.05 |
| Editor | premium | ~2k | ~1.2k | ~$0.08 |
| Fork proposer | mid | ~4k | ~500 | ~$0.02 |
| **Total** | | | | **~$0.26** |

Up from v1's ~$0.07. Roughly 4× the cost for output that is dramatically
more substantive. Still cache-once-read-forever, so the per-reader cost is
unchanged.

---

## 6. What v2 does *not* change

- Tree model (immutable nodes; forking = new child).
- Seed (hand-written `seed_2026.json`).
- Data model shape for nodes (just more fields saved).
- Every-click-branches policy.
- The deferred list from `concept.md` §8 (images, maps, voice, multi-seed).

---

## 7. Risks introduced by v2

| Risk | Mitigation |
|---|---|
| Summaries diverge from specialist JSONs (summarizer hallucinates) | Summarizer prompt forbids introducing facts not present in the specialist outputs. Future: JSON-level consistency check. |
| Cross-interference stage invents interactions that aren't real | Same constraint: must cite which specialist documents contain the participating facts. |
| Asimov voice everywhere becomes monotonous over 20 years | Style guide includes cadence rules (vary scope of time discussed, alternate long retrospective sentences with short declarative ones). Revisit at depth 10. |
| Longer outputs → more tokens for downstream stages in deep branches | The full state + all 5 specialist docs grows unboundedly. At depth N we may need to roll older specialist docs into a condensed "historical context" block. Not a v2 problem; flag for v3. |
| Fork domain constraint too rigid (sometimes two domains are genuinely co-mingled) | Allow `domains_involved: ["ecology","economy"]` plurals in a future revision; v2 keeps it strict to avoid collapse back to single-domain forks. |

---

## 8. Implementation notes

- Specialists run in parallel (`asyncio.gather`). Everything after is
  sequential — each stage depends on the previous.
- First run generates a baseline summary of the seed so that year 2027 has
  "previous year" content to compare against.
- All structured outputs use JSON mode; prose outputs stream to the
  terminal for feel.
- Model tiers are swappable at the top of `poc.py`. The fallback list is
  the PoC's answer to "this model isn't on your account."

---

*v2 mantra: **specialists analyse, summariser balances, cross-interference
connects, storyteller narrates, editor polishes.** Five jobs, five prompts.
No one agent is asked to do two things at once.*
