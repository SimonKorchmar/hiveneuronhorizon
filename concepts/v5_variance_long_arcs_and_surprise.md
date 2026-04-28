# Future Weavers v5 — Variance, Long Arcs, and Earned Surprise

> **Status (April 2026): proposed.** v4 is implemented and its scene-craft
> contract is doing its job — the prose is dense, embodied, and
> sensorily anchored. v4's audits all pass on run `20260423-155647`
> (`in_scene_ratio: 0.98`, three "changed" mains, two on-page
> irreversible events, collision satisfied, continuity verdict
> `pass`). And the chapters still read as flat. This is the v5
> diagnosis and the levers proposed to fix it.
>
> Where v4 was about **what a scene must do**, v5 is about **what
> a chapter must vary, what a year must owe the future, and what a
> chapter is allowed to do that the outline did not authorize**.
>
> v4 made the camera better. v5 has to move the camera, lengthen the
> film, and let the actors break a window.

---

## 0. Critique of the v4 output (evidence-based)

Diagnoses observed in `runs/20260423-155647/year_2027/07_story_final.md`
and `year_2028/07_story_final.md`. v4 metrics on these chapters all
pass; the failures below are not metric failures, they are gaps the
v4 metrics did not measure.


| v4 failure                                            | What the reader feels                                                 | Root cause                                                                                                                                                    |
| ----------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Year 2028 is a remake of 2027 in the same room        | "I have read this chapter."                                           | No constraint on **setting / POV / time-scale repetition** at chapter level. The staging ledger only audits per-scene gestures.                               |
| Chosen forks get compressed back to Ana's desk        | "The drastic event happened off-screen and got summarized."           | Beat sheet has no rule that the chapter must **stage the fork's irreversible act on-page where it happens**. Speakerphone counts as on-page.                  |
| `central_tension` repeats verbatim across years       | "We're having the same argument again."                               | Summariser has no anti-repetition memory of previous years' tensions; tension is allowed to be a stable theme, not a moving wager.                            |
| Hooks all ripen `+1 year`                             | "Every cliffhanger is 'find out at the next audit'."                  | `ripens_by_year` is treated as a single-step counter, not a debt ledger. No mechanism plants long debts (3–7 yr) or rewards their late resolution.            |
| Decade spine is in every prompt but binds no decision | "There is no destination."                                            | Spine is injected as context. No stage **claims against it**, no audit checks that this year **discharged any of its act's promise material**.                |
| Every irreversible event is paper                     | "It's all administrative."                                            | No diversity rule on `irreversible_event.type` across years; `decision-enacted` is the easiest to stage in a monoscene at a desk and is what gets chosen.     |
| `monoscene` mode wins by default                      | "The story is a stage play with one set."                             | Mode rotation rule forbids same mode within 3 years, but the easiest way to satisfy `in_scene_ratio ≥ 0.65` and `collision` is monoscene/diptych in one room. |
| New cast members enter as bodies, not engines         | "Carolina is here. Carolina straightens corners. Carolina sits down." | Cast-plan validates count and faultline-position, not whether the new entrant **drives a beat**. Side characters never get a `scene_drives` flag.             |
| Nothing surprises the reader                          | "I knew where this was going from page one."                          | The pipeline is fully deterministic from spine to outline to narrator. The narrator's licence is to render — never to rupture, withhold, or upstage.          |
| Continuity pass rewards predictability                | "The chapter does what it said it would do, and that is the problem." | The pass audits beat-sheet **fidelity**. There is no audit for whether **anything genuinely unexpected** happens.                                             |


The unifying observation: v4's metrics measure the *quality of a single scene* and the *bookkeeping of a single year*. They do not measure **variance across the run**, **debt to the future**, **distance from the procedural baseline**, or **the presence of the unforeseen**. v5 adds those four.

---

## 1. Core v5 principles (in addition to v3's five and v4's three)

1. **A run is a sequence of differences.** Place, POV, time-scale, and plot-shape are first-class budget axes; a chapter that reuses last year's combination must justify it explicitly or be rejected.
2. **Each year owes the future.** A chapter must plant at least one **long debt** (ripens ≥ 3 years out) and must explicitly discharge or escalate at least one **standing debt** from the run's open ledger.
3. **The spine is a contract, not context.** The decade spine's act-level `promise` text decomposes into specific dramatisation obligations; each year claims against ≥ 1 obligation and the continuity pass audits the claim on-page.
4. **A chapter is allowed to surprise itself.** The pipeline reserves a structured slot for a **rupture** the outline did not author — selected from a typed registry, declared in advance, and audited for whether it actually surprised.

---

## 2. Variance budget — place, POV, time, and shape

The single biggest lever after v4. Today the pipeline produces an
office-desk-monoscene-real-time-decision-then-stamp every year. v5
makes that combination harder to reach for than its alternatives.

### 2.1 The `setting_ledger.json` (new run-level artefact)

Modelled on `slop_ledger.json` and `chapter_index.json`, but tracks
**chapter-level** combinations, not phrases or per-scene gestures. One
row per year:

```json
{
  "year": 2028,
  "place_signature": "ana-office:el-paso-county-liaison",
  "place_family": "office-bureaucratic-interior",
  "pov_gravity_well_id": "ana-miranda",
  "time_scale": "single-hour-real-time",
  "plot_shape": "decision-under-audit-pressure",
  "irreversible_event_types": ["decision-enacted", "first-use"],
  "act_promise_claimed": "act-1-corridor-improvised"
}
```

Each axis has a **cooldown window**:


| Axis                       | Cooldown | Notes                                                                                                                                                               |
| -------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `place_signature`          | 3 years  | Exact location. Ana's intake office is one signature.                                                                                                               |
| `place_family`             | 2 years  | Coarse class. `office-bureaucratic-interior` cannot be the *primary* place 2 years running.                                                                         |
| `pov_gravity_well_id`      | 2 years  | The character whose decisions structure the chapter (not just whose POV scene appears most).                                                                        |
| `time_scale`               | 2 years  | One of: `single-hour-real-time`, `single-day`, `weeks-compressed`, `season`, `multi-year-flashforward`, `letter-from-future`, `historical-zoom`.                    |
| `plot_shape`               | 2 years  | One of: `decision-under-pressure`, `pursuit`, `arrival`, `departure`, `failure-and-its-aftermath`, `discovery`, `ambush`, `confession`, `negotiation`, `reckoning`. |
| `irreversible_event_types` | 2 years  | At least one event type each year must be one **not used in the last 2 years**. Caps the run from being all `decision-enacted`.                                     |


### 2.2 Where the constraint lives in the pipeline

- **Outline (06d)** receives `setting_ledger.json` and the cooldown table. It must pick a combination not in cooldown, OR include a `variance_override` block with a one-sentence justification. A variance override is permitted **at most once per 4 years**.
- **Code-side validator** rejects outlines that violate cooldowns without an override. This runs before the narrator is called, so we don't pay premium tokens on a doomed chapter.
- **Continuity pass (07b)** records the actual realised signature and writes it to `setting_ledger.json` after the chapter ships, regardless of what the outline declared. This catches the "outline said `season` but the chapter is one Tuesday" failure mode.

### 2.3 Forks must be staged where they happen

If the chosen fork's `actor` is not the chapter's `pov_gravity_well_id`, the beat sheet must include **at least one scene** in which:

- the POV is the fork's actor (or someone physically present at the irreversible act), AND
- the location is where the irreversible act takes place (not a phone call about it), AND
- the irreversible act itself, or its on-page consequence, happens in that scene.

Concretely: if the fork is "Omar deploys emergency rationing wells", the chapter cannot satisfy the irreversibility budget by having Omar phone Ana from the well station. It must **leave Ana's desk** for at least one scene at the well station, in Omar's POV. The continuity pass audits this with a new field `fork_staged_on_site: bool` and the code-side audit rejects `fork_staged_on_site: false` unless the fork's `actor` is the same character as `pov_gravity_well_id`.

### 2.4 Time-scale tools the narrator gets back

The current pipeline gives the narrator one register: real-time scene prose. v5 explicitly authorises five additional time-shapes the outline may pick, each with one usage rule:


| Time-shape                | What it is                                                        | Usage rule                                                                                    |
| ------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `season`                  | Chapter compresses 3–6 months into one continuous narrative voice | Must contain ≥ 1 dated event with a witnessed micro-scene inside it.                          |
| `multi-year-flashforward` | A short scene set 2–5 years after the chapter's "now"             | Must be marked as flashforward; must not contradict any future year's already-written state.  |
| `letter-from-future`      | One section narrated by a future, possibly unborn POV             | At most once per 5 years. Must end with the letter being received or destroyed in-narrative.  |
| `historical-zoom`         | Camera pulls out to summarise a movement / generation / region    | Capped at 25% of chapter words.                                                               |
| `dream-or-rumour`         | A scene flagged in-text as imagined / heard secondhand / dreamed  | Must end with a return-to-reality beat that registers what the dream/rumour cost or revealed. |


These exist as `time_shape` values in the outline schema; they are not metaphors. The narrator must execute the time-shape it picked.

---

## 3. Long-arc hooks — the run debt ledger

v4 plants and resolves hooks year-over-year. v5 turns the hook system
into a **debt ledger across the whole run** so the reader gets the
sense that something is being built toward, not just paid off next
quarter.

### 3.1 `debt_ledger.json` (new run-level artefact)

A flat list of every hook ever planted across the run, each with:

```json
{
  "hook_id": "october-backlog-vote",
  "planted_year": 2027,
  "planted_in_chapter": "monoscene/Ana-office",
  "ripens_by_year": 2028,
  "horizon_class": "near",          // near = +1, mid = +2..+4, long = +5..+7, decade = +8..+10
  "stake": "the corridor's legal capacity",
  "spine_act": 1,
  "spine_promise_claim": "act-1-corridor-improvised",
  "status": "advanced",             // open | advanced | resolved | reversed | abandoned
  "status_history": [...]
}
```

### 3.2 Per-year obligations against the ledger

Every beat sheet must:

- **Plant ≥ 1 long debt** (`horizon_class` in {`long`, `decade`}) per year. v4's "≥ 1 dramatic-seed" stays; v5 adds the long-horizon constraint on top.
- **Discharge or escalate ≥ 1 standing debt** of `horizon_class` ≥ `mid`. "Discharge" means status becomes `resolved` or `reversed` on-page; "escalate" means `advanced` *with cost paid by a named character*. A debt being merely re-mentioned does not count.
- **No more than 60% of debts may be `near`-horizon at any one time.** If the ledger tips toward all-near-term, the fork proposer prompt is augmented to bias toward forks that ripen long debts.

### 3.3 The fork proposer becomes ledger-aware

Today the fork proposer sees the previous year's hooks. In v5 it sees:

- the open debt ledger (with `horizon_class` flags)
- the spine's act and which act-promise lines are still unclaimed
- the cooldown table for `irreversible_event_types`

It must produce 3 forks that, **between them**, cover at least:

- one fork that ripens an existing **long** or **mid** debt (gives the run its "I planted that years ago" payoff)
- one fork that introduces a new horizon (creates a fresh long debt the chapter will plant)
- one fork in a domain not used in the last 2 years (v4's anti-lock-in rule, retained)

A fork that does none of those three is rejected at validation time and the proposer is re-run.

### 3.4 Spine binding

The decade spine's `acts[i].promise` is currently free-form prose. v5
requires it to be decomposed at seed time into **3–6 named promise
lines per act**, each a stageable obligation:

```json
{
  "act": 1,
  "name": "Paper and Pressure",
  "promise_lines": [
    {
      "id": "act-1-white-collar-collapse",
      "obligation": "Stage at least one chapter in which a named young white-collar worker loses their job, downgrades, or is replaced by an AI system on-page."
    },
    {
      "id": "act-1-aquifer-arithmetic",
      "obligation": "Stage at least one chapter at a water site (well, district office, irrigation valve) in which an allocation decision visibly reduces someone's access."
    },
    {
      "id": "act-1-corridor-improvised",
      "obligation": "Stage the corridor as a humane improvisation that has not yet been audited or hardened."
    }
  ]
}
```

Each year's beat sheet must declare `act_promise_claim`: which promise line it dramatises this year. The continuity pass audits whether the claim is realised on-page (a new `act_promise_realised: bool` field). At the act boundary (e.g. end of 2029), the run must show every act-1 promise line claimed and realised at least once. If any promise line is unclaimed by the act's last year, the next year's beat sheet is *forced* to claim it (this is the only mode where the system overrides outline freedom).

This is the lever that makes the spine matter. Without it, "white-collar collapse" and "aquifer arithmetic" remain texture in Ana's office. With it, at least one chapter must be at a well, and at least one chapter must dramatise a job being lost on-page.

---

## 4. Earned surprise — the rupture slot

The user-facing problem: chapters do exactly what the outline said
they would do, and the reader feels the rails. v5 adds a structured,
auditable slot for **the chapter doing something its outline did
not author**, drawn from a typed registry and authorised in advance.
This is not "let the narrator be creative." It is a separate stage
that injects a controlled disruption before the narrator runs.

### 4.1 Where it lives in the pipeline

A new stage, **06e — rupture authorisation**, runs between the chapter
outline (06d) and the narrator execute (06b → renumbered to 06f for
clarity). The rupture stage is a *cheap-tier* call. It receives:

- the chapter outline (06d)
- the beat sheet (06c)
- the debt ledger (open hooks, especially long-horizon ones)
- the side-cast register
- the run's prior `rupture_log.json` (cooldown memory)

It produces `06e_rupture.json`: at most one rupture per chapter, drawn
from the registry below, OR `null` if no rupture is authorised this
year (some years should be quiet).

### 4.2 Rupture registry


| Rupture type                    | What it does                                                                                                                                     | Constraint                                                                                                                        |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `withheld-information-revealed` | A character has been hiding something material; this chapter reveals it on-page.                                                                 | The hidden thing must be consistent with prior chapters (no retcon). The reveal must change at least one main's actions in-scene. |
| `side-character-takeover`       | A side-cast member named in a prior year hijacks a scene from the planned POV.                                                                   | The side character must be from `side_cast.json` with ≥ 2 prior appearances. Cannot be a character invented this chapter.         |
| `off-stage-rupture-on-stage`    | An event the world state has marked as off-page in prior years intrudes physically in the scene (the war reaches the kitchen).                   | The event must already exist in the state; this is staging, not invention.                                                        |
| `expected-outcome-reversed`     | The outline says X happens; the chapter delivers ¬X. The cost of the reversal must be paid on-page by the POV.                                   | At most once every 4 years. The continuity pass overrides v4's "events in beat sheet must occur" rule for this year only.         |
| `time-jump-mid-chapter`         | A scene break fast-forwards months or years inside the chapter.                                                                                  | Must be flagged in-text (a date, a witnessed gap). Cannot exceed `ripens_by_year` of any open near-debt without resolving it.     |
| `unscheduled-character-loss`    | A side-cast or minor main is lost (death, departure, defection, breakdown) without prior planting in this year's beat sheet.                     | Must affect at least one main's standing in subsequent years. Recorded in `cast.json` as a forced retirement reason.              |
| `rumour-or-omen`                | A scene of folk-rumour, dream, or omen that *turns out to be true* in a later year's chapter.                                                    | Plants a `decade`-class hook automatically. Cannot be used twice in any 5-year window.                                            |
| `genre-tilt`                    | One scene is rendered in a register the chapter mode forbids (a piece of song lyric, a recipe, a court transcript, a child's drawing described). | At most once every 3 years. Must be ≤ 250 words. Cannot replace a beat-sheet beat; it sits between two beats.                     |


### 4.3 What the rupture stage outputs

```json
{
  "year": 2029,
  "rupture": {
    "type": "side-character-takeover",
    "actor_id": "packet-clerk-rosa",
    "displaces_pov_in_beat": "named-family-at-the-door",
    "reason": "Rosa has appeared in 2027 and 2028 silently sorting packets; v5 promotes her to drive the family-at-the-desk beat from her POV, reframing Ana's authority as something Rosa enables and resents.",
    "expected_effect": "The reader sees the corridor's gatekeeping from below for the first time. Ana's filed standard reads differently when narrated by someone whose hands enact it.",
    "audit_signal": "If Rosa's POV does not actually carry ≥ 400 words of the beat, the rupture is recorded as `unrealised`."
  }
}
```

If `rupture` is `null`, the year is recorded as `quiet: true` in the
`rupture_log.json`. **Quiet years are positively valuable**; the
registry is not a quota. The cooldown rules below ensure ruptures do
not become the new monotone.

### 4.4 Frequency and pacing

- A run cannot have two consecutive ruptured years of the **same type**.
- A run cannot have ruptured years in 4 consecutive years (some years should be quiet so ruptures land).
- A run **must** have a rupture by year 4 of the run if none has fired before then. If the rupture stage returns `null` four years running, the next year's stage prompt is forced to authorise one.
- `expected-outcome-reversed` and `unscheduled-character-loss` are gated to ≤ 2 occurrences across the entire 10-year run, since they break v4's irreversibility/cast contracts.

### 4.5 The narrator's licence

The narrator (06f) receives both the outline (06d) and the rupture
(06e). Its instruction is: **execute the outline AND the rupture
together**. The rupture is binding, not optional. The continuity
pass audits whether the rupture's `audit_signal` was met; if not,
the chapter ships with `rupture_realised: false` and the rupture is
re-queued (not re-attempted automatically; just logged for the next
year's stage to consider).

The narrator is not given freelance creative licence. The narrator
is given **a second, smaller plan** that the outline did not see and
was not allowed to plan around. That asymmetry — outline did not get
to defuse the rupture — is what makes the chapter feel like
something happened that the system did not predict.

### 4.6 Why this is not just "let the model improvise"

Because the rupture is:

1. **Typed** — drawn from a fixed registry, not invented per chapter.
2. **Audited** — has an explicit `audit_signal` that the continuity pass checks.
3. **Cooldown-gated** — frequency caps prevent it from becoming a new template.
4. **State-bound** — most rupture types reference existing state (a side-cast member with appearances, an off-page event already in the world state, a long-horizon debt). The narrator can disrupt the chapter; it cannot conjure a UFO.
5. **Cost-paying** — every rupture type's contract names what cost it imposes on a main character or the world state. A free reveal is not allowed.

---

## 5. Continuity pass additions (07b)

In addition to v4's audits, v5's continuity pass emits:


| Field                          | Type   | Audited                                                                                               |
| ------------------------------ | ------ | ----------------------------------------------------------------------------------------------------- |
| `setting_ledger_compliance`    | object | Per axis (place / pov / time-scale / plot-shape / event-type), did this chapter respect the cooldown? |
| `fork_staged_on_site`          | bool   | Was the chosen fork's irreversible act staged where and by whom it happens, not via a phone call?     |
| `act_promise_claimed`          | string | Which act-promise line did this chapter claim?                                                        |
| `act_promise_realised`         | bool   | Did the rendered chapter actually dramatise the claim on-page?                                        |
| `debt_ledger_long_planted`     | int    | Count of new `long` or `decade` horizon hooks planted this year. Required ≥ 1.                        |
| `debt_ledger_discharged`       | array  | List of hook_ids whose status changed this year, with old/new status.                                 |
| `rupture_realised`             | bool   | If a rupture was authorised, did the prose actually deliver its `audit_signal`?                       |
| `irreversible_event_diversity` | bool   | Did this chapter use ≥ 1 event type not used in the last 2 years?                                     |


Code-side audit (`_audit_continuity_report` extension): if
`fork_staged_on_site` is false AND `pov_gravity_well_id != fork.actor`,
reject. If `act_promise_realised` is false AND the act has only one
year remaining, force the next year's beat sheet to claim the missed
promise. If `setting_ledger_compliance` shows two-axis cooldown
violations without a `variance_override`, reject.

One editor retry on fail; second failure ships with `degraded: true`
(consistent with v4 policy).

---

## 6. New / changed artefacts

```
runs/<run_id>/
  00_decade_spine.json          # CHANGED: acts now contain promise_lines[]
  setting_ledger.json           # NEW (v5): chapter-level place/pov/time/shape ledger
  debt_ledger.json              # NEW (v5): all hooks ever planted, with horizon and status
  rupture_log.json              # NEW (v5): per-year rupture record, including quiet years
  ...
  year_YYYY/
    06c_beat_sheet.json         # CHANGED: declares act_promise_claim,
                                #          requires ≥1 long-horizon hook in hooks_to_plant,
                                #          requires fork-on-site beat if fork.actor != pov_well
    06d_chapter_outline.json    # CHANGED: declares time_shape, place_signature, plot_shape
    06e_rupture.json            # NEW (v5): authorised rupture or null
    06f_story_draft.md          # RENUMBERED from 06_story_draft.md (was 06b in poc)
    07b_continuity_report.json  # CHANGED: v5 audit fields above
    09_readability.json         # CHANGED: includes time_shape_used, plot_shape_used,
                                #          long_debts_planted, debts_discharged, rupture_type
```

`replay.py` gets a new stage `--from-stage 06e` to re-run rupture +
narrator + editor + continuity pass. Stage 06e is also useful as a
standalone replay target: a designer can iterate on what kind of
rupture the year wanted without recomputing earlier stages.

---

## 7. Pipeline diff summary

```
v4:
  fork → specialists → state → summary → cross → cast → dossiers → beats
       → outline → narrator → editor → continuity → fork-proposer → readability

v5:
  fork → specialists → state → summary (anti-repetition memory of prior tensions)
       → cross
       → cast (reads side_cast promotion candidates)
       → dossiers
       → beats (claims an act_promise; plants ≥1 long-horizon hook;
                requires fork-on-site beat when fork.actor != pov_well)
       → outline (variance ledger + time_shape + plot_shape;
                  rejected by code if cooldowns violated without override)
       → rupture authorisation (NEW — typed, cooldown-gated, optional)
       → narrator (executes outline AND rupture)
       → editor (preserves rupture)
       → continuity (v4 audits + v5 audits above)
       → fork-proposer (debt-ledger aware; one fork must ripen a standing debt)
       → readability (v5 fields)
```

---

## 8. What v5 explicitly does not change

- v3's specialists / state merger / cross-interference rotation rules.
- v4's scene-craft contract (desire/obstacle/turn/cost/gesture/subtext). A scene is still a scene.
- v4's typed irreversibility budget. v5 adds a *diversity* rule on top; the budget itself stands.
- v4's slop ledger and staging ledger. v5 adds a setting ledger alongside them; the existing ledgers are not replaced.
- The cost target. v5 adds one cheap-tier stage (rupture authorisation) and a few code-side validators. Estimated added cost per year: < $0.02.

---

## 9. Migration

- v4 runs remain readable. New runs must satisfy v5 schemas.
- The decade spine's `promise` text in existing v4 runs gets a one-time migration script: feed each act's `promise` to a cheap-tier model with the prompt "decompose this paragraph into 3–6 stageable promise lines" and write the result back. Existing per-year beat sheets are left untouched; only new years claim against the decomposed promise lines.
- Existing hooks in `chapter_index.json` get a one-time migration to seed `debt_ledger.json`. Their `horizon_class` is computed from `ripens_by_year - planted_year`; statuses are inferred from prior continuity reports.
- `setting_ledger.json` is reconstructed from prior years by reading each year's outline (place / time-scale / etc.) and inferring missing fields.

---

## 10. Open questions

1. **Should `quiet: true` years be capped per run?** A run that ruptures every other year still feels patterned. Probably cap quiet streaks at 4 (no more than 4 quiet years in a row) and allow up to ~5 ruptured years in a 10-year run. Tune from data.
2. **Who runs the rupture stage — mid-tier or cheap-tier?** Cheap is the default. If ruptures consistently feel arbitrary or off-tone, promote to mid. The audit will tell us via `rupture_realised` rates.
3. **Does the rupture stage see the prose draft?** No. It runs *before* the narrator. If we let it see the draft, it becomes an editor pass and stops surprising the outline.
4. **Should the user (reader of the eventual web app) see ruptures marked?** No. The reader sees prose. The rupture log is internal.
5. **What about deliberate continuity breaks across forked branches?** Out of scope for v5; this is for the web-app phase where multiple readers fork the same node and the system must reconcile divergent state.

---

*v4 made each scene worth reading. v5 makes the year-to-year change worth following — by varying what's in the frame, by owing the future something concrete, by tying every chapter to the spine's specific promises, and by reserving room for the chapter to do something the outline did not know it would do.*