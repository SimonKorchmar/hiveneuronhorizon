# Future Weavers v3 — Character-Driven Storytelling Plan

> **Status (April 2026): v3 shipped. v4 (scene depth + dramatic spine)
> has been implemented on top of it — see
> `./v4_scene_depth_and_spine.md` for the design doc and `poc/README.md`
> for the pipeline map as it stands today.** This document is kept for
> historical context: the "why we went character-driven in the first
> place" baseline that v4 sharpens but does not replace.
>
> Evolution of the v2 pipeline (`v2_storytelling_pipeline.md`). v2 produced
> respectable essay-shaped history but monotonous prose, no people to
> follow, and a world that shrank around the first dominant fork. v3 adds
> characters with genuine dramatic stakes, a mastermind who assembles
> scaffolding (never prose), a narrator who picks a fresh chapter shape
> each epoch, and a voice strategy built around constrained variation.
>
> This document is the revised plan. An earlier draft had two prose
> passes, 10 character-LLMs writing in voice, and the outline at premium
> tier. All three were expensive in ways that did not buy quality. §0
> summarises what was wrong and why the fixes hold.
>
> ---
>
> ### v4 addendum (implemented)
>
> v3 gave us chapters that read as thematically cohesive institutional
> reportage — competent, steady, a little cold. v4, now implemented,
> addresses three things v3 structurally could not:
>
> 1. **Scene depth.** v3's scene budget counted scenes but said nothing
>    about what a scene was FOR. v4 attaches a scene-craft contract to
>    every scene (desire, obstacle, turn, cost, embodied gesture,
>    unresolved subtext — each scoped to the scene-moment, not the
>    year) and replaces v3's 10-way
>    structure menu with 6 chapter MODES whose word budgets encourage
>    fewer-and-deeper scenes (`monoscene`, `diptych`, `triptych`,
>    `long-march`, `overheard`, `mosaic`).
> 2. **A dramatic spine across the full decade.** v3 had per-year
>    tensions; v4 commits a whole run to one named dramatic question
>    (the `decade_spine` artefact) and makes every per-year stage —
>    fork proposer, summariser, cast plan, beat sheet, outline, narrator,
>    continuity pass — aim at the destination that spine names. Forks
>    are now typed irreversible events with a declared
>    `spine_wager_impact`; per-year summaries emit a `year_dilemma`
>    (an actor's binary choice with a clock, costs on both sides, and
>    a wager) rather than v3's one-sentence `central_tension`.
> 3. **Audited change, irreversibility, and collision.** The continuity
>    pass now records per-main `change_delta`, flags characters
>    unchanged for 3+ years (cast_plan must resolve them), enforces
>    >=1 on-page-or-ratified irreversible event per year, enforces a
>    collision scene when `main_cast >= 3`, enforces an in-scene words
>    ratio >=65%, and tracks typed hooks (with a `dramatic-seed`
>    minimum of 1 per year). Side characters and scene stagings are
>    now persisted across years to prevent quiet repetition.
>
> Full spec: `./v4_scene_depth_and_spine.md`. Code: `poc/poc.py`,
> `poc/prompts.py`. Pipeline map: `poc/README.md`.

---

## 0. Critique of the earlier v3 draft (fixed in this revision)

| Earlier flaw | Fix in this revision |
|---|---|
| Mastermind wrote a prose "character narrative" that the Narrator then rewrote. Two prose passes, averaged voice, redundant cost. | **One prose writer only.** Mastermind now outputs a structured JSON **beat sheet** (scenes, callbacks, character beats, dominant images). Narrator is the only stage that writes reader-facing prose. |
| 10 character-subagents each composed prose in their own voice. Ten weak impersonations averaged into a mush. | Character subagents now produce **dossiers** (JSON): want, obstacle, actions this year, 1–2 quotable lines, memorable image, unresolved-at-year-end. No prose. |
| Outline pass at premium tier. Structural reasoning overpaid. | **Outline moves to mid-tier.** Premium goes to execution + editor only. |
| Cast entries had role and voice, no dramatic stakes. | Cast entries now require **want + obstacle + contradiction** per year, plus a stable **tic** and a **signature object/place**. |
| "Interleave world and character" had no craft floor. | Outline must declare a **scene budget** (≥N scenes, each with when/where/who/sensory anchor/specific line). |
| Cohesion with last chapter was assumed, not enforced. | New **continuity pass** after the editor verifies ≥2 hooks from last chapter were picked up and ≥2 new ones planted. |
| Palette selection had "no-repeat" but no *chooser*. | Palette is picked by a rule: `year_mood` + cast composition + fork domain → palette candidate set; slop ledger prunes recent repeats. Plus a third axis (see §5.1): each chapter adds one **device constraint**. |
| Year-0 bootstrap unspecified (no cast for seed year). | Explicit **cast bootstrap** stage runs once at seed time to seed 3 founding characters from the seed JSON. |
| Narrative threads (movements, places, projects) got no continuity infrastructure separate from the cast. | **Thread register** parallel to the cast register, with the same freshness/retirement mechanics. |
| Editor free to "rewrite for texture" without palette fidelity check. | Editor is told the palette explicitly and is checked by the continuity pass on palette terms. |
| $0.60 / epoch. | **~$0.45 / epoch** (§9). Premium spend is concentrated where the reader can taste it. |

---

## 1. Core design principles

Five principles drive every decision below.

1. **One voice writes for the reader.** Only the Narrator produces
   reader-facing prose. Every other agent produces JSON or short
   structured notes. This is the single biggest quality-per-dollar
   lever in the system.
2. **Drama lives in stakes.** A character without a want and an obstacle
   is an observer. Observers bore. Every cast member, every epoch, has
   both.
3. **Freshness is a constraint problem.** Variation is manufactured by
   rotating palette + modulator + device each chapter, not by asking
   the model to "be creative."
4. **Off-page is often stronger than on-page.** When a year has one
   dramatic event (a landfall, a death, a coup), putting it off-page
   — referenced, remembered, implied — often makes the chapter feel
   more like lived history than staged drama. Consequence often beats
   spectacle. This is an Asimov/Borges/Le Guin move. We make it
   *available*, not required; the beat sheet decides, year by year,
   whether this chapter should use it.
5. **Cohesion is grammar, not vibes.** Callbacks to prior chapters and
   seeds for future ones are required, counted, and verified.

---

## 2. Pipeline shape (revised)

```
  CHOSEN FORK (from previous year)
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  1. SCIENCE SUBAGENTS  (5 parallel, cheap tier)             │
  │     ecology · economy · geopolitics · society · culture     │
  │     Input: chosen fork, OWN previous-epoch doc, previous    │
  │            overall year summary, active threads.            │
  │     Output: rich JSON (v2 shape) + a mandatory thread move  │
  │             (advance | transform | close) on ≥1 active      │
  │             thread.                                         │
  │  → 02_specialist_<name>.json                                │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  2. STATE MERGER  → 03_state.json                           │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  3. EPOCH SUMMARISER (mid)                                  │
  │     Balanced JSON summary + year_mood + central_tension     │
  │     (1 sentence: what is this year ABOUT?).                 │
  │  → 04_summary.json                                          │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  4. CROSS-INTERFERENCE ANALYST (mid)                        │
  │     Same as v2. Rotation rule: if >60% of interactions      │
  │     touch the fork's domain, re-prompt for ≥2 that don't.   │
  │  → 05_crossinterference.json                                │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  5. CHARACTER PLOT MASTERMIND (mid, 3 sub-steps)            │
  │                                                             │
  │     5a. CAST PLAN                                           │
  │         Inputs: summary, cross-interference, cast.json,     │
  │                 thread_register.json, previous chapter,     │
  │                 dormant items.                              │
  │         Outputs: the 3–6 main characters for this epoch.    │
  │         Each entry: returning | introduced | retiring,      │
  │         brief for subagent, POSITIONED AT a specific        │
  │         cross-interference (characters live on faultlines). │
  │         Must obey freshness rule: ≥1 new character every 2  │
  │         epochs; ≥1 returning character unless none exist.   │
  │     → 06a_cast_plan.json                                    │
  │                                                             │
  │     5b. CHARACTER DOSSIER DISPATCH (parallel, cheap tier)   │
  │         One dossier per cast member. Each subagent receives │
  │         their arc history, the current epoch summary, the   │
  │         cross-interference JSON, and their brief. Returns   │
  │         STRICT JSON (not prose): want, obstacle,            │
  │         contradiction, this_year_beats[], quotable_lines[], │
  │         memorable_image, unresolved_at_year_end, interacts_ │
  │         with[]. Voice tag stays metadata only.              │
  │     → 06b_dossier_<id>.json                                 │
  │                                                             │
  │     5c. BEAT SHEET (structured, not prose)                  │
  │         Mastermind reads all dossiers + last chapter's      │
  │         open hooks + the central_tension.                   │
  │         Produces JSON beat sheet: hooks_to_resolve[],       │
  │         hooks_to_plant[], ordered_beats[] (each: a cross-   │
  │         domain interaction + which cast members are         │
  │         present + in whose POV it is felt), side_characters │
  │         [], off_page_event (see §1.4), recurring_objects[]. │
  │     → 06c_beat_sheet.json                                   │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  6. NARRATOR ORCHESTRATOR (two-pass, tiered)                │
  │                                                             │
  │     6a. OUTLINE (MID tier)                                  │
  │         Inputs: summary, cross-interference, beat sheet,    │
  │                 dossiers, last chapter, style_ledger,       │
  │                 slop_ledger, year_mood, central_tension.    │
  │         Outputs a chapter outline that answers the          │
  │         READER'S COMPASS (§6.1):                            │
  │           - Follow-what: which thread/character the reader  │
  │             follows through the chapter                     │
  │           - Change-what: the one delta the chapter earns    │
  │           - Hook: the open question it hands forward        │
  │         Picks a STRUCTURE (§6.2), a VOICE PALETTE (§5.2)    │
  │         = base + modulator + device, a SCENE BUDGET (§6.3), │
  │         and a WORD BUDGET from year_mood (§5.3).            │
  │         Must justify each pick in 1 sentence.               │
  │     → 06d_chapter_outline.json                              │
  │                                                             │
  │     6b. EXECUTE (PREMIUM tier)                              │
  │         Writes the chapter to the outline. Must:            │
  │           - Interleave world-scale and human-scale in       │
  │             EVERY section (no pure-analysis sections).      │
  │           - Honour the scene budget with concrete           │
  │             when/where/who.                                 │
  │           - Leave the off-page event off-page.              │
  │           - Use every quotable line from dossiers at least  │
  │             once (may paraphrase).                          │
  │     → 06_story_draft.md                                     │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  7. EDITOR (premium)                                        │
  │     Polish + palette fidelity + slop-ledger enforcement.    │
  │     May rewrite sentences for texture, bound by specialist  │
  │     JSON + dossiers + beat sheet (no new facts).            │
  │  → 07_story_final.md                                        │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  8. CONTINUITY PASS (mid, short, cheap)                     │
  │     Reads final chapter + last chapter + outline + beat     │
  │     sheet. Verifies:                                        │
  │       - ≥2 hooks from last chapter were resolved or         │
  │         acknowledged                                        │
  │       - ≥2 hooks were planted for next chapter              │
  │       - chosen palette is demonstrably present              │
  │       - named characters: every cast member appears ≥1x     │
  │       - no invented names outside dossiers/specialist docs  │
  │       - cast state updated consistently                     │
  │     If any check fails, append a targeted `FIX:` note and   │
  │     re-run editor (single retry max).                       │
  │  → 07b_continuity_report.json                               │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  9. FORK PROPOSER (mid)                                     │
  │     Unchanged rules from v2 PLUS: at least one fork must    │
  │     come from a region/topic not dominant in the last 2     │
  │     years (anti-lock-in).                                   │
  │  → 08_forks.json                                            │
  └─────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 10. LEDGER UPDATE (code)                                    │
  │     cast.json · thread_register.json · style_ledger.json    │
  │     slop_ledger.json · chapter_index.json · dormant_* .json │
  │     per-character arc files · per-thread arc files          │
  └─────────────────────────────────────────────────────────────┘
```

### One-time seed bootstrap (runs before year +1)

```
SEED → 5 specialists' BASELINE summaries (already exists)
     → BASELINE CAST BOOTSTRAP (mid, one call)
         Reads seed JSON + seed summary. Picks 3 founding characters
         positioned at the seed's named threads (e.g. one hydrologist,
         one AI-labor displaced worker, one migrant). Writes cast.json
         and the three char_<id>_arc.md stubs so year +1 has an
         opening cast to call on.
     → INITIAL FORKS (as today)
```

---

## 3. Characters: making them matter

### 3.1 Dossier shape (per character, per epoch)

```json
{
  "id": "maria-okafor",
  "year": 2029,
  "status": "returning",
  "position": "cross-interference-id: verification-overrides-shift-ecological-priorities",
  "want": "To get the wastewater interface upgrade back on the funded list before the next storm.",
  "obstacle": "Her own report's admissibility is contested at the state level; the paperwork regime she opposes is now her enemy.",
  "contradiction": "She is a public scientist whose credibility depends on the same verification apparatus that is failing her project.",
  "this_year_beats": [
    "Drafts an ODR (opinion of record) that will be used as evidence in 2030 litigation.",
    "Meets with a municipal treasurer who has lost four bond auctions in a row.",
    "Refuses a television interview."
  ],
  "quotable_lines": [
    "We are pumping because we can account for pumping.",
    "The marsh does not sign a receipt."
  ],
  "memorable_image": "Spreadsheet open on her laptop at 2 a.m., beside a stack of reef tiles from a 2024 restoration project.",
  "unresolved_at_year_end": "Whether her report will be admitted in the state review scheduled for spring 2030.",
  "interacts_with": ["treasurer-aleksei-kunz"]
}
```

The mastermind's job in 5a is to produce briefs that make those fields *available*. The dossier call in 5b is cheap — each character is a single sub-1K-token prompt with a tight schema.

### 3.2 Cast register (`cast.json`)

Persistent per run. Records for each character: identity, status
(`active | dormant | retired | deceased`), bios, per-year notes,
relationships, `signature_tic` (one verbal or physical habit),
`signature_object_or_place`. Auto-marks `dormant` after 3 unused
epochs; the mastermind may revive by setting `active` and must
justify.

### 3.3 Thread register (`thread_register.json`)

Parallel to cast for non-human continuity: movements (e.g. "paperwork
justice"), places (e.g. "the proof-pack clinic on Canal Street"),
projects (e.g. "the Atlantic Adaptation Compact"). Same lifecycle
fields. The specialist "thread move" requirement (§2.1) writes here;
the mastermind beat sheet reads here.

### 3.4 Dramatic selection rule

The 5a cast plan **must** position each main character at a named
`cross_domain_interaction` from 05. Characters are not
representatives of domains; they are people living on faultlines. A
character whose role does not map to a current interaction should be
dormant this epoch.

### 3.5 Retirement beat

When a character is retired, the mastermind writes a single
**final_beat** sentence (stored on the cast entry). If the narrator
uses it, the chapter gets a small emotional close. This is the one
case a non-narrator may hand the narrator a prose fragment — because
one sentence cannot corrupt a voice.

---

## 4. The off-page event option

Every beat sheet MAY designate one **off_page_event** for the year:
the year's most dramatic single happening (a landfall, a death, a
collapse, a coup, a breakthrough) to be referenced, remembered, or
implied — but not staged directly. Examples of referencing: a date,
a flooded basement found the next morning, a line item on an
insurance refusal, a name spoken once.

This is **a tool, not a rule**. The mastermind decides per year
whether the chapter is better served by keeping one event off-page.
Most years will use it; some won't (a year with no single dominant
event, or a `turning` year where the event IS the chapter, won't).
The beat sheet's `off_page_event` field is nullable.

The reason we expose this as a first-class tool: it is one of the
specific structural tricks that separates lived history from staged
action prose. Asimov, Borges, Le Guin lean on it constantly. Done
well, it makes invented years feel recalled rather than scripted.

---

## 5. Voice strategy: palette × modulator × device

### 5.1 Three axes

Each chapter composes its voice from three independent choices:

1. **Base register** — the Asimov-inspired default plus a handful of
   close cousins:
   - *retrospective* (Foundation narrator; long view)
   - *dossier* (Encyclopedia Galactica; fragments)
   - *reported* (newsroom remove, named sources, dates)
   - *memoir* (close first-person, one character's year)

2. **Modulator** — a tonal colour layered on the base:
   - *elegiac* (turning, loss)
   - *ironic* (drift, absurdity of procedure)
   - *forensic* (reckoning, evidence)
   - *pastoral* (quiet, weather, object-study)
   - *polyphonic* (chorus of voices)

3. **Device constraint** (Oulipo-style; one per chapter):
   - "Every section opens on a date."
   - "No dialogue from public officials; only from private citizens."
   - "Every scene contains weather."
   - "Exactly three quotations; no more."
   - "The central character is never described physically."
   - "One paragraph per month of the year."
   - "No abstract noun is the subject of a sentence for the first 200 words."
   - "The word 'history' does not appear."

Base × modulator × device = hundreds of combinations. The outline
picks one of each, guided by `year_mood` + cast composition + fork
domain, and vetoed only by the slop_ledger's 3-year window on exact
repeats. Each mode has a 30-word **exemplar** baked into its registry
entry so the narrator sees the target texture, not an abstract
description.

### 5.2 Palette chooser (deterministic first, model-tunable second)

A small rule engine in code:

```
candidates = [palette for palette in REGISTRY
              if palette not in slop_ledger.window(years=3)
              and palette.fits(year_mood)
              and palette.supports(cast_size)]
outline_prompt: "Pick one from {candidates}, justify in one sentence
                 referencing the central_tension."
```

So the model isn't asked to invent a palette each time; it's asked to
pick between 3–5 fitting options. Cheaper, more consistent, easier
to debug.

### 5.3 `year_mood` → word budget

| mood | budget | pacing |
|---|---|---|
| acute | 1100–1400 | dense, short sentences in the body |
| drift | 600–800 | connective tissue, longer breath |
| reckoning | 1000–1200 | evidence-forward |
| turning | 1200–1600 | one scene gets real room |
| quiet | 500–700 | observation over argument |

### 5.4 Dynamic slop ledger

Editor writes into `slop_ledger.json` any phrase/structure it had to
kill, with a cooldown (default 3 years). On first read of the
existing run, seed with:

- `"Every truce purchases its own breakdown."`
- `"The Xs called it A. The Ys called it B. They were describing the same thing."`
- `"The year YYYY was the year in which …"`
- Openings `"By year's end…"`, `"In YYYY,"`
- Abstract-noun subjects repeated > twice per chapter.

Cooldown is pool-rotation, not permanent ban. That keeps variation
without starving the style bank.

---

## 6. Chapter structure (never the same twice)

### 6.1 Reader's compass (outline must answer)

Every outline JSON begins with three plain-English answers:

- **Follow-what** — the thread or character the reader follows through the chapter.
- **Change-what** — the single delta the chapter earns (a relationship, a status, a public understanding).
- **Hook** — the unresolved question handed to the next chapter.

If the outline can't answer these, the outline is rejected and
regenerated. Three rails. They do more for readability than any
stylistic rule.

### 6.2 Structure menu (outline picks one)

- **Braided POVs** — 3 characters, interleaved strands.
- **Fragment dossier** — 5–7 numbered fragments (a memo, a transcript, a clipping, a field note).
- **Single-POV year** — one character carries the chapter.
- **Before / During / After** — beats around a decisive event (possibly the off-page one).
- **Case-study frame** — one small place stands for the year; zoom in/out.
- **Chorus** — many short voices, no sustained POV.
- **Recursive** — year opens at its end, works backward.
- **Committee / ledger** — the year told as minutes or accounts.
- **Letters** — calendar of correspondence.
- **Historian-introduces-witness** — retrospective frame brackets a first-person testimony.

Slop ledger: same structure may not recur within 3 years.

### 6.3 Scene budget

The outline must declare ≥ N scenes depending on mood:

| mood | scenes | scene shape |
|---|---|---|
| quiet | ≥1 | anchored moment, sensory |
| drift | ≥2 | small, specific, offhand |
| reckoning | ≥3 | evidence-forward, at least one interior |
| acute | ≥3 | compressed, one with decision-weight |
| turning | ≥4 | at least one with consequence on-page |

Each scene specifies: `when` (date or hour), `where` (place we can
picture), `who` (named cast), `anchor` (sensory or physical detail),
`line` (one specific paraphrasable sentence).

---

## 7. File layout per epoch

```
runs/<run_id>/
  cast.json
  thread_register.json
  style_ledger.json
  slop_ledger.json
  chapter_index.json
  characters/
    char_<id>_arc.md              # one per named character
  threads/
    thread_<id>_arc.md            # one per named thread
  year_2026_seed.json
  year_2026_summary.json
  year_2026_cast_bootstrap.json   # NEW (once, at start)
  year_2027/
    01_fork.json
    02_specialist_*.json
    03_state.json
    04_summary.json               # now with year_mood + central_tension
    05_crossinterference.json
    06a_cast_plan.json            # NEW
    06b_dossier_<id>.json         # NEW (per character, JSON)
    06c_beat_sheet.json           # NEW (structured, not prose)
    06d_chapter_outline.json      # NEW
    06_story_draft.md             # narrator execution
    07_story_final.md             # editor polish
    07b_continuity_report.json    # NEW
    08_forks.json
    09_readability.json           # NEW
```

Numbering still reads top-to-bottom in pipeline order.

---

## 8. Readability metrics (printed + saved)

`09_readability.json` per epoch:

```
{
  "named_people_count": 5,
  "returning_characters": 3,
  "new_characters": 1,
  "retired_characters": 0,
  "scenes_count": 4,
  "unique_places": 7,
  "regions_covered": 5,
  "facets_covered": 5,
  "structure_used": "braided-povs",
  "palette": {"base":"retrospective","modulator":"forensic","device":"every-section-opens-on-a-date"},
  "hooks_resolved": ["hook-2028-okafor-testimony"],
  "hooks_planted": ["hook-2029-state-review","hook-2029-canal-street"],
  "slop_tics_flagged": []
}
```

Target thresholds enforced by continuity pass. A chapter that misses
more than one gets one auto-retry on the editor with targeted `FIX:`
notes; beyond that, it ships with a `degraded: true` tag in the
index for later human review rather than another retry.

---

## 9. Cost model (target: ~$0.45 / epoch)

| Stage | Tier | Notes | $ |
|---|---|---|---|
| 5 × specialists | mini | own-line memory → smaller input | ~$0.02 |
| Summariser (+ mood + central_tension) | mid | | ~$0.04 |
| Cross-interference | mid | | ~$0.04 |
| Cast plan (5a) | mid | small | ~$0.02 |
| Character dossiers (5b) | **cheap** | 3–6 × short JSON | ~$0.02 |
| Beat sheet (5c) | mid | structured, not prose | ~$0.03 |
| Outline (6a) | **mid** (not premium) | | ~$0.03 |
| Narrator execute (6b) | premium | | ~$0.12 |
| Editor | premium | | ~$0.10 |
| Continuity pass | mid | short check | ~$0.02 |
| Fork proposer | mid | | ~$0.02 |
| **Total per epoch** | | | **~$0.46** |

Compared to the earlier v3 draft ($0.60) and to v2 ($0.26):

- Kills one prose pass (mastermind weave → JSON beat sheet): −$0.05
- Kills prose in character subagents (→ JSON dossiers, cheap tier): −$0.05 and quality up
- Moves outline mid-tier: −$0.04
- Adds a cheap continuity pass: +$0.02

Net: ~$0.14 saved, quality meaningfully up.

Because nodes are immutable and cached, per-reader cost is still ~$0.

### Premium budget distribution

Of ~$0.46 per epoch, ~$0.22 is premium tier. 100% of that premium
spend is on stages the reader can directly taste (narrator execution
+ editor). No premium token is spent on structural reasoning or
dossiers.

---

## 10. Phased implementation

Each phase is shippable on its own and can be replayed against the
existing `runs/20260419-192449/` fixture for diffable comparison.

### Phase 1 — Skeleton (cast + threads + dossiers) — SHIPPED

- Add `cast.json`, `thread_register.json`, `dormant_*.json`.
- Add seed **cast bootstrap** stage.
- Add cast-plan (5a) + character-dossier dispatch (5b, JSON only) + beat-sheet (5c).
- Wire beat sheet into the v2 storyteller as an additional input. Keep v2 prompts for storyteller + editor otherwise unchanged.
- Replay 2027–2029 with the same forks.

**Ship criterion:** each chapter names ≥3 people, ≥1 returning character in 2028 and 2029, and the beat sheet's `quotable_lines` appear in the prose (even if awkwardly).

### Phase 2 — Narrator split + structure + reader's compass — SHIPPED

- Split the narrator: outline (mid) + execute (premium).
- Add structure menu + scene budget.
- Outline must answer the reader's compass (§6.1) or be rejected.
- Kill v2's default retrospective frame as the forced opener.

**Ship criterion:** 2027, 2028, 2029 use three different structures; each chapter has a filled-in compass; scene counts meet the mood targets.

**Implementation notes (shipped):**

- New stage `06d_chapter_outline.json`. `run_chapter_outline` in `poc.py`,
  prompt pair `CHAPTER_OUTLINE_SYSTEM` / `CHAPTER_OUTLINE_USER_TEMPLATE` in
  `prompts.py`.
- `chapter_index.json` tracks structure/mood/scenes/word_budget/voice_tilt
  per year so the no-repeat-within-3-years rule on `structure` can be
  enforced in code.
- Year mood is decided by the outline itself for now (summariser-side
  `year_mood` wiring is Phase 3 per §10).
- Storyteller promoted to premium tier (`MODELS["storyteller"]`) and its
  system prompt rewritten to render-the-outline instead of "historian
  writing long after the fact". Editor prompt teaches it to preserve the
  chosen structure rather than smooth every chapter into a single essay.
- Banned retrospective openers ("In YYYY,", "By year's end,", "The year
  YYYY was...") enforced both in the outline validator's
  `opening_line_seed` check and in the narrator + editor prompts.

### Phase 3 — Voice palette + device constraint + slop ledger — SHIPPED

- Add voice registry with exemplars.
- Add palette chooser (code-side candidate filter + mid-tier pick).
- Add dynamic slop ledger seeded from the existing outputs.
- Add `year_mood` wiring from summariser to budgets.

**Ship criterion:** blind read of three consecutive chapters reliably identifies three different voices; no seeded slop phrase recurs inside window.

**Implementation notes (shipped):**

- Voice registry lives in `poc.py` as three constants: `VOICE_BASES` (4),
  `VOICE_MODULATORS` (5), `VOICE_DEVICES` (8). Each entry carries a
  `description` and a ~30-word `exemplar` so the Narrator sees a target
  texture rather than an abstract instruction (plan §5.1). 4 × 5 × 8 =
  160 combinations available; a 3-year freshness window on each axis
  leaves > 100 combinations at every depth.
- Palette chooser is `compute_palette_candidates()`: a code-side filter
  that prunes each axis by (a) not-used-in-last-`PALETTE_WINDOW` years
  and (b) mood-fit tables for base and modulator (`_BASE_MOOD_FIT`,
  `_MODULATOR_MOOD_FIT`). Devices are only freshness-filtered. The
  outliner receives ≤5 candidates per axis with their exemplars and
  picks one of each, with a `justification` sentence that must
  reference `central_tension`. The code-side validator rejects any
  pick outside the candidate ids — the model cannot invent a palette.
- Slop ledger lives at `runs/<run_id>/slop_ledger.json`, seeded at
  startup with `SEEDED_SLOP_PHRASES` (v2's recurring tics plus generic
  AI essay/news slop). Each entry has `added_year`, `last_seen_year`,
  `cooldown_until_year` (= `added_year + SLOP_WINDOW`). Active entries
  for a given year feed into the outline, narrator, and editor
  prompts ("do not echo these"). After the editor runs,
  `_scan_and_refresh_slop()` is a cheap code-side substring scan that
  re-arms cooldowns for any seeded phrase the editor let through,
  avoiding a second LLM call.
- `year_mood` and `central_tension` are now emitted by the summariser
  (and the baseline summariser, so year +1 has a "previous summary"
  that already carries them). `_validate_summary_mood()` enforces
  `year_mood ∈ VALID_MOODS` and a non-empty `central_tension`. The
  outliner echoes `year_mood` (validator rejects any mismatch) and no
  longer invents mood or a `year_mood_rationale`.
- The outline's `voice_tilt` field is replaced by `voice_palette:
  {base, modulator, device, justification}`. `chapter_index.json`
  now records `voice_palette` per year; `_recent_palettes()` is what
  the chooser uses to enforce freshness.
- The Narrator and Editor both receive a rendered "palette card"
  (base + modulator + device + exemplars) plus the active slop list.
  The Narrator is told the device is a hard constraint; the Editor
  is told to preserve both the palette and the device and to rewrite
  any sentence that still echoes a slop-ledger phrase.

### Phase 4 — Continuity pass + off-page rule + anti-lock-in — SHIPPED

- Add continuity pass (§ pipeline 8).
- Track off-page-event use in the slop ledger so consecutive years don't all evade the big event.
- Enforce cross-interference rotation rule.
- Enforce fork-proposer "one fork from elsewhere."

**Ship criterion:** over any 3-year window after year 5, ≥3 domains and ≥4 distinct regions are named in every chapter; off-page event is present in non-turning years.

**Implementation notes (shipped):**

- New stage `07b_continuity_report.json` backed by
  `run_continuity_pass` (mid tier) in `poc.py` and the
  `CONTINUITY_PASS_SYSTEM` / `CONTINUITY_PASS_USER_TEMPLATE` pair in
  `prompts.py`. The auditor reads the final chapter + outline + beat
  sheet + cast plan + dossiers + the previous chapter's
  `hooks_to_plant` + the active slop ledger, and emits a STRICT JSON
  report: `hooks_resolved_from_previous[]`, `hooks_planted_observed[]`,
  `palette_fidelity{base_evidence, modulator_evidence, device_evidence,
  device_satisfied}`, `cast_appearances{id:{appears,evidence}}`,
  `invented_names[]`, `off_page_honored`, `issues[]`, `verdict`,
  `fix_notes`.
- A code-side layer (`_audit_continuity_report`) cross-checks the
  cases the LLM is most likely to soft-pedal: every main-cast id
  must be marked `appears: true`; if a previous chapter exists,
  `hooks_resolved_from_previous` must contain ≥2 entries;
  `hooks_planted_observed` must contain ≥2; `device_satisfied` must
  be true; `invented_names` must be empty; if the beat sheet
  declared an `off_page_event`, `off_page_honored` must not be false.
  Any code-detected problem overrides an LLM `pass` verdict. The
  audit output accumulates on `report.code_audit_problems` for
  transparency.
- On fail, `_build_fix_block` renders the auditor's `fix_notes` plus
  the code audit into a `FIX:` block prepended to the editor's user
  prompt. The editor is invoked ONCE more with the polished draft
  (not the original) so it is rewriting a near-final text, not
  re-starting. The slop scan runs again; the continuity pass runs
  again. A second failure ships the chapter with `degraded: true`
  on the report rather than looping.
- `chapter_index.json` now carries four new per-year fields:
  `chosen_fork_domain`, `off_page_used`, `hooks_planted` (copied from
  the beat sheet), and `cast_ids`. Plus `continuity_verdict` ∈
  {pass, fail, degraded}. `_append_chapter_index` takes these as
  explicit kwargs. Helpers: `_recent_chapters`,
  `_recent_off_page_uses`, `_recent_fork_domains`,
  `_previous_chapter_entry`.
- **Cross-interference rotation** (`CROSS_INTERFERENCE_FORK_DOMAIN_LIMIT
  = 0.60`): `run_cross_interference` now takes `fork_domain`. After
  each call, if >60% of interactions include the fork's domain OR
  fewer than 2 interactions avoid it, the analyst is re-prompted
  (up to 2 retries) with a concrete "keep your strongest fork-domain
  interactions, but replace the weakest ones so ≥2 do NOT include
  '<fork_domain>' in domains_involved" instruction. Exhausting
  retries ships what we have with a warning rather than blocking.
- **Off-page tracking**: `run_beat_sheet` now receives
  `previous_hooks_to_plant` (from last year's chapter_index entry)
  and `recent_off_page_years`. The beat-sheet prompt renders a new
  `RECENT OFF-PAGE USE` block: if the last
  `OFF_PAGE_CONSECUTIVE_LIMIT = 2` years both used off-page, the
  prompt strongly prefers on-page for this year; one recent use is
  permitted; zero is unconstrained. The beat-sheet system prompt
  also adds an explicit paragraph pointing to that block so the
  model sees the constraint.
- **Fork-proposer anti-lock-in** (`FORK_ANTI_LOCKIN_WINDOW = 2`):
  `_validate_forks` now takes `recent_fork_domains`. With recent
  entries in the index, at least ONE of the three proposed forks
  must use a domain NOT on that list (the prior two chosen-fork
  domains). The prompt renders a `CHOSEN-FORK DOMAINS IN RECENT
  YEARS` footer and the system prompt has a new hard rule #6
  declaring the anti-lock-in. Invalid responses retry with the
  exact problem string + recent set appended.
- Retry budgets (tuneable at the top of `poc.py`):
  `CONTINUITY_RETRY_MAX = 1`, `CONTINUITY_MIN_HOOKS_RESOLVED = 2`,
  `CONTINUITY_MIN_HOOKS_PLANTED = 2`.

### Phase 5 — Readability metrics + replay CLI — SHIPPED

- Add 09_readability.json.
- `python replay.py <run_id> --from-stage 04` — re-runs downstream
  stages on existing specialist JSONs. Essential for safely iterating
  on prompts.

**Ship criterion:** every year_<YYYY>/ folder contains a
`09_readability.json` that can be diffed across years to catch drift
(falling regions, rising retired-character count, palette
repetition); `python replay.py <run_id> --from-stage 07` rewrites
the editor output without re-running specialists / summariser /
mastermind / narrator; `python replay.py <run_id> --from-stage 09`
refreshes readability with no LLM call at all.

**Implementation notes (shipped):**

- Per-year `09_readability.json` generated by `compute_readability()`
  in `poc.py` (pure code, no API call). Fields follow plan §8 with
  three extras — `year`, `continuity_verdict`, `degraded` — so a
  grep across `runs/*/year_*/09_readability.json` reads as one
  diffable table. Places and regions are normalised (whitespace +
  case) before uniqueness counting so "Lagos" and " lagos " don't
  both count; `regions_covered` unions
  `headline_developments[*].region` and `regional_breakouts` keys
  across the 5 specialist docs. `facets_covered` counts distinct
  domains named across `crossinterference.cross_domain_interactions`
  (≤ 5; a dropping value is the symptom of the world shrinking
  around a dominant fork, which Phase 4's rotation rule exists to
  prevent). `slop_tics_flagged` re-scans the final prose using the
  same `_slop_phrase_matches` helper the editor ledger uses, so the
  metric reflects the prose on disk even when the editor was
  re-run on a continuity retry.
- `generate_epoch` now takes `start_from: str = "02"` and uses an
  ordered `STAGE_ORDER` tuple
  (`02 · 04 · 05 · 06a · 06b · 06c · 06d · 06 · 07 · 07b · 08 · 09`)
  with a load-or-run dispatch per stage: everything earlier than
  `start_from` is loaded from disk, everything at or after runs
  normally. Post-processing is gated on whether the feeder stage
  ran — chapter_index.json is rewritten whenever
  `start_from <= 07b` (cast_plan / beat_sheet / outline /
  continuity_verdict can all change the entry); cast.json + per-
  character arc files are updated only when dossiers (06b) re-ran;
  the slop-ledger scan runs only when the editor (07) or continuity
  retry (07b) produced fresh prose. All updates are idempotent on
  `year` so the same replay can be run repeatedly without corrupting
  ledgers. Arc-file appends remain append-only (cosmetic duplicate
  dated sections on repeated 06b replays; arc files are for humans
  and nothing else parses them).
- `poc/replay.py` is a thin CLI: `argparse` over
  `run_id · --from-stage · [--year]`, with `--from-stage` constrained
  to the `STAGE_ORDER` ids via `choices=`. It reconstructs
  `parent_state`, `previous_summary`, `prev_chapter_text`, and
  `prev_year` from the prior year's folder (or from the baseline
  summary + seed for year +1), loads the current year's fork from
  `01_fork.json`, strips the current year's `chapter_index.json`
  entry when applicable (so freshness filters see prior years
  only), and calls `generate_epoch(..., start_from=…)`. Stage 09
  alone skips the API-key check — it's pure code. Replaying a year
  older than the latest prints a warning because subsequent years
  were built on the old artefacts and this tool does not cascade.

### Phase 6 (later) — Chronicler era chapters

Every 5 years, a Chronicler stage writes `chapter_YYYY_YYYY.md` in a
distinct "historian of the historians" voice, over the previous 5
finals + summaries. Lets the tree be re-read at two zoom levels.

---

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Characters hallucinate facts beyond specialists | Dossier subagents receive ONLY specialist docs + cross-interference + their brief. Editor + continuity pass flag any name/number not traceable. |
| Cast grows past usefulness (20 active by year 10) | Auto-dormancy at 3 unused epochs; retirement beats; cap of 6 active per epoch enforced in 5a. |
| Beat sheet over-constrains the narrator into a checklist | Beat sheet is scaffolding, not a script. Narrator prompt explicitly allows reordering and omission of beats with a 1-sentence justification in `06d_chapter_outline.json`. Outline, not beat sheet, is the last word. |
| Device constraints produce cute / gimmicky chapters | Device list curated; each device has a usage note. Editor drops a device that fights the year_mood. Slop ledger tracks device reuse too. |
| Voice registry exhausts at depth 20 | 4 bases × 5 modulators × 8+ devices = 160+ combinations; 3-year window leaves hundreds available. |
| Off-page option is overused and every year starts to feel evasive | The mastermind decides year by year. Cross-interference JSON + cast composition drive the choice; slop ledger can track consecutive uses. Turning years and event-defined years keep the event on-page. |
| Palette chooser's rule engine stales over time | Candidate filter rules are data-driven (in code, easy to edit); nothing is baked into prompts. |
| Continuity pass enters an infinite retry loop | One retry maximum. Beyond that, chapter ships with `degraded: true` for later human review. |
| Arc history bloats token budget at depth 20 | `char_<id>_arc.md` keeps last 3 years verbatim + one-line per older year, like specialist docs. |
| First year has no returning cast | Cast bootstrap seeds 3 founding characters from seed JSON. |

---

## 12. What v3 does NOT change

- Tree model; immutable nodes; fork-click = new child.
- Seed file.
- 5-specialist shape (refined input, same output).
- Numbered per-epoch filenames.
- Caching philosophy (per-reader cost stays ~$0).

---

## 13. One-line summary

*v2 wrote history. The first v3 draft wrote prose twice, in ten voices,
and overpaid. This revision writes reader-facing prose once, in a
freshly-chosen voice, about people with stakes, with the biggest event
happening just off-page.*
