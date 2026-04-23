# Future Weavers v4 — Scene Depth + Dramatic Spine

> **Status (April 2026): implemented.** The v4 spec below has been wired
> into `poc/poc.py` and `poc/prompts.py`. The decade spine artefact
> (`00_decade_spine.json`) is generated once at seed time and injected
> into every per-year stage; chapter modes + scene-craft contracts +
> typed hooks + irreversibility budget + change audit + collision
> requirement + in-scene ratio are enforced by the continuity pass and
> its code-side audit. Side-cast register and staging ledger persist
> across years. v3 runs remain readable; new runs must satisfy v4
> schemas. See `poc/README.md` for the concrete pipeline map.
>
> v3 shipped a pipeline that reliably produces **thematically cohesive
> institutional reportage**. Chapters pass continuity checks, rotate
> palettes, cite hooks, and read like competent long-form journalism.
> They do not read like sci-fi epics.
>
> After reviewing run `20260423-122202` (years 2027 and 2028), two
> structural failures are obvious, and they compound over long runs:
>
> 1. **Scenes are too short to breathe.** Every "scene" is a 150–200
>   word captioned tableau. There is no room for desire → obstacle →
>    turn → cost inside any one scene. The prose reads like photo
>    captions, not fiction.
> 2. **The backbone is a thesis, not a dilemma.** The `central_tension`
>   and per-year hooks describe *conditions* ("growth has become
>    repair", "will the request be filed") rather than *wagers*. No
>    irreversible events. No reversals. No character change. Over ten
>    years the chapters iterate, they don't accumulate.
>
> v4 fixes both. The v3 scaffolding (specialists, summarizer,
> cross-interference, cast/dossier/beats, continuity pass) stays
> intact. What changes is the **scene economy**, the **dramatic
> contract**, and the **change audit**. The narrator gets more room
> and more responsibility; the outliner stops over-prescribing.

---

## 0. Critique of the v3 output (evidence-based)

Diagnoses observed in `runs/20260423-122202/year_2027/07_story_final.md`
and `year_2028/07_story_final.md`:


| v3 failure                                              | What the reader feels                                                                         | Root cause                                                                                                         |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| 7 dated scenes × ~170 words each                        | "A sequence of short paragraphs about different people I don't know."                         | `scene_budget ≥ N` rewards *scene count*, not *scene time*.                                                        |
| Main cast never share a meaningful scene                | "Parallel monologues, not a braid."                                                           | Beat sheet allows solo beats for all 5 mains with no collision requirement.                                        |
| No irreversible events in either year                   | "Nothing is happening."                                                                       | Hook schema tracks *admin requests*; continuity pass rewards "hook advanced", not "hook resolved with cost".       |
| Characters identical year over year                     | "These are the same paragraphs with different dates."                                         | `signature_object_or_place` + `signature_tic` are treated as stability, never flagged as staging slop.             |
| Every "world-beat" paragraph re-explains the summarizer | "The narrator keeps stopping to summarize."                                                   | `section_plan.scale: "world"` defaults to summary prose; no craft rule distinguishes it from `04_summary.json`.    |
| Register locked to forensic / reported                  | "Everything sounds like a wire service."                                                      | Palette rotates *within* a narrow institutional register. All 8 devices and 4 bases encourage detached prose.      |
| Forks propose *trends* not *events*                     | "The year doesn't start because something *happened*; it starts because a condition shifted." | Fork schema allows drasticness-level without requiring an *actor + act + stake*.                                   |
| Side characters disposable                              | "Ten names nobody carries."                                                                   | Side cast defined per-chapter, no persistence, no promotion path.                                                  |
| Dialogue absent or capped                               | "No one speaks to anyone."                                                                    | `exactly-three-quotations` and `no-direct-speech` devices systematically suppress it; no device *requires* speech. |
| Reader's compass produces theses                        | "The hook is a New Yorker subhead."                                                           | `hook` free-text field with no schema; LLM writes journalistic framing by default.                                 |


---

## 1. Core v4 principles (in addition to v3's five)

v3's five principles stand. v4 adds three:

1. **A scene is a lived unit.** If it doesn't have a desire, an
  obstacle, a turn, and a cost, it is not a scene — it is a beat
   note or a world paragraph. Chapters are built out of **few long
   scenes**, not many short ones.
2. **Each year must cost somebody something.** At least one
  irreversible event must occur or be ratified on-page per year:
   a decision enacted, a promise broken, a person lost, a capability
   fielded, a door closed. The continuity pass enforces this.
3. **The backbone is a dramatic wager, not a thematic frame.** The
  run commits early to a **decade spine** — a named dramatic
   question with stakes on both sides — and every year's fork must
   advance or complicate that wager.

---

## 2. Scene economy overhaul

The single biggest lever. Today's pipeline produces 6–7 short scenes
per chapter; v4 produces **1–3 developed scenes** plus optional short
connective tissue.

### 2.1 Chapter modes (replaces `structure` slot)

A chapter picks one of six **modes**. Each mode specifies scene count,
length distribution, and register expectations:


| Mode         | Scenes | Length distribution                                              | Example                                                                                                |
| ------------ | ------ | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `monoscene`  | 1      | 1800–2600 words in one location, one continuous time             | A single afternoon at Anjali's well-failure hearing; everything else is off-page.                      |
| `diptych`    | 2      | Two 900–1300 word scenes that mirror or collide                  | Maya's audit room + Leila's intake room, same hour, same proof-language, opposite institutional power. |
| `triptych`   | 3      | Three 600–900 word scenes with causal chain                      | A → B → C where A makes B possible and B forces C.                                                     |
| `long-march` | 1      | A single journey in 1800–2500 words, multiple locations, one POV | Rahul traveling to reconcile three schools in one day.                                                 |
| `overheard`  | 2–3    | Dialogue-forward; minimum 60% dialogue; 1500+ words              | Anjali and Rajiv arguing over a ration order; a parallel scene in the village.                         |
| `mosaic`     | 4–6    | Short dispatches, ≤300 words each                                | **Capped at 1 in every 4 years.** This is what v3 always produces.                                     |


- `mosaic` is what we have now. It gets a **hard frequency cap** so it can't be the default.
- Modes may not repeat within **2 years** (v3's structure-repeat rule extended).
- A mode picks allowable register ranges; a `monoscene` cannot ship without interiority; an `overheard` cannot ship without 3+ dialogue exchanges between main cast.

### 2.2 Scene craft contract

Every scene (not mosaic dispatch) must satisfy, verified in the
continuity pass:

- **Desire-in-moment** — what does the POV want in the next ten minutes? (distinct from year-want in dossier)
- **Obstacle-in-moment** — what specifically is in the way right now?
- **Turn** — a sentence-identifiable moment where information, balance, or understanding shifts.
- **Cost** — what the POV loses, accepts losing, or cannot unsay.
- **Embodied gesture** — at least one thing a body or hands do that *reveals* rather than stages. (Straightening paper stacks is a tic, not a gesture. A gesture is: Anjali signs the form she promised not to sign; Maya's hand stops halfway to the keyboard.)
- **Unresolved subtext** — one thing clearly unsaid that the reader can feel.The outline declares these per scene as a structured object:

```json
{
  "scene_id": "kanpur-early-trigger",
  "mode_role": "monoscene",
  "desire_in_moment": "Anjali wants Rajiv's signature before noon.",
  "obstacle_in_moment": "Rajiv has a call with the Chief Engineer at 11:45 and will use it to stall.",
  "turn": "Rajiv reaches for the form; Sushma coughs; Rajiv withdraws the pen.",
  "cost": "Anjali agrees to an informal supplementary clause she promised herself she would never sign.",
  "embodied_gesture": "She caps her own pen before he puts his down.",
  "subtext": "Both know Sushma is watching on behalf of the village association."
}
```

The narrator receives this contract; the continuity pass checks that
the turn, cost, and gesture are present in the rendered prose.

### 2.3 Retire the "≥N scenes, each with who/where/anchor/line" budget

Today's outline prescribes a thesis line per scene; the narrator then
paraphrases the thesis. Delete `line` from the scene schema. Keep
`anchor` but rename it `opening_image` and cap at 12 words (it should
seed a sensory entry, not summarize the scene). The narrator must
*find* what the scene is about while writing it.

### 2.4 Collision requirement

Any chapter with ≥3 main cast must include at least **one scene**
where **≥2 main cast members share the same space and both exercise
agency** (disagree, misunderstand, negotiate). Passive co-presence
(looking at the same map) does not count. Enforced by the continuity
pass.

### 2.5 In-scene / retrospective ratio

Hard rule measured post-edit: **≥65% of chapter words must be in
continuous present-tense scene** (a character doing something now in
one place), **≤35% retrospective/world/summary**. v3 runs at ~30 / 70.
The continuity pass counts words and rejects chapters that invert
the ratio.

---

## 3. Dramatic backbone overhaul

### 3.1 Decade spine (new top-level artifact)

At run start, after the seed bootstrap and founding cast, a new stage
emits `decade_spine.json`:

```json
{
  "spine_title": "The Reckoning of the Growth Machine",
  "dramatic_question": "Can the institutions built for expansion reinvent themselves into institutions of maintenance before the people inside them quit, riot, or are replaced?",
  "wager": {
    "if_yes": "A new legitimacy emerges from repair; a generation keeps its footing.",
    "if_no": "Parallel systems swallow the official ones; legitimacy migrates; the named protagonists lose their place."
  },
  "acts": [
    { "act": 1, "years": [2027, 2028, 2029], "role": "setup — the growth machine visibly strains; first irreversible casualties" },
    { "act": 2, "years": [2030, 2031, 2032, 2033], "role": "escalation — parallel systems form; defections begin; first betrayal" },
    { "act": 3, "years": [2034, 2035], "role": "reversal — the wager is decided; cost paid; a name survives, a name does not" }
  ],
  "countdown": "By end of act 2, at least one named main-cast member must have left the formal system they entered the story inside."
}
```

The spine is **visible to the fork proposer, outliner, and narrator**.
It is the first thing on every prompt. It gives the run a destination.

### 3.2 Per-year dramatic spine (replaces `central_tension`)

The summarizer stops writing `central_tension` as a sentence. Instead
it emits:

```json
{
  "year_dilemma": {
    "actor": "Anjali Mehta",
    "choice_a": "File the enforcement order and lose district funding for the next fiscal year.",
    "choice_b": "Sit on the data and watch three villages empty before the monsoon.",
    "stakes_a": "Her career and her water budget; the migrants she can't then house.",
    "stakes_b": "The three villages; her self-respect; her standing with Sushma."
  },
  "year_clock": "Monsoon onset, ~June 15. If no order is filed by May, enforcement cannot be operationalized in time.",
  "year_wager": "Whether a single administrator's paper trail can pre-empt a predictable collapse."
}
```

This structure forces a binary with costs on both sides, a time limit,
and a named risk. The outline echoes these; the beat sheet assigns the
dilemma to a POV; the narrator renders a scene in which the dilemma
faces the character.

### 3.3 Irreversibility budget

Each year must contain **≥1 irreversible event** — classified in one
of six types and audited by the continuity pass:


| Type                          | Example                                                          |
| ----------------------------- | ---------------------------------------------------------------- |
| `decision-enacted`            | Rajiv signs the order (or refuses it finally, on record)         |
| `relationship-shift`          | Sushma stops trusting Anjali; Daniels names Maya the scapegoat   |
| `world-fact-fielded`          | The first ration lock installed on a municipal line              |
| `loss`                        | A villager, a job, a tool, a binder, a reputation                |
| `defection`                   | Someone leaves the formal system for the parallel one            |
| `promotion-of-side-character` | A named side character gains status, becomes recurring main cast |


Off-page irreversibility counts **only if** the chapter includes an
on-page consequence of it. "The canal crisis escalated" does not
count; "Anjali spent an hour translating the canal order into her
own district's forms, and realized her early-trigger memo was now
moot" does.

### 3.4 Hook schema with quality classes

Replace free-text hooks with typed hooks:

```json
{
  "hook_id": "anjali-maya-cross-office",
  "type": "dramatic-seed",
  "subtype": "rivalry | promise | threat | discovery | debt",
  "planted_in_scene": "kanpur-early-trigger",
  "ripens_by_year": 2030,
  "stake": "If ripened: Anjali's proof-language infects Maya's firm's compliance framework; if not: the frameworks diverge and the protagonists lose shared ground."
}
```

Types:

- `dramatic-seed` — person / promise / threat / rivalry / discovery. **At least one per year; counts toward the ≥2 planted.**
- `world-seed` — a condition that will bite later.
- `admin-carry-over` — today's entire hook ledger. **Does NOT count toward ≥2 planted.** May appear as color, not as spine.

Hooks have `ripens_by_year`. The continuity pass can look back and
flag hooks that passed their ripen date without resolution — forcing
the outliner to resolve or retire them, not infinitely defer.

### 3.5 Character change audit

New per-character entry in the continuity report: `change_delta`.

```json
{
  "character_id": "maya-ramirez",
  "change_delta": {
    "belief": "stopped believing the firm will name her point person",
    "status": "unchanged",
    "relationship": "Daniels downgraded from ally to user",
    "body_or_position": "unchanged"
  },
  "change_verdict": "changed"
}
```

Rules:

- A character whose `change_verdict` is `unchanged` **three years in a
row** is automatically flagged for either (a) forced fork arc next
year, (b) demotion to side cast, or (c) retirement. The outliner
sees this flag and must act on it.
- The pass rejects chapters where all main cast are `unchanged`; at
least one must change each year.

---

## 4. Fork proposer: events, not trends

### 4.1 Fork schema (stricter)

```json
{
  "domain": "geopolitics",
  "title": "Anjali's Enforcement Memo Is Leaked to the Basin Authority",
  "fork_type": "event",
  "actor": "Sushma Verma (village representative)",
  "irreversible_act": "Passes the memo to the downstream basin authority's press officer",
  "named_stake": "Anjali's district career; cross-border treaty compliance; the village's legal standing",
  "clock": "14 days before the basin authority's quarterly press",
  "drasticness": "high"
}
```

`fork_type` must be one of:

- `event` — someone does something specific
- `technology-fielded` — a capability comes online somewhere concrete
- `person-enters` — a named side character steps into main cast
- `person-exits` — a named main leaves the formal system (defection / death / retirement)

`trend` is explicitly disallowed. "Procedural Realism becomes dominant
genre" is rejected by the validator.

### 4.2 Fork rooting in the decade spine

Each fork proposal must declare `spine_advances: "act_1_escalation"`
(or similar) AND `spine_wager_impact: "tips toward yes" / "tips toward no" / "raises stake on both sides"`. The fork proposer sees
the spine; the chooser sees the implication.

---

## 5. Register rotation (expand beyond wire-service)

### 5.1 New bases (additive)

Today's four bases (retrospective, dossier, reported, memoir) all
land in detached register. Add four:

- `close-third` — tight POV interiority, a body moving through a place
- `dialogue-scene` — conversation as primary engine
- `letter` — single voice writing to another named person
- `long-cam` — a single location observed across hours, many bodies passing through

New modulators (additive): `interior`, `domestic`, `bodily`,
`wry-spoken`, `angry`.

New devices (additive, and reshaped away from suppression):

- `one-scene-in-one-hour` — entire chapter spans ≤60 minutes of story time
- `two-voices-alternating` — dialogue-forward, no narrator summary
- `one-body-detail-per-paragraph` — forces embodiment
- `no-institution-named` — forces interiority; bans the words
"district", "firm", "clinic", "procurement"

Retire (or cap frequency to 1-in-4):

- `exactly-three-quotations`, `the-word-history-does-not-appear`, and
any device whose effect is *to suppress dialogue or interiority*.

### 5.2 Register budget across the decade

Over any rolling 5-year window, the palette chooser must pick:

- ≥1 year with a `close-third` or `dialogue-scene` base
- ≥1 year with a `monoscene` or `overheard` mode
- ≤2 years with `mosaic` mode

Enforced by code-side counter alongside existing freshness rules.

---

## 6. Staging slop ledger (new layer)

Today's slop ledger tracks phrases. Add a **staging ledger** tracking
recurring scene stagings per character:

```json
{
  "maya-ramirez": {
    "staging_used": [
      {"year": 2027, "stage": "vent-desk-printouts"},
      {"year": 2028, "stage": "vent-desk-printouts"}
    ],
    "cooldown_if_used_twice": true
  }
}
```

If a character's signature staging has appeared in the last 2 years,
the outliner must stage them elsewhere. Signature objects remain in
the dossier but the **compulsory placement** is dropped. Maya exists
outside the vent.

---

## 7. Side-cast persistence and promotion

### 7.1 Side-cast register

New artifact `side_cast.json` parallel to `cast.json`. Every named
side character enters here with:

```json
{
  "id": "sushma-verma",
  "first_seen": 2027,
  "appearances": [2027, 2028],
  "role_family": "village-representative",
  "promotable": true,
  "promotion_trigger": "If they take an irreversible act on-page against or with a main."
}
```

### 7.2 Promotion path

When a side character takes an irreversible act (see §3.3) they become
eligible for promotion to main cast next year. The cast-plan stage
sees promotable side characters; a promotion counts as the year's
"person-enters" event if chosen as a fork.

### 7.3 Throwaway budget

Each chapter may introduce **≤3 new named side characters**. Additional
bodies must be unnamed (villagers, clerks, the supervisor). This
prevents 2028's 10-named-side-cast sprawl.

---

## 8. Pipeline changes (shape)

v3's pipeline stays; these stages are modified or added:

```
SEED BOOTSTRAP + CAST BOOTSTRAP (v3)
         │
         ▼
[NEW] DECADE SPINE INIT          → decade_spine.json
         │
         ▼
per year:
  specialists (v3)
  state merger (v3)
  summarizer (v3, MODIFIED)       → year_dilemma + year_clock + year_wager
                                     replace central_tension
  cross-interference (v3)
  cast plan (v3, MODIFIED)        → sees character-change flags; must
                                     advance or retire unchanged mains
  dossiers (v3)
  beat sheet (v3, MODIFIED)       → assigns dilemma to POV; plants
                                     ≥1 dramatic-seed hook
  chapter outline (v3, MODIFIED)  → picks chapter MODE (not just
                                     structure); emits scene craft
                                     contract; no `line` per scene;
                                     staging-ledger-aware
  narrator execute (v3, MODIFIED) → receives scene contract + spine;
                                     free to discover inside the
                                     contract. Longer scenes, fewer.
  editor (v3)                     → preserves mode + contract
  continuity pass (v3, EXPANDED)  → audits:
                                     - in-scene/retro ratio
                                     - scene contract fidelity
                                     - collision (if applicable)
                                     - irreversibility budget
                                     - change-delta per main
                                     - hook typing
                                     - staging-ledger compliance
  fork proposer (v3, MODIFIED)    → fork_type ∈ {event, tech-fielded,
                                     person-enters, person-exits};
                                     spine-impact declared;
                                     trends rejected
```

---

## 9. Audit targets (what "good" looks like)

A v4 chapter, shipped clean, should pass:

- Mode ≠ `mosaic` **or** `mosaic` allowed by 4-year frequency cap
- ≥1 scene satisfies full scene contract (desire/obstacle/turn/cost/gesture/subtext)
- If ≥3 mains, ≥1 collision scene with 2+ mains exercising agency
- In-scene word share ≥65%
- ≥1 irreversible event on-page or on-page consequence of off-page
- ≥1 main cast member has `change_verdict: "changed"`
- ≥1 `dramatic-seed` hook planted
- No main cast member has `unchanged` for 3rd consecutive year
- No character staged in their signature location if used in last 2 years
- Fork proposed for next year declares `fork_type ∈ {event, tech-fielded, person-enters, person-exits}` and a spine-impact

A run of 10 years should, by construction, contain:

- ≥2 main-cast defections or retirements
- ≥3 side-cast promotions to main
- ≥1 `monoscene` chapter
- ≥1 `overheard` chapter
- ≤2 `mosaic` chapters
- A resolved decade-spine wager (yes / no / both) by end of act 3

---

## 10. What v4 does NOT change

- Specialists, state merger, summarizer facet shape, cross-interference analyst — unchanged.
- Dossier schema — unchanged.
- Slop ledger for phrases — unchanged (augmented by §6).
- Cast register, off-page tracking, anti-lock-in fork rule — unchanged.
- Tiering (cheap specialists, mid outliner + auditor, premium narrator + editor) — unchanged.
- Per-year cost target — roughly flat; narrator runs longer but
outline is leaner.

---

## 11. Open questions for discussion

1. **Does the decade spine lock the run too early?** Alternative: spine is declared at year 3 after the world has settled, and acts are re-planned at year 6. Tradeoff: less destination, more responsiveness.
2. **Who authors the year_dilemma — summarizer or a new stage?** Summarizer currently writes facet-balanced summary; dilemma-writing is a different craft. May want a dedicated mid-tier `dramatist` stage between summarizer and cast plan.
3. **How strict should mode frequency caps be?** `mosaic` ≤ 1 in 4 feels right. `monoscene` mandatory ≥ 1 in 5? Or soft-preferred?
4. **Collision requirement — always, or only for chapters with ≥3 mains?** Current draft: only with ≥3. Could strengthen to: always ≥2 mains in a scene, which would force fewer-POV chapters.
5. **In-scene ratio of 65% — feasible on first try, or ramp?** May need to ramp: 55% year 1, 60% year 2, 65% year 3+, so the narrator isn't blocked by a hard fail on a model that tends toward summary.
6. **Do we keep the thematic hooks for flavor?** Proposal: yes, as `admin-carry-over` and `world-seed` types, but they don't count toward the planted quota.
7. **Retiring the `line` field per scene — does the narrator lose the target image?** Alternative: keep `opening_image` and `line_of_subtext` (a line the scene *implies*, not a thesis line).

---

## 12. Minimum viable v4 (if you want to stage it)

If full v4 is too much in one pass, stage it:

- **v4.0 — scene economy only.** Add chapter modes; cap mosaic frequency; add scene contract (desire/obstacle/turn/cost); add in-scene ratio audit. No spine yet. This alone should change how chapters *read*.
- **v4.1 — spine + dilemma.** Add decade spine; replace central_tension with year_dilemma/clock/wager; fork schema tightened. This changes what chapters are *about*.
- **v4.2 — change audit + persistence.** Character change-delta; side-cast register + promotion; staging ledger; irreversibility budget. This changes how chapters *accumulate*.

v4.0 is the one that directly addresses "I think we need to extend
the narration atoms." v4.1 directly addresses "the backbone needs to
be more enticing." v4.2 is what makes a long run feel like an epic
rather than a ten-year iteration of the same chapter.