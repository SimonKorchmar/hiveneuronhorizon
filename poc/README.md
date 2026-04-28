# Future Weavers — Phase 0 PoC (v5 variance + long-arc + rupture pipeline)

A CLI that generates one year of future history at a time, anchored to a
named decade-scale dramatic question, populated by characters with wants
and obstacles, varied across setting / POV / time-scale / plot-shape,
staged under an explicit scene-craft contract, allowed one typed
surprise rupture when earned, audited for continuity and long-arc debt
before it ships, and recorded each year in a one-row readability metric
for diffable long-run audit.

- Design history: `../concepts/v2_storytelling_pipeline.md` (v2, essay-shaped)
- v3 plan:        `../concepts/plan.md` (character-driven baseline)
- v4 plan:        `../concepts/v4_scene_depth_and_spine.md`
- v5 plan:        `../concepts/v5_variance_long_arcs_and_surprise.md` (implemented here)

## Pipeline (per run + per year)

```
[once at seed time]
seed_state
   -> baseline summarizer              (read-only snapshot of the present)
   -> cast bootstrap                   (3 founding characters with stakes)
   -> decade spine (v4)                (00_decade_spine.json — the 10-year
                                        dramatic question, its wager, its
                                        countdown, its 3 acts. Injected into
                                        every per-year stage downstream.)

[per year]
chosen_fork                             (v4: a typed IRREVERSIBLE EVENT with
                                         actor/act/named_stake/clock AND a
                                         declared spine_wager_impact — no trends)
   -> 5 specialists in parallel        (ecology/economy/geopolitics/society/culture)
   -> state merger
   -> summarizer                       (balanced summary of ALL 5 facets;
                                        Phase 3: emits year_mood +
                                        central_tension; v4: also emits a
                                        year_dilemma — actor, two sides,
                                        clock, wager — the chapter's
                                        dramatic core)
   -> cross-interference analyst       (cross-domain interactions; Phase 4:
                                        rotation retry if >60% touch the
                                        chosen fork's domain)
   -> cast plan (5a)                   (3-6 main characters, positioned on
                                        faultlines; v4: every entry carries
                                        a `spine_stake`; characters flagged
                                        as unchanged for 3+ years MUST be
                                        retired OR returned with a
                                        `forced_change_note`)
   -> character dossiers (5b, parallel) (want, obstacle, beats, quotable lines,
                                        body detail — JSON)
   -> beat sheet (5c)                  (structured scaffolding, not prose;
                                        v4: assigns the year_dilemma to a
                                        POV character, declares >=1 typed
                                        IRREVERSIBLE_EVENT (on-page OR with
                                        an on-page consequence), plants
                                        TYPED HOOKS with >=1 dramatic-seed
                                        and ripens_by_year, and requires a
                                        collision_plan when main_cast >= 3;
                                        sees previous chapter's typed hooks
                                        + recent off-page use + the recent
                                        staging ledger)
   -> chapter outline (6a)             (v4: picks a CHAPTER MODE from
                                        {monoscene, diptych, triptych,
                                        long-march, overheard, mosaic}
                                        rather than v3's long structure
                                        list; same mode cannot recur
                                        within 3 years; mosaic is capped
                                        at ~20% of a run. Each scene
                                        carries a SCENE CRAFT CONTRACT
                                        — desire, obstacle, turn, cost,
                                        embodied_gesture, unresolved_subtext
                                        — plus opening_image.
                                        v3 per-scene `line`
                                        is retired. Voice palette picked
                                        from the expanded v4 registry with
                                        a SUPPRESSIVE-DEVICE CAP and the
                                        no-institution-named device
                                        disallowed in monoscene/diptych.)
   -> narrator execute (6b)            (Phase 2: prose rendered to the outline
                                        — premium tier, streamed; Phase 3:
                                        writes toward the palette exemplars,
                                        obeys the device constraint, avoids
                                        the active slop ledger)
   -> editor                           (polish that preserves structure +
                                        palette; enforces the slop ledger)
   -> continuity pass (7b)             (v4 audits, on top of v3's hooks /
                                        palette / cast / invented-names /
                                        off-page checks:
                                          * CHANGE_AUDIT — per main, a
                                            {verdict, axis, evidence}
                                            change_delta. At least one
                                            main must have changed; three
                                            unchanged years in a row flags
                                            a character for forced change
                                            or retirement next year.
                                          * IRREVERSIBILITY — every
                                            beat-sheet irreversible_event
                                            must be either on-page or
                                            ratified on-page by its named
                                            consequence.
                                          * COLLISION — when main_cast
                                            >= 3, at least one scene must
                                            stage >=2 mains exercising
                                            agency (not mere co-presence).
                                          * IN-SCENE RATIO — >=65% of
                                            chapter words must be active
                                            scene prose, not retrospective
                                            exposition.
                                          * TYPED HOOKS — >=1 dramatic-seed
                                            planted per year; previous
                                            dramatic-seeds prioritised for
                                            resolution.
                                        One editor retry on fail; second
                                        failure ships with `degraded: true`.)
   -> fork proposer                    (v4: 3 drastic IRREVERSIBLE forks
                                        across 3 domains, each declaring
                                        fork_type in {event,
                                        technology-fielded, person-enters,
                                        person-exits}, actor,
                                        irreversible_act, named_stake,
                                        clock, spine_advances, and
                                        spine_wager_impact. Trends are
                                        rejected. Anti-lock-in retained:
                                        >=1 fork from a domain not used in
                                        the last 2 years.)
   -> readability metrics (9)          (Pure code. Per-year
                                        09_readability.json — cast counts,
                                        scenes, places, regions, facets,
                                        mode_used (+ legacy structure_used),
                                        palette, hooks_resolved,
                                        hooks_planted, dramatic_seeds_planted,
                                        changed_mains,
                                        irreversible_events_declared /
                                        _observed, collision_required /
                                        _satisfied, in_scene_ratio, slop
                                        tics flagged. No LLM call; diffable
                                        across years.)
```

### v4: scene depth + dramatic spine (what v4 buys you)

v4 is the first major pass since v3 shipped a character-driven baseline.
v3 made the pipeline write "thematically cohesive institutional
reportage" — competent, steady, but a little cold. v4 is the cut that
pushes the prose toward fewer, deeper scenes with real dramatic stakes,
and commits the whole 10-year run to one named dramatic question rather
than letting each year drift on the current fork's vibe.

- **Decade spine** (`00_decade_spine.json`, one-time at seed). A named
  dramatic question the decade answers (yes/won/delivered, or no/lost/
  denied), a double-sided wager (both outcomes cost something), a
  specific dated countdown, a 3-act structure with year ranges, and
  per-character stakes. The spine is injected into the summariser,
  cast plan, beat sheet, outline, narrator, continuity pass, and fork
  proposer. Downstream stages aim at the destination the spine names;
  the fork proposer must declare how each fork pushes the wager
  (toward-yes / toward-no / sideways).
- **Year dilemma** replaces the v3 `central_tension` as the chapter's
  dramatic core. The summariser emits an `actor`, two choices each with
  costs, a stakes sentence, a clock that forces the choice, and a wager
  payoff both ways. The beat sheet then assigns the dilemma to a
  `dilemma_pov_character_id`; the outline and narrator build the
  chapter around that character's forced choice.
- **Chapter modes** supersede v3's 10-way structure menu. Six shapes:
  `monoscene`, `diptych`, `triptych`, `long-march`, `overheard`,
  `mosaic`. Each has its own scene count range, word-range guardrails,
  and compatibility rules with the palette devices. Same mode cannot
  recur within 3 years; `mosaic` is capped at ~20% of a run so the
  default shape remains few-and-deep scenes.
- **Scene craft contract**. Every scene in `scene_budget` must carry a
  `contract` with `desire` (what the POV wants IN THIS MOMENT, not the
  year), `obstacle` (what's between them and it, scene-specific),
  `turn` (how the pressure changes direction), `cost` (what's spent
  when the turn happens), `embodied_gesture` (a physical detail in the
  moment), and `unresolved_subtext` (what's not said aloud) — all
  non-empty strings. v3's per-scene `line` is retired; `anchor` is
  renamed `opening_image`. This is the mechanical version of "what is
  this scene FOR".
- **Typed hooks**. `hooks_to_plant` are now objects: `hook_id`, `type`
  in {`dramatic-seed`, `world-seed`, `admin-carry-over`}, `subtype`,
  `ripens_by_year`, `stake`. Every year must plant >=1 `dramatic-seed`;
  the continuity pass prioritises last year's dramatic seeds when
  auditing resolution. Legacy string hooks from pre-v4 runs are
  normalised as admin-carry-over so they still read.
- **Irreversibility budget**. Every beat sheet declares >=1 typed
  `irreversible_event` (`decision-enacted`, `loss`, `defection`,
  `arrival`, `departure`, `rupture`, `first-use`, `death`, `birth`).
  The continuity pass checks each event is either staged on-page or
  ratified on-page by its `on_page_consequence`. Silent off-page
  irreversibility is not allowed to carry the year.
- **Character change audit**. Per-main `change_delta` with `verdict`
  (`changed`/`unchanged`), `axis` (belief / status / relationship /
  body / capacity / allegiance), and evidence. >=1 main must have
  changed this year. Any character with a 3-year unchanged streak is
  flagged to the cast_plan stage, which must retire them OR return
  them with a `forced_change_note` committing to what breaks them
  open this year — they cannot be silently dragged along.
- **Side-cast register** (`side_cast.json`) and **staging ledger**
  (`staging_ledger.json`). Beat-sheet `side_characters` are persisted
  across years with rolling appearance counts (a promotion path to
  main cast if they keep showing up). The staging ledger records
  (character, location, gesture-family) signatures scene by scene
  and feeds recent signatures into the outline prompt to prevent
  the same character from doing the same thing in the same kind of
  room again.
- **Collision requirement**. When `main_cast.size >= 3`, the beat
  sheet's `collision_plan.required` MUST be true and the outline
  MUST stage at least one scene where >=2 mains exercise agency
  toward opposing / conflicting ends (not merely co-present). The
  continuity pass audits that the collision scene actually got
  staged on the page.
- **In-scene words ratio**. The continuity pass reports the
  percentage of chapter words that are active scene prose
  (dialogue, gesture, action) vs retrospective exposition. The
  pipeline enforces `>=0.65`. Retrospective framing remains useful
  for headers and transitions, but a chapter that is 40% scene and
  60% report is rejected.
- **Voice registry expansion + suppressive-device cap**. The palette
  picks up new bases (`close-third`, `dialogue-scene`, `letter`,
  `long-cam`), new modulators (`interior`, `domestic`, `bodily`,
  `wry-spoken`, `angry`), and new devices
  (`one-scene-in-one-hour`, `two-voices-alternating`,
  `one-body-detail-per-paragraph`, `no-institution-named`). Devices
  marked `suppressive` (devices that restrict what language the
  chapter can use) are capped at `SUPPRESSIVE_DEVICE_CAP` per
  rolling window so the run doesn't become a parade of constraints.
  The `no-institution-named` device is disallowed in `monoscene`
  and `diptych` modes to protect the scene contract.
- **Fork schema strictness**. Forks must be discrete IRREVERSIBLE
  EVENTS with `fork_type`, `actor`, `irreversible_act`, `named_stake`,
  `clock`, `spine_advances.{act, how}`, and `spine_wager_impact`.
  Trends ("trust in institutions keeps declining") are rejected at
  validation time.

See `../concepts/v4_scene_depth_and_spine.md` for the design doc.

### Phase 2: narrator split (what "outline" buys you)

The outline stage picks, per chapter:

- **Reader's compass** — `follow_what`, `change_what`, `hook`. Three rails
that answer "why am I reading this chapter?" before a word of prose is
written. If the outliner can't fill them, the outline is rejected.
- **Structure** — one of ten shapes (braided-povs, fragment-dossier,
single-pov-year, before-during-after, case-study-frame, chorus, recursive,
committee-ledger, letters, historian-introduces-witness). Same structure
may not recur within 3 years (tracked in `chapter_index.json`).
- **Scene budget** — ≥ N concrete scenes, each with `when` / `where` / `who` /
`anchor` / `line`. At most one world-only scene per chapter; this chapter
is populated by people.
- **Opening-line seed** — the narrator must lean on it; the v2 "In 2027, …"
retrospective opener is explicitly banned.

The narrator execute pass (premium) then renders the outline. The editor
preserves the chosen structure instead of smoothing every chapter into a
single historian voice.

### Phase 3: voice palette + device constraint + slop ledger

Freshness becomes a constraint problem rather than a "be creative" plea.

- `**year_mood` moves upstream.** The summarizer now picks the mood
(acute / drift / reckoning / turning / quiet) and writes a
`central_tension` sentence — the chapter's dramatic spine. The outliner
echoes these; it no longer invents them.
- **Voice registry** (in `poc.py`): 4 BASES (retrospective, dossier,
reported, memoir), 5 MODULATORS (elegiac, ironic, forensic, pastoral,
polyphonic), 8 DEVICES (Oulipo-style one-chapter constraints — "every
section opens on a date", "exactly three quotations", "the word
'history' does not appear", etc.). Each entry carries a ~30-word
exemplar so the narrator sees target texture, not an abstract label.
- **Palette chooser** — code-side `compute_palette_candidates()` filters
each axis by freshness (not used in the last 3 years) and mood-fit
(for base + modulator). The outline receives ≤5 candidates per axis
and picks one of each, with a `justification` sentence referencing
`central_tension`. The validator rejects any pick outside the
candidate set; the model cannot invent a palette.
- **Slop ledger** at `runs/<run_id>/slop_ledger.json`, seeded with v2's
recurring tics and generic AI essay/news slop. Active entries are
injected into outline / narrator / editor prompts with a "do not use,
do not paraphrase closely" instruction. After the editor runs, a
cheap substring scan re-arms cooldowns for any seeded phrase that
slipped through (no extra LLM call).

A one-time **cast bootstrap** runs once at startup after the baseline
summary: it seeds 3 founding characters from the seed JSON so year +1
has a cast to call on.

### Phase 5: readability metrics + replay CLI

Phase 5 is the developer-ergonomics phase. It doesn't change what's written
for the reader; it changes how we audit and iterate.

- **`09_readability.json` per epoch** — one flat JSON row per year,
derived from artefacts already on disk. Fields:
`named_people_count`, `returning_characters`, `new_characters`,
`retired_characters`, `scenes_count`, `unique_places`,
`regions_covered`, `facets_covered`, `structure_used`, `palette`
(base / modulator / device ids), `hooks_resolved`, `hooks_planted`,
`slop_tics_flagged`, `continuity_verdict`, `degraded`. Pure code —
no additional LLM calls. Makes long runs auditable at a glance and
turns "did that prompt tweak actually help?" into a diff of numbers
across the same fork path.
- **`replay.py <run_id> --from-stage <id>`** — stage-scoped re-run
against an existing run. `generate_epoch` now accepts `start_from`;
earlier stages are loaded from disk instead of recomputed. Typical
uses:
  - `--from-stage 07` — rewrite the editor + re-audit + re-propose
    forks + refresh readability (skips specialists / summariser /
    mastermind entirely).
  - `--from-stage 07b` — re-audit only, without rewriting the
    editor output. Useful for iterating on the continuity-pass
    prompt.
  - `--from-stage 09` — recompute readability only (code-only; no
    API key required).
  - `--year YYYY` — target an earlier year; default is the latest
    year folder. Replay warns if you target anything other than the
    latest year since it does not cascade.
- Stages share numbering with the `year_<YYYY>/` folder prefixes:
`02 · 04 · 05 · 06a · 06b · 06c · 06d · 06 · 07 · 07b · 08 · 09`.
The chapter index entry for the replayed year is stripped before
re-running so freshness filters on structure / palette see only
prior years, and re-appended after. Cast / arc updates are
idempotent on `year`.

### Phase 4: continuity pass + off-page rule + anti-lock-in

Phase 4 adds guarantees so a long run doesn't drift, lock in, or lose
characters mid-chapter.

- **Continuity pass** (`07b_continuity_report.json`): a cheap mid-tier
auditor reads the post-editor final chapter alongside its structural
contract (outline, beat sheet, cast plan, dossiers, the previous
chapter's `hooks_to_plant`, active slop ledger) and emits a strict
JSON report: which previous-chapter hooks were resolved, which new
hooks were planted, whether the chosen voice palette + device
constraint are actually realised, whether every main-cast character
appears, whether any names were invented outside the documented
record, whether the declared off-page event was honored. A code-side
cross-check (`_audit_continuity_report` in `poc.py`) catches the
cases the LLM tends to soft-pedal — every cast id must be
`appears: true`, ≥2 hooks resolved and ≥2 planted, `device_satisfied`
true, `invented_names` empty, off-page respected when declared. Any
fail, the auditor's `fix_notes` plus the code findings are rolled
into a `FIX:` block prepended to a single editor retry. A second
failure ships the chapter with `degraded: true` rather than looping.
- **Off-page tracking** (`chapter_index.json.off_page_used`): after two
consecutive off-page years, the next beat-sheet prompt is nudged
toward on-page so chapters don't feel systematically evasive. One
recent off-page is permitted; zero is unconstrained.
- **Cross-interference rotation** (`CROSS_INTERFERENCE_FORK_DOMAIN_LIMIT
= 0.60`): if more than 60% of the analyst's interactions touch the
chosen fork's domain, or if fewer than 2 avoid it, the analyst is
re-prompted for ≥2 non-fork interactions (up to 2 retries). Stops
the world from shrinking around whichever domain was forked.
- **Fork-proposer anti-lock-in** (`FORK_ANTI_LOCKIN_WINDOW = 2`): at
least ONE of the three proposed forks must be in a domain NOT used
as the chosen fork in the last 2 years. Prevents the narrative from
pivoting on the same axis year after year.

## Setup

```powershell
cd poc
pip install -r requirements.txt
# open .env and paste your key after OPENAI_API_KEY=
python poc.py
```

### Replay (Phase 5)

Re-run a slice of the pipeline on an existing run without regenerating
stages you didn't touch:

```powershell
# Rewrite editor + re-audit + re-propose forks + refresh readability
python replay.py <run_id> --from-stage 07

# Re-audit only (no editor call)
python replay.py <run_id> --from-stage 07b

# Refresh readability metrics only (pure code; no API key required)
python replay.py <run_id> --from-stage 09

# Target an earlier year explicitly
python replay.py <run_id> --year 2028 --from-stage 06d
```

Run `python replay.py --help` for the full stage list.

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
7. The storyteller streams 800–1200 words of prose in the chosen voice
  palette, rendering the outline against the beat sheet and dossiers.
8. The editor streams a polished final version.
9. A continuity pass audits the final chapter (hooks, palette, cast,
  invented names, off-page discipline). On fail, the editor runs once
  more with a targeted `FIX:` block; on second fail, the chapter ships
  with `degraded: true` on the report.
10. Three new drastic forks appear — at least one is guaranteed to be
   in a domain outside the last two years' fork choices. Pick one, or
   `q` to quit.

## Output layout

Every run produces its own folder:

```
poc/runs/<timestamp>/
  00_decade_spine.json                # one-time dramatic spine
                                      #           (question / wager /
                                      #           countdown / 3 acts /
                                      #           promise_lines /
                                      #           stakes_for_cast)
  cast.json                           # persistent cast register
  side_cast.json                      # NEW (v4): persistent side-cast
                                      #           register with rolling
                                      #           appearance counts
  staging_ledger.json                 # NEW (v4): (character, location,
                                      #           gesture-family) scene
                                      #           signatures to prevent
                                      #           repetition
  chapter_index.json                  # per-year structure + mood +
                                      #   voice_palette + chosen_fork_domain
                                      #   + off_page_used + cast_ids +
                                      #   continuity_verdict;
                                      # v4: `mode` (alongside legacy
                                      #   `structure`), typed hooks_planted
                                      #   objects, change_audit,
                                      #   irreversible_events_observed,
                                      #   year_dilemma
  slop_ledger.json                    # phrases in cooldown, seeded at startup
  setting_ledger.json                 # NEW (v5): place / POV /
                                      #   time-scale / plot-shape cooldowns
  debt_ledger.json                    # NEW (v5): all planted hooks as
                                      #   near/mid/long/decade obligations
  rupture_log.json                    # NEW (v5): quiet and ruptured years
  characters/
    char_<id>_arc.md                  # one per named character; appended each epoch
  year_2026_seed.json
  year_2026_summary.json              # baseline summary of the seed
  year_2026_cast_bootstrap.json       # founding 3 characters
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
    06a_cast_plan.json                # who appears this epoch (3-6)
    06b_dossier_<id>.json             # per-character JSON dossier
    06c_beat_sheet.json               # structured mastermind scaffold
    06d_chapter_outline.json          # compass + mode + scene budget;
                                      # v4: per-scene `contract`
                                      # (desire/obstacle/turn/cost/
                                      # gesture/subtext), `opening_image`
                                      # (no `line`), voice_palette;
                                      # v5: place/time/plot variance axes
    06e_rupture.json                  # NEW (v5): typed rupture or quiet
    06f_story_draft.md                # narrator execute draft
    06_story_draft.md                 # legacy mirror of 06f draft
    07_story_final.md                 # editor's polish (may be rewritten
                                      # once more if continuity pass fails)
    07b_continuity_report.json        # hooks / palette / cast /
                                      # invented-names audit, plus
                                      # `degraded: true` if the retry also
                                      # failed; v4 adds change_audit,
                                      # irreversibility, collision,
                                      # mode_fidelity.in_scene_ratio, and
                                      # typed-hooks fidelity blocks;
                                      # v5 adds setting/debt/promise/
                                      # rupture/fork-on-site audit fields
    08_forks.json                     # v4: forks typed as irreversible
                                      # events with fork_type / actor /
                                      # named_stake / clock /
                                      # spine_advances / spine_wager_impact;
                                      # v5 adds debt_role
    09_readability.json               # one-row audit record —
                                      # v4: mode_used, dramatic_seeds_planted,
                                      # changed_mains,
                                      # irreversible_events_declared
                                      # /_observed, collision_required
                                      # /_satisfied, in_scene_ratio;
                                      # v5 adds time_shape_used,
                                      # plot_shape_used, long_debts_planted,
                                      # debts_discharged, rupture_type
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