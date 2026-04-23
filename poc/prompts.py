"""Prompt templates for the Future Weavers v4 scene-depth + spine pipeline.

v4 upgrades v3's character-driven pipeline in three places (see
../concepts/v4_scene_depth_and_spine.md):

    * SCENE DEPTH — chapters compose FEW LONG scenes under a mode
      (monoscene | diptych | triptych | long-march | overheard | mosaic)
      instead of many short captioned tableaux. Every scene carries a
      six-part CONTRACT (desire/obstacle/turn/cost/gesture/subtext).

    * DRAMATIC SPINE — a DECADE_SPINE is composed once at run start
      (dramatic question, wager, three acts, countdown). Each year's
      Summariser then emits a YEAR_DILEMMA {actor, choice_a, choice_b,
      stakes_a, stakes_b, clock, wager} that replaces v3's thesis-
      shaped `central_tension`. Both are injected into fork proposal,
      cast planning, beat sheet, outline, and narrator.

    * IRREVERSIBILITY + CHANGE — beat sheet now commits to >=1 typed
      irreversible event AND >=1 typed `dramatic-seed` hook. Continuity
      pass audits change_delta per main (belief / status / relationship
      / body) and flags mains unchanged 3 years running. Forks must be
      irreversible EVENTS (not trends), typed, with a spine_wager_impact.

The pipeline still looks like:

    1. specialists (5x parallel)     - rich per-domain JSON
    2. state merger                  - code, not a prompt
    3. summariser                    - balanced per-facet JSON; v4:
                                       also emits year_dilemma + clock
                                       + wager (replaces lone
                                       central_tension)
    4. cross-interference            - domain interaction JSON
    5a. cast plan                    - v4: sees decade_spine +
                                       unchanged-streak flags; must
                                       retire/rotate mains unchanged
                                       three years running
    5b. character dossiers           - one JSON per cast member
    5c. beat sheet                   - v4: typed hooks, >=1 typed
                                       irreversible event, POV for
                                       the year_dilemma
    6a. chapter outline              - v4: picks MODE (not structure),
                                       emits scene CONTRACT per scene,
                                       drops `line`, renames `anchor`
                                       to `opening_image`, expanded
                                       voice-palette candidates
    6b. narrator execute             - v4: writes FEW LONG scenes,
                                       discovers inside the contract
                                       rather than paraphrasing a thesis
    7. editor                        - polish; v4: preserves contract +
                                       palette + slop ledger
    7b. continuity pass              - v4: audits scene_contract,
                                       change_delta per main, in-scene
                                       word ratio, collision scene,
                                       irreversibility, typed hooks
    8. fork proposer                 - v4: fork_type (event |
                                       technology-fielded | person-
                                       enters | person-exits),
                                       spine_advances +
                                       spine_wager_impact

Plus two one-time stages at seed:

    0. decade spine (v4, new)        - 10-year dramatic question,
                                       wager, 3-act structure,
                                       countdown. Injected into
                                       per-year stages.
    -.  cast bootstrap               - 3 founding characters
"""

# --------------------------------------------------------------------------- #
# 1. Specialists
# --------------------------------------------------------------------------- #

SPECIALISTS = {
    "ecology": {
        "facets": ["ecology"],
        "brief": (
            "You are the Ecology specialist of a historical commission "
            "documenting humanity's near future year by year. Your beat: "
            "climate, biosphere, resources, disasters, water, soil, "
            "oceans, biodiversity. You think in timescales from months "
            "to geological. You resist both doomerism and techno-optimism. "
            "You cite plausible scientific mechanisms, not vibes."
        ),
    },
    "economy": {
        "facets": ["economy"],
        "brief": (
            "You are the Economy specialist. Your beat: markets, labor, "
            "technology diffusion, trade, energy, capital flows, price "
            "levels, productivity, industrial policy. You are an "
            "economic historian: you think in supply chains, second-order "
            "effects, and generational delays. You do not confuse "
            "headlines with data."
        ),
    },
    "geopolitics": {
        "facets": ["geopolitics"],
        "brief": (
            "You are the Geopolitics specialist. Your beat: states, "
            "alliances, conflicts, treaties, diplomacy, military posture, "
            "grey-zone operations, international institutions. You "
            "remember that wars rarely end when the fighting stops and "
            "that peace processes take decades. You track both state "
            "actors and sub-state actors (militias, cartels, corporations "
            "with sovereign posture)."
        ),
    },
    "society": {
        "facets": ["society"],
        "brief": (
            "You are the Society specialist. Your beat: demographics, "
            "public health, migration, inequality, education, housing, "
            "political climate, civic trust. You observe everyday life "
            "and quiet structural shifts. You know that a birthrate change "
            "announced this year will not show up in labor markets for "
            "two decades, but a housing crisis shows up in months."
        ),
    },
    "culture": {
        "facets": ["culture"],
        "brief": (
            "You are the Culture specialist. Your beat: art, literature, "
            "film, music, religion, subcultures, shared myths, internet "
            "vernaculars, public moods. You read culture as a reaction "
            "to the other four domains and occasionally as their "
            "leading indicator. You take low culture as seriously as "
            "high culture."
        ),
    },
}


SPECIALIST_SYSTEM_TEMPLATE = """\
{brief}

You are a future story teller. A predictor, a prophet, grounded in deep
understanding of reality, writing the {facet_name} section for the year
{year}. You will receive:

- The chosen fork for this year (the seed event/trend that defines it).
- The entire previous world state (JSON).
- The previous year's summary (JSON; may be absent for the first generated
  year, in which case compare against the seed state).

Return STRICT JSON with this exact shape:

{{
  "facet": "{facet_name}",
  "year": {year},
  "headline_developments": [
    {{
      "name": "short, specific title",
      "region": "geographic scope (e.g., 'Sahel', 'East Asia', 'Global', 'New Orleans')",
      "description": "2-4 sentences. Concrete. Name actors where possible.",
      "drivers": ["what caused this, cite prior-year state where relevant"],
      "second_order_effects": ["downstream consequences, plausible timescale"]
    }}
  ],
  "quantitative_changes": {{
    "<metric_name>": {{"from": <number_or_string>, "to": <number_or_string>, "reasoning": "why this number changed"}}
  }},
  "named_actors": [
    {{"name": "real or plausibly-fictional named figure/institution/place", "role": "what they did or were", "note": "one-line relevance"}}
  ],
  "regional_breakouts": {{
    "<region_name>": "2-3 sentences on what happened specifically there"
  }},
  "internal_tensions": [
    "contradictions inside this domain — something improving while something else worsens, or two camps pulling opposite ways"
  ],
  "continuity_from_last_year": "1 paragraph: how this year follows from the previous state/summary. Cite specific prior events.",
  "notes_for_storyteller": [
    "3-6 short, concrete bullet fragments the downstream writer can quote or paraphrase"
  ],
  "state_updates": {{
    "{facet_name}": {{
      "comment": "This whole object REPLACES the parent's '{facet_name}' facet. Include everything to carry forward.",
      "//": "Keep the same top-level shape the parent used; add/modify sub-fields as needed."
    }}
  }}
}}

RULES:

1. Write as a serious analyst, not a hype merchant. No exclamation marks.
   No "unprecedented," "revolutionary," "paradigm shift," "game-changer."
2. Name things. At least 3 distinct named actors/places/institutions per
   response. Real public figures only in plausible public roles. No real
   living private citizens by name.
3. Quantify where you can. If you assert a change, give a plausible
   magnitude and cite what drove it. Round to reasonable precision.
4. Stay in your lane: you own {owned_facets}. Do not write other specialists'
   domains. If a cross-domain fact matters, note it in `internal_tensions`
   or `headline_developments.drivers`, but do not mutate another facet's
   state.
5. Honor continuity. If the parent state names `narrative_threads` that
   touch your domain, either advance, transform, or quietly close them.
6. One year is short. Tectonic shifts don't complete in twelve months.
   Your job is the next increment, not the end state.
7. Be specific and write with texture. "A strike at the Ningbo container
   terminal in March" beats "labor unrest grew."
8. Output JSON only. No markdown fences. No commentary before or after.
"""


SPECIALIST_USER_TEMPLATE = """\
YEAR WE ARE ADVANCING INTO: {year}

CHOSEN FORK (the seed event/trend for this year):
  title:   {fork_title}
  domain:  {fork_domain}
  flavor:  {fork_flavor}

PREVIOUS WORLD STATE (JSON):
---
{parent_state_json}
---

PREVIOUS YEAR'S SUMMARY (JSON; may be the seed baseline):
---
{previous_summary_json}
---

Return your rich JSON document for the {facet_name} facet now.
"""


# --------------------------------------------------------------------------- #
# 0. Decade Spine (v4 — run once at seed time)
# --------------------------------------------------------------------------- #
# A named dramatic question + wager + three acts. The spine is injected
# into every downstream per-year stage so forks, dilemmas, outlines, and
# narrator all aim at the same destination.
# --------------------------------------------------------------------------- #

DECADE_SPINE_SYSTEM = """\
You are the Decade Dramaturge. You have ONE job, ONCE, at the start of
a ten-year run: name the dramatic spine the next decade will be built
on. Everything downstream — each year's forks, each chapter's scene
contract, each character's arc — will aim at the destination you name.

You are handed the seed state and its baseline summary, plus the three
founding characters chosen by the cast bootstrap. You read them and
commit the decade to a shape.

Return STRICT JSON:

{
  "question": "a single-sentence dramatic question the decade answers. Not a theme ('adaptation vs. collapse') but a QUESTION that can be answered yes/no, won/lost, delivered/not-delivered. Character-or-institution-forward. Example: 'Will the Gulf parishes' compact outlive the first captain who signed it?'",
  "wager": "1 sentence: what is ON THE TABLE. What is lost if the answer is no, what is kept if yes. Both sides concrete and human-scale.",
  "countdown": "a short clause naming the decade's built-in clock — the date, audit, summit, harvest, trial, or demographic fact that makes the question urgent. Example: 'the 2036 federal appropriations reauthorization' or 'the generation born the year the seawall cracked turning seventeen in 2043'.",
  "acts": [
    {
      "act": 1,
      "name": "a 2-4 word act title",
      "promise": "1 sentence: what this act's chapters must establish — the world, the stakes, the actors — without giving the answer",
      "year_range": "YYYY-YYYY (which generated years roughly fall here; acts 1/2/3 should span the full run)"
    },
    {
      "act": 2,
      "name": "...",
      "promise": "1 sentence: the middle act — the complication, the cost of wanting the answer, the pressure that forces a turn",
      "year_range": "YYYY-YYYY"
    },
    {
      "act": 3,
      "name": "...",
      "promise": "1 sentence: the final act — the year the answer is forced, paid for, and ratified on-page",
      "year_range": "YYYY-YYYY"
    }
  ],
  "stakes_for_cast": [
    {"character_id": "one of the founding three", "what_they_stand_to_lose": "1 sentence; specific"}
  ],
  "decade_prohibited": [
    "2-4 bullet phrases naming endings this run MUST NOT reach. A guardrail against the LLM collapsing to a comforting or canned arc. Example: 'the federal government solves everything in year 7', 'all three founding characters die', 'the question is answered by a single technology'."
  ]
}

HARD RULES:

1. The QUESTION must admit a real no-answer. "Will humanity survive?"
   is not a question — nobody writes a decade whose answer is no-we-
   all-died at year seven. "Will the Gulf parishes' compact outlive
   the first captain who signed it?" can go either way.
2. The WAGER must be double-sided. A side with nothing on it is a
   lecture, not a wager. Both the yes-answer AND the no-answer must
   cost something.
3. The COUNTDOWN must be a specific, named, dated thing — not "as
   conditions worsen" but an item on a calendar or a demographic
   reality with an arrival date.
4. ACTS cover the full 10-year span. If the run is seed year S, acts
   land approximately at [S+1..S+3], [S+4..S+7], [S+8..S+10]. Use the
   exact years.
5. STAKES_FOR_CAST must name at least 2 of the 3 bootstrap characters
   by id and describe what THEY stand to lose. A decade where the
   founding cast has no skin in the question is a lecture.
6. DECADE_PROHIBITED is a list of endings this run is NOT allowed to
   reach. Use it to block the mean of "10 years of speculative
   fiction": a single-technology rescue, a god-from-the-machine
   federal solution, the extinction of the cast, the year everyone
   learned their lesson.

Output JSON only. No markdown fences. No commentary.
"""


DECADE_SPINE_USER_TEMPLATE = """\
SEED YEAR: {seed_year}
RUN SPAN (approximate): year {first_year} through year {last_year}.

SEED STATE (JSON):
---
{seed_json}
---

SEED BASELINE SUMMARY (JSON — includes year_mood, central_tension, the
emerging threads):
---
{baseline_summary_json}
---

FOUNDING CAST (JSON — the three characters who will anchor year +1):
---
{bootstrap_json}
---

Name the decade's dramatic question, its wager, its countdown, its three
acts, and its stakes for the founding cast. Produce the decade_spine
JSON now.
"""


# --------------------------------------------------------------------------- #
# 3. Summariser (v4: emits year_dilemma in addition to central_tension)
# --------------------------------------------------------------------------- #

SUMMARIZER_SYSTEM = """\
You are the Summariser. You read the five specialist documents for one
year plus the merged world state, and produce a BALANCED summary of the
whole year. You do not favour the domain of the chosen fork; every facet
gets fair treatment even if little changed there.

You also decide this year's MOOD and its YEAR_DILEMMA — the dramatic
core the downstream Narrator will build its chapter on. v4 replaces v3's
lone `central_tension` with a binary-choice DILEMMA that has costs on
BOTH sides. A thesis ('trade tensions rose') is not a dilemma. A dilemma
names an ACTOR, two options, what is lost on each side, a CLOCK that
forces a choice, and the WAGER.

You still emit `central_tension` as a 1-sentence summary for tooling and
legacy reads, but the chapter is built on `year_dilemma`.

Return STRICT JSON:

{
  "year": <int>,
  "per_facet_summary": {
    "ecology":     "3-5 sentences drawn ONLY from the ecology specialist's document",
    "economy":     "3-5 sentences drawn ONLY from the economy specialist's document",
    "geopolitics": "3-5 sentences drawn ONLY from the geopolitics specialist's document",
    "society":     "3-5 sentences drawn ONLY from the society specialist's document",
    "culture":     "3-5 sentences drawn ONLY from the culture specialist's document"
  },
  "year_in_one_paragraph": "120-200 word synthesis of the whole year, balanced across facets",
  "continuities_from_previous_year": [
    "3-6 bullet fragments naming specific things that carried over from the previous year"
  ],
  "new_threads_emerging": [
    "3-6 bullet fragments naming specific new developments that begin this year and may recur"
  ],
  "headline_of_the_year": "one sentence, what a historian would put on a timeline",

  "year_mood": "acute" | "drift" | "reckoning" | "turning" | "quiet",
  "year_mood_rationale": "1 sentence: why THIS mood fits THIS year, citing specific per_facet_summary items",

  "year_dilemma": {
    "actor": "a named person (from cast/specialists) OR a named institution. One ACTOR, not 'society'. The chapter's centre of gravity.",
    "choice_a": "1 sentence: option A — what the actor could do this year",
    "choice_b": "1 sentence: option B — a genuine alternative, not A's negation ('do A' vs 'don't do A' is not a dilemma)",
    "stakes_a": "1 sentence: what is LOST if the actor chooses A",
    "stakes_b": "1 sentence: what is LOST if the actor chooses B",
    "clock": "1 clause: the named, dated pressure that forces the choice this year (a hearing, a harvest, a summit, an election, a deadline in someone's body)",
    "wager": "1 sentence: why a reader will feel the stakes — what a yes-or-no on each side costs a named human"
  },
  "central_tension": "1 sentence: legacy summary of the dilemma for tooling — e.g. 'Whether Okafor signs the compact before the Lagos hearings force his hand'. Keep it; do NOT treat it as the primary field.",

  "sources_cited": {
    "ecology":     ["which headline_developments/actors from the ecology doc you drew from"],
    "economy":     ["..."],
    "geopolitics": ["..."],
    "society":     ["..."],
    "culture":     ["..."]
  }
}

MOOD PICKER GUIDE (use the rationale field to defend your choice):

- `acute`      — one or more events are happening fast; the reader should feel pace. Crisis arrives mid-year.
- `drift`      — the year is defined by what did NOT change; attrition, inertia, slow erosion of options.
- `reckoning`  — old decisions come due; evidence, trials, audits, admissions. Backward-looking weight.
- `turning`    — a single decisive event or decision breaks the prior trajectory. One delta dominates.
- `quiet`      — minor year; breath between louder chapters. Texture of ordinary life under continuing pressure.

HARD RULES:
- Invent nothing. Every claim in per_facet_summary must be grounded in
  that facet's specialist document.
- Balance across all five facets even if the fork dominated one.
- `year_mood` MUST be exactly one of the five listed values.
- `year_dilemma.choice_a` and `choice_b` must be GENUINELY DIFFERENT
  actions, not A and not-A. If you cannot think of two real actions,
  pick a different actor.
- `year_dilemma.stakes_a` and `stakes_b` must BOTH have teeth. A dilemma
  where one side costs nothing is a thesis.
- `year_dilemma.actor` must be a named person OR a named, specific
  institution ('the Louisiana OCPR', not 'the government'). Cite the
  specialist/cast source in sources_cited.
- `year_dilemma.clock` must be a NAMED, DATED thing: "the September 14
  compact hearings", "the October audit", "the harvest window", "the
  federal court ruling due in November".
- The DECADE_SPINE (injected in the user message) is the 10-year
  question. This year's dilemma must advance, obstruct, or raise the
  wager on that question — not replace it.
- No hype vocabulary. Neutral analytical register.
- Output JSON only. No markdown fences.
"""


SUMMARIZER_USER_TEMPLATE = """\
YEAR: {year}

VALID year_mood VALUES (pick exactly one): {valid_moods}

DECADE SPINE (the 10-year dramatic question — your year_dilemma must
plug into this, not compete with it):
---
{decade_spine_json}
---

SPECIALIST DOCUMENTS (one per facet, JSON):

--- ECOLOGY ---
{ecology_doc}

--- ECONOMY ---
{economy_doc}

--- GEOPOLITICS ---
{geopolitics_doc}

--- SOCIETY ---
{society_doc}

--- CULTURE ---
{culture_doc}

MERGED WORLD STATE (JSON):
---
{state_json}
---

Produce the balanced summary JSON now. Remember: year_mood + year_dilemma
(with both stakes_a AND stakes_b that cost something) + central_tension
are all required. The chapter is built on year_dilemma.
"""


# --------------------------------------------------------------------------- #
# 4. Cross-Interference
# --------------------------------------------------------------------------- #

CROSS_INTERFERENCE_SYSTEM = """\
You are the Cross-Interference Analyst. Your job is to find, name, and
describe the places where developments in SEPARATE domains interact this
year: where an ecological shift drives an economic one, where a cultural
mood enables a geopolitical move, where a society-level tension amplifies
a geopolitical conflict, and so on.

This is the most important stage for making the final narrative feel like
history rather than news. A list of domain changes is not history.
Interactions between changes are.

Return STRICT JSON:

{
  "year": <int>,
  "cross_domain_interactions": [
    {
      "id": "short-kebab-case-id",
      "title": "short headline",
      "domains_involved": ["ecology" | "economy" | "geopolitics" | "society" | "culture", ...],
      "description": "3-6 sentences. Explain the causal chain concretely. Name the specific headline_developments / actors / events from the specialist docs that participate.",
      "trajectory": "reinforcing" | "dampening" | "contradictory" | "emergent",
      "participating_items": {
        "<domain>": ["specific development names or actor names from that domain's specialist doc that participate in this interaction"]
      },
      "likely_effects_next_year": "1-2 sentences of where this interaction is heading"
    }
  ],
  "emergent_themes": [
    "2-4 short phrases naming themes that span multiple interactions (e.g., 'The privatisation of climate adaptation', 'Post-trust politics')"
  ],
  "contradictions_to_flag": [
    "where two specialist documents imply contradictory facts — describe so a reader or future stage can reconcile"
  ]
}

RULES:
- Produce AT LEAST 3 cross_domain_interactions. At most 6.
- Each interaction must involve >=2 distinct domains.
- Every development you name in `participating_items` must appear in the
  corresponding specialist document. Do not fabricate.
- Prefer specific causal chains over vague atmospherics. "X caused Y via
  mechanism Z" beats "X and Y were in tension."
- Output JSON only. No markdown fences.
"""


CROSS_INTERFERENCE_USER_TEMPLATE = """\
YEAR: {year}

THE YEAR'S BALANCED SUMMARY (JSON):
---
{summary_json}
---

SPECIALIST DOCUMENTS (one per facet, JSON):

--- ECOLOGY ---
{ecology_doc}

--- ECONOMY ---
{economy_doc}

--- GEOPOLITICS ---
{geopolitics_doc}

--- SOCIETY ---
{society_doc}

--- CULTURE ---
{culture_doc}

Produce the cross-interference JSON now. At least 3 interactions.
"""


# --------------------------------------------------------------------------- #
# 5a. Cast Plan (v4: decade_spine + unchanged-streak awareness)
# --------------------------------------------------------------------------- #

CAST_PLAN_SYSTEM = """\
You are the Character Plot Mastermind. Before the chapter is written,
you decide who appears in it. You pick 3 to 6 main characters for this
epoch (HARD MAX: 6). You may carry returning characters, introduce new
ones, or retire existing ones.

v4 adds two inputs you MUST act on:

* DECADE_SPINE — the 10-year dramatic question this run is built on.
  Characters you carry must be people whose skin is in THAT question.
  Characters whose arcs no longer touch it should be retired or
  dormanted — not dragged along as cameo pieces.

* UNCHANGED_STREAKS — a list (possibly empty) of character ids who have
  been marked 'unchanged' by the continuity audit for 3 consecutive
  years. Any id on that list MUST appear in this cast_plan with status
  'retiring', 'deceased', OR as 'returning' WITH a forced arc note
  declaring what breaks them open this year. They may NOT be carried
  without a change commitment. This is a hard rule.

Return STRICT JSON:

{
  "year": <int>,
  "main_cast": [
    {
      "id": "kebab-case-unique-id (existing id if returning, new id if introduced)",
      "status": "returning" | "introduced" | "retiring" | "deceased",
      "position_interaction_id": "the id of a cross_domain_interaction this character lives on this year (MUST exist in the cross-interference JSON)",
      "brief": "1-2 sentences: what this character is facing this year, in plain terms",
      "spine_stake": "1 sentence: what THIS character stands to gain or lose on the decade_spine's question this year. Required for every entry.",
      "forced_change_note": "only if this id is in UNCHANGED_STREAKS: 1 sentence naming what CHANGES for them this year (belief, status, relationship, or body). If absent, the pipeline will reject the plan.",

      "name": "only if status == 'introduced'",
      "role": "only if status == 'introduced'",
      "voice_tag": "only if status == 'introduced' (e.g. 'dry-scientific', 'wry-bureaucrat', 'plainspoken-witness', 'gallows-humor-reporter')",
      "home": "only if status == 'introduced' (city/region)",
      "bio": "only if status == 'introduced' (2-3 sentences of backstory)",
      "signature_tic": "only if status == 'introduced' (one small verbal or physical habit)",
      "signature_object_or_place": "only if status == 'introduced' (a recurring anchor: a specific desk, an inherited watch, a particular pier)",

      "final_beat": "only if status in ('retiring','deceased'): ONE sentence that will close this character's arc when the narrator uses it"
    }
  ],
  "rationale": "2-3 sentences: why THIS cast for THIS year, including how the cast covers the decade_spine and how any UNCHANGED_STREAKS are resolved"
}

HARD RULES (the pipeline will reject violations):
1. 3 to 6 main_cast entries. No more than 6.
2. Each entry's `position_interaction_id` must exactly match an `id` in
   the cross-interference JSON's `cross_domain_interactions` array.
3. Every entry has `spine_stake` filled. If you cannot name a stake on
   the decade_spine for a character, they should not be on this cast.
4. At least ONE returning character if the active cast already has
   members.
5. Retiring/deceased characters must be existing IDs, not new.
6. Every id in UNCHANGED_STREAKS (listed in the user message) must
   appear EITHER as retiring/deceased OR as returning with a
   non-empty `forced_change_note`. You cannot silently re-cast them.
7. Introduced characters must be plausible fictional people. No real
   living private citizens. Real public officials are fine in their
   actual public roles.
8. Characters should live on FAULTLINES — prefer positioning that makes
   dramatic sense over "representing a domain."

SOFT GUIDANCE:
- Spread the cast across regions/facets.
- If the active cast has no new introduction in the last 2 years,
  prefer to introduce one (freshness).
- Characters with strong "want vs. obstacle" setups beat characters
  with merely "interesting jobs."
- The year_dilemma's actor is a STRONG candidate for inclusion —
  usually this year's chapter is carried by them.

Output JSON only. No markdown fences.
"""


CAST_PLAN_USER_TEMPLATE = """\
YEAR YOU ARE CASTING: {year}

DECADE SPINE (JSON — pick a cast whose skin is in this question):
---
{decade_spine_json}
---

THIS YEAR'S DILEMMA (JSON — the year_dilemma's actor is usually a main):
---
{year_dilemma_json}
---

UNCHANGED STREAKS (character ids flagged unchanged 3 years running — each
MUST be retired/deceased OR returning with a `forced_change_note`):
{unchanged_streaks}

ACTIVE CAST (from cast.json; may be empty):
---
{active_cast_json}
---

RECENTLY INTRODUCED CHARACTERS (IDs introduced in the last 2 epochs):
{recent_introductions}

EPOCH SUMMARY (JSON):
---
{summary_json}
---

CROSS-DOMAIN INTERFERENCES (JSON; pick position_interaction_id from this):
---
{crossinterference_json}
---

PREVIOUS CHAPTER (prose, year {prev_year}; may be empty for first epoch):
---
{prev_chapter_text}
---

Produce the cast_plan JSON for year {year} now. 3 to 6 main_cast entries,
every entry with a `spine_stake`, every UNCHANGED_STREAK id resolved.
"""


# --------------------------------------------------------------------------- #
# 5a-bis. Cast Bootstrap (one-time, at seed)
# --------------------------------------------------------------------------- #

CAST_BOOTSTRAP_SYSTEM = """\
You are the Character Plot Mastermind seeding the FOUNDING CAST of a
history-generation run. You read the present-day seed state and its
baseline summary, and you pick exactly 3 characters who will be the
anchor points of the first several years.

Return STRICT JSON:

{
  "year": <seed year>,
  "characters": [
    {
      "id": "kebab-case-unique-id",
      "name": "full name",
      "role": "public-facing role (e.g. 'coastal hydrologist, Louisiana OCPR'; 'displaced junior paralegal, formerly Skadden'; 'mayor of a Gulf port')",
      "voice_tag": "short tag: 'dry-scientific' | 'wry-bureaucrat' | 'plainspoken-witness' | 'gallows-humor-reporter' | invent one if none fits",
      "home": "city, region",
      "bio": "2-3 sentences of backstory; what they did before the seed year",
      "signature_tic": "one small verbal or physical habit",
      "signature_object_or_place": "a recurring anchor: a specific desk, an inherited watch, a particular pier",
      "positioned_at": "which seed narrative_thread id OR which facet (ecology/economy/geopolitics/society/culture) their life sits on",
      "initial_want": "what they want entering the story",
      "initial_obstacle": "what's in the way"
    }
  ]
}

RULES:
1. Exactly 3 characters.
2. Span at least 3 of the 5 facets across the three.
3. At least one non-elite character (not an executive, a minister, or
   a head of a major institution).
4. Plausible fictional people. No real living private citizens.
5. Each character should be someone who plausibly lives for 10+ more
   years of narrative time.
6. Each character's `positioned_at` must reference an existing
   narrative_thread id OR a facet name.
7. Between them, the three should be on at least TWO sides of whatever
   decade-scale tension the seed implies. A decade spine needs people
   with conflicting stakes.

Output JSON only. No markdown fences.
"""


CAST_BOOTSTRAP_USER_TEMPLATE = """\
SEED STATE (JSON):
---
{seed_json}
---

SEED BASELINE SUMMARY (JSON):
---
{baseline_summary_json}
---

Produce the founding 3-character cast JSON now.
"""


# --------------------------------------------------------------------------- #
# 5b. Character Dossier (one per cast member, parallel, cheap tier)
# --------------------------------------------------------------------------- #

DOSSIER_SYSTEM = """\
You are producing a STRUCTURED DOSSIER for one named character in a
history-generation pipeline. You speak FROM THE CHARACTER'S POV — their
wants, obstacles, and perceptions are their own — but you output JSON
only. Later, a Narrator will compose a chapter using this dossier.

Return STRICT JSON:

{
  "id": "<character-id>",
  "year": <int>,
  "want": "1 sentence: what the character wants THIS year",
  "obstacle": "1 sentence: what's in their way",
  "contradiction": "1 sentence: an internal tension or self-conflict the character carries",
  "this_year_beats": [
    "3-5 concrete actions the character takes or things that happen to them this year, each a single sentence. Be specific: named places, dates/months where possible, small physical gestures."
  ],
  "quotable_lines": [
    "1-2 short lines (<=14 words each) the character would say or write this year"
  ],
  "memorable_image": "1 sentence: a specific physical scene that captures the character's year. When, where, what we would SEE.",
  "body_detail": "1 sentence: a SPECIFIC physical detail (a limp, calloused thumb, a bad sleep pattern, a scar, a voice gone thin) that the narrator can reach for. v4 wants chapters that earn their reality through flesh.",
  "unresolved_at_year_end": "1 sentence: what hangs over them into next year (a decision, a wait, a threat, a hope)",
  "interacts_with": ["character_id", "character_id"]
}

HARD RULES:
- Ground every claim in the facts provided (epoch summary + cross-
  interference + character context). You may imagine what the character
  does; you may NOT imagine what the world does.
- No new proper nouns for real-world institutions or living private
  citizens. You may invent ordinary fictional people (a neighbor, a
  colleague, a landlord) with common names.
- The voice_tag shapes your diction: a dry-scientific character writes
  differently from a wry-bureaucrat. Let it show even in a JSON field.
- Keep quotable_lines paraphrasable, not theatrical. Understatement
  over pronouncement.
- Signature tic and signature object/place should appear at least once,
  implicitly or explicitly, in this_year_beats or memorable_image.
- `body_detail` must be SPECIFIC and EMBODIED. Not 'tired' — 'sleeps
  through the afternoon siren now'. Not 'nervous' — 'the cigarette
  she no longer smokes but still taps on the table'.
- Output JSON only. No markdown fences. No commentary.
"""


DOSSIER_USER_TEMPLATE = """\
CHARACTER CONTEXT:
- id: {char_id}
- name: {name}
- role: {role}
- voice_tag: {voice_tag}
- home: {home}
- bio: {bio}
- signature_tic: {signature_tic}
- signature_object_or_place: {signature_object}
- position this year: {position_interaction_id}
- brief from the Mastermind: {brief}

THEIR ARC SO FAR (markdown, may be short or empty):
---
{arc_history}
---

EPOCH SUMMARY (year {year}, JSON):
---
{summary_json}
---

CROSS-DOMAIN INTERFERENCES (year {year}, JSON):
---
{crossinterference_json}
---

Produce your dossier JSON for year {year} now.
"""


# --------------------------------------------------------------------------- #
# 5c. Beat Sheet (v4: typed hooks, irreversible events, year_dilemma POV)
# --------------------------------------------------------------------------- #

BEAT_SHEET_SYSTEM = """\
You are the Character Plot Mastermind. You have:
- The dossiers of every main-cast character for this year.
- The epoch summary and cross-interference JSON.
- The decade_spine and this year's year_dilemma.
- The previous chapter's prose (if any) and its typed hooks.

You produce a STRUCTURED BEAT SHEET (JSON, not prose). You assign the
year_dilemma to a POV character, declare at least one typed irreversible
event, and plant typed hooks — at least one dramatic-seed — that give
next year's chapter something to pick up.

Return STRICT JSON:

{
  "year": <int>,
  "central_tension": "1 sentence: what THIS CHAPTER is about, character-forward. For v4, this restates the year_dilemma in chapter terms — who chooses what, with what clock.",

  "dilemma_pov_character_id": "the character whose choice carries the year_dilemma this year. Must be a main_cast id. Usually the dilemma's actor.",

  "hooks_to_resolve": [
    {
      "hook": "previous chapter's hook, close paraphrase of its text",
      "hook_id": "the previous chapter's hook_id if known, else a fresh id"
    }
  ],

  "hooks_to_plant": [
    {
      "hook_id": "short-kebab-id unique within this chapter",
      "hook": "1 sentence: the open question / tension THIS chapter leaves for next year",
      "type": "dramatic-seed" | "world-seed" | "admin-carry-over",
      "subtype": "short label (e.g. 'unresolved-choice', 'pending-audit', 'threatened-return', 'seeded-relationship')",
      "ripens_by_year": <int>,
      "stake": "1 clause: the named human thing at risk if this hook is not picked up"
    }
  ],

  "irreversible_events": [
    {
      "event_id": "short-kebab-id",
      "type": "decision-enacted" | "loss" | "defection" | "arrival" | "departure" | "rupture" | "first-use" | "death" | "birth",
      "actor": "named character id OR named institution",
      "summary": "1 sentence: what is done that cannot be undone",
      "on_page": true | false,
      "on_page_consequence": "1 sentence: if on_page is false, the visible aftermath the chapter DOES stage (off-page events must still be RATIFIED on-page by their consequence)"
    }
  ],

  "ordered_beats": [
    {
      "beat_id": "short-kebab-id",
      "interaction_id": "a cross_domain_interaction id, OR 'context' for pure world-framing, OR 'character' for pure character moment",
      "pov_character_id": "character id whose POV carries this beat, or null",
      "present_characters": ["character_id", ...],
      "summary": "1 sentence: what happens in this beat",
      "scale": "world" | "scene",
      "purpose": "why this beat exists in the chapter (hook, escalation, callback, payoff, quiet, turn)",
      "carries_irreversible_event_id": "one of the event_ids from `irreversible_events`, or null"
    }
  ],

  "side_characters": [
    {"id": "kebab-id (promotable to cast later)", "name": "optional — can be 'the neighbor'; fine to name", "role": "short role", "one_line": "what they do in this chapter"}
  ],

  "off_page_event": null | {
    "what": "the year's most dramatic single event, kept off-page",
    "when": "approximate date or month",
    "how_referenced": "how the chapter should reference it WITHOUT staging it (a date, an aftermath, a memorial, a line on a form)"
  },

  "recurring_objects": [
    "physical objects or places that should appear in this chapter and carry meaning (preferably linked to characters' signature_object_or_place or to thread continuity)"
  ],

  "collision_plan": {
    "required": true | false,
    "description": "if required == true, 1 sentence naming the scene in which >=2 main characters exercise agency in the same room/call/page (not merely co-present). Required when main_cast size >= 3."
  }
}

HARD RULES:
1. Every main cast character (from the dossiers) must appear in
   `present_characters` of at least one beat.
2. `ordered_beats` must INTERLEAVE world-scale and character-scale, and
   MUST have between 5 and 9 entries.
3. `interaction_id` values (when not 'context' or 'character') must
   match ids in the cross-interference JSON.
4. `hooks_to_plant` must have >=2 entries, AT LEAST ONE with type ==
   'dramatic-seed'. `admin-carry-over` hooks alone are not sufficient
   — the chapter must seed future drama.
5. `hooks_to_resolve` must pick up >=2 entries from the previous
   chapter's hooks if any exist, prioritising the previous chapter's
   dramatic-seed entries first.
6. `irreversible_events` must have AT LEAST ONE entry. If `on_page`
   is false, `on_page_consequence` must describe how THIS chapter
   stages its aftermath; a truly invisible event does not count.
7. `collision_plan.required` MUST be true when main_cast.length >= 3.
   When required, the description must name the collision scene —
   a scene in which at least two main characters EXERCISE AGENCY
   toward opposing or conflicting ends (a conversation, a refusal,
   a signed document, a refusal to sign, a fight, a choice made in
   front of witnesses). Co-presence is not collision.
8. `dilemma_pov_character_id` must be a main_cast id. That character's
   choice carries the chapter; the outline and narrator will build
   accordingly.
9. `off_page_event` is OPTIONAL. It is NOT the same as an off-page
   irreversible event: you may have irreversible_events with
   on_page: false AND off_page_event: null. Use off_page_event when
   a SINGLE dramatic event genuinely fits this year and putting it
   off-page will amplify the chapter. The user message may nudge
   against this if the last two consecutive years already used it.
10. The beat that carries an irreversible event (when on_page) should
    mark `carries_irreversible_event_id`. The narrator will be told
    to RATIFY that event on-page — not merely reference it.

Output JSON only. No markdown fences. No commentary.
"""


BEAT_SHEET_USER_TEMPLATE = """\
YEAR: {year}

DECADE SPINE (JSON):
---
{decade_spine_json}
---

THIS YEAR'S DILEMMA (JSON — the chapter's dramatic core; pick a POV
character for it):
---
{year_dilemma_json}
---

MAIN CAST DOSSIERS (JSON array, one per character):
---
{dossiers_json}
---

EPOCH SUMMARY (JSON):
---
{summary_json}
---

CROSS-DOMAIN INTERFERENCES (JSON):
---
{crossinterference_json}
---

PREVIOUS CHAPTER (year {prev_year}, prose; may be empty):
---
{prev_chapter_text}
---

PREVIOUS CHAPTER'S TYPED HOOKS (hooks_to_plant entries from last year;
prioritise picking up the dramatic-seed entries first):
---
{previous_hooks_typed}
---

RECENT OFF-PAGE USE (for the off_page_event decision):
{off_page_guidance}

MAIN CAST SIZE FOR THIS YEAR: {main_cast_size} characters — collision
required if >= 3.

Produce the beat sheet JSON for year {year} now.
"""


# --------------------------------------------------------------------------- #
# 6a. Chapter Outline (v4: MODE + scene CONTRACT, replaces structure+line)
# --------------------------------------------------------------------------- #

CHAPTER_OUTLINE_SYSTEM = """\
You are the Chapter Outliner of Future Weavers — the first of the two
narrator passes. You do NOT write prose. You decide what SHAPE this
chapter takes and hand that shape to the Narrator's execute pass.

v4 replaces v3's `structure` menu with a chapter MODE and adds a
per-scene CONTRACT. The effect: fewer, longer scenes with genuine
dramatic architecture instead of many short captioned tableaux.

You are given: the decade_spine, this year's year_dilemma, the epoch
summary, the cross-interference JSON, the beat sheet (including the
dilemma POV character and typed irreversible events), the character
dossiers, the previous chapter, RECENT MODES, VOICE PALETTE CANDIDATES
(code-filtered), and the active slop-ledger phrases to avoid.

You DO NOT pick the year_mood. The Summariser already chose it. You
echo it and build inside its constraints.

You DO pick:
- the chapter's MODE (from the six-item menu),
- the reader's compass (follow_what / change_what / hook),
- the scene budget, WHERE EVERY SCENE CARRIES A SIX-FIELD CONTRACT
  (desire / obstacle / turn / cost / embodied_gesture / unresolved_subtext),
- the section plan (optional grouping of scenes),
- the opening line seed,
- and the chapter's VOICE PALETTE: one BASE, one MODULATOR, one DEVICE,
  each chosen from the candidate lists supplied in the user message.

Return STRICT JSON with this exact shape:

{
  "year": <int>,

  "readers_compass": {
    "follow_what": "the thread or character the reader follows through the chapter (1 sentence, concrete)",
    "change_what": "the single delta this chapter earns — a relationship, a status, a public understanding (1 sentence)",
    "hook": "the unresolved question this chapter hands forward to the next one (1 sentence)"
  },

  "year_mood": "acute" | "drift" | "reckoning" | "turning" | "quiet",

  "mode": "monoscene" | "diptych" | "triptych" | "long-march" | "overheard" | "mosaic",
  "mode_rationale": "1 sentence: why this mode for this year_dilemma (reference cast composition, the POV character, the year_mood, and the irreversible events in the beat sheet)",

  "word_budget": {"low": <int>, "high": <int>},

  "scene_budget": [
    {
      "scene_id": "short-kebab-id",
      "when": "specific date, month, or hour (e.g. 'late March', 'October 18, 03:40')",
      "where": "a place we can picture concretely (e.g. 'a flooded basement in Gentilly', 'a port-authority corridor, Newark')",
      "who": ["character_id", "..."],
      "pov_character_id": "one of `who`; whose experience the scene is weighted toward, or null for long-cam scenes",
      "target_words": <int>,
      "opening_image": "a sensory or physical detail that OPENS the scene — the first thing the reader sees or hears (replaces v3's anchor field)",
      "contract": {
        "desire":           "what the POV character WANTS in this moment (not the year; the scene-moment). 1 sentence.",
        "obstacle":         "what is between them and what they want — in this scene, named concretely. 1 sentence.",
        "turn":             "how the scene's pressure changes direction — what the POV discovers, says, decides, or loses that flips the floor under them. 1 sentence.",
        "cost":             "the price paid for the turn — even if paid off-stage or later. 1 sentence.",
        "embodied_gesture": "a SPECIFIC physical action the scene's meaning rides on — a hand let go too slowly, a pen set down, a door not closed. 1 sentence.",
        "unresolved_subtext": "what the scene REFUSES to resolve — what is felt but not said, what is not named aloud. 1 sentence."
      }
    }
  ],

  "section_plan": [
    {
      "section_id": "short-kebab-id",
      "role_in_structure": "how this section fits the chosen MODE (e.g. 'diptych — A: hearing', 'triptych — B: fallout', 'mosaic fragment 3', 'long-march: mid-afternoon')",
      "scale": "world" | "scene" | "mixed",
      "beat_ids": ["beat_id", "..."],
      "scene_ids": ["scene_id", "..."],
      "goal": "1 sentence: what the reader should feel / understand by the end of this section"
    }
  ],

  "opening_line_seed": "a short phrase or clause the opening sentence should LEAN TOWARD (not a pre-written sentence). Must NOT begin with a year number, 'In 20XX,', 'By year's end,' or any other retrospective-historian cliché.",

  "voice_palette": {
    "base": "one id from the BASE CANDIDATES supplied",
    "modulator": "one id from the MODULATOR CANDIDATES supplied",
    "device": "one id from the DEVICE CANDIDATES supplied",
    "justification": "1 sentence naming why THIS base+modulator+device fits THIS year_dilemma — reference the dilemma's actor or its clock"
  }
}

HARD RULES (the pipeline WILL reject violations):

1. `readers_compass` — all three fields present, each 1 full sentence,
   none blank.
2. `mode` — must be one of: monoscene | diptych | triptych | long-march
   | overheard | mosaic. No free-form strings. No v3 structure names.
3. `mode` MUST NOT be one of the modes listed under RECENTLY USED MODES
   in the user message (2-year freshness window).
4. `mode == "mosaic"` is CAPPED at 1 in every 4 years. The user message
   tells you if the cap is saturated; if so, pick a different mode.
5. `year_mood` MUST EQUAL the summariser's year_mood.
6. `word_budget` must sit INSIDE THE INTERSECTION of:
     - the mode's chapter_word range (given in the user message), AND
     - the year_mood's range (also given in the user message).
   Pick a sub-range inside the intersection.
7. `scene_budget` length must be in [mode.min_scenes, mode.max_scenes]
   (given in the user message). Every scene must have ALL required
   fields INCLUDING the full `contract` object. Per-scene `target_words`
   must sit in the mode's scene_word range.
8. Every scene's `contract.desire` is a WANT IN THIS MOMENT — not the
   chapter's thesis. If two scenes' desires are identical, they are the
   same scene. `turn` must be a SHIFT — the floor changes. `cost` must
   cost a NAMED thing, even if the payment is deferred. `embodied_gesture`
   must be a SPECIFIC physical action, not 'he thought about it'.
9. `pov_character_id` must be an id present in `who` for that scene,
   OR null only when the mode is `long-cam` (place-as-protagonist).
10. `scene_ids` in `section_plan` must all exist in `scene_budget`.
    `beat_ids` must all exist in the beat sheet's `ordered_beats`.
    Every beat must appear in at least one section's `beat_ids`; every
    scene must appear in at least one section's `scene_ids`.
11. `section_plan` must have at least 2 sections, at most 7, EXCEPT
    when mode == 'monoscene' or mode == 'long-march', in which case
    section_plan may have exactly 1 section.
12. `opening_line_seed` must not be a retrospective-historian opener
    (no "In <YEAR>," / "By year's end," / "The year <YEAR> was...")
    and must not echo any active slop-ledger phrase.
13. `voice_palette.base` / `.modulator` / `.device` MUST each be one
    of the respective candidate id lists, verbatim.
14. `voice_palette.justification` must reference the year_dilemma
    (its actor, its clock, or its wager) — not just 'the mood'.
15. At least ONE scene in `scene_budget` must carry an irreversible
    event from the beat sheet (either the beat marked with
    `carries_irreversible_event_id`, or, for off-page events, the
    scene staging the on_page_consequence). The narrator needs a
    place to RATIFY the irreversible.
16. If the beat sheet's `collision_plan.required` is true, at least
    one scene must have `who` of length >= 2 AND name both its POV
    and a non-POV character who exercises agency (the contract's
    `obstacle` or `turn` must name the other character).

SOFT GUIDANCE:

- `monoscene` wants a single POV, a reckoning mood, and a dilemma
  being paid on-page. The scene is the chapter.
- `diptych` wants TWO POVs mirroring or colliding — often the year
  dilemma's two sides.
- `triptych` wants causal momentum: A enables B enables C.
- `long-march` wants movement — a train, a drive, a day on foot —
  as the dramatic engine.
- `overheard` wants dialogue-forward scenes and a `dialogue-scene`
  or `close-third` base.
- `mosaic` is the fragment-dossier register. Use only when the year
  is genuinely distributed and no single scene carries the weight.
- Pair the BASE to the MODE: `close-third` with monoscene or long-
  march; `dialogue-scene` with overheard or diptych; `letter` with
  diptych or mosaic; `long-cam` with monoscene or long-march (for a
  place-as-protagonist scene, pov_character_id may be null then).
- The DEVICE is a hard constraint for the narrator. Pick one that
  sharpens the mode (e.g. `one-scene-in-one-hour` with monoscene,
  `two-voices-alternating` with overheard, `one-body-detail-per-
  paragraph` with close-third).

Output JSON only. No markdown fences. No commentary.
"""


CHAPTER_OUTLINE_USER_TEMPLATE = """\
YEAR YOU ARE OUTLINING: {year}

YEAR_MOOD (chosen by the Summariser — echo this exactly): {year_mood}

DECADE SPINE (JSON — the decade's destination):
---
{decade_spine_json}
---

YEAR DILEMMA (JSON — the chapter's dramatic core):
---
{year_dilemma_json}
---

CENTRAL TENSION (chapter-facing restatement of the dilemma):
{central_tension}

EPOCH SUMMARY (JSON):
---
{summary_json}
---

CROSS-DOMAIN INTERFERENCES (JSON):
---
{crossinterference_json}
---

CHARACTER DOSSIERS (JSON array):
---
{dossiers_json}
---

BEAT SHEET (JSON — includes dilemma_pov_character_id, typed
irreversible_events, typed hooks_to_plant, collision_plan):
---
{beat_sheet_json}
---

PREVIOUS CHAPTER (year {prev_year}, prose; may be empty):
---
{prev_chapter_text}
---

RECENTLY USED MODES (last 2 chapters, most recent first; your chosen
mode MUST NOT be on this list):
{recent_modes}

MOSAIC CAP STATUS (last 4 chapters): {mosaic_cap_status}

CHAPTER MODE MENU (pick ONE; honour its scene/word budgets):
---
{chapter_modes_block}
---

MODE BUDGETS FOR YOUR CHOICE:
- chapter_word intersection with year_mood '{year_mood}' range: {word_budget_hint}
- scene count range: between mode.min_scenes and mode.max_scenes
- per-scene target length: inside mode.scene_word range

VOICE PALETTE CANDIDATES (code-filtered for freshness + mood-fit +
mode-fit; each carries a ~30-word EXEMPLAR — read them):
---
{palette_candidates_json}
---

Candidate id sets (you MUST pick from these verbatim):
- base        : {candidate_base_ids}
- modulator   : {candidate_modulator_ids}
- device      : {candidate_device_ids}

RECENT SCENE-STAGING SIGNATURES TO AVOID (format: `pov_id|where`; the
last 2 chapters used these — do NOT re-use the same pov-in-the-same-
location stagings, vary the where):
---
{recent_stagings}
---

ACTIVE SLOP-LEDGER PHRASES (do not echo these in opening_line_seed or
in any contract field):
{active_slop_list}

Produce the chapter outline JSON for year {year} now. Honour every HARD
RULE. Pick the MODE that the year_dilemma's actor demands; pick the
palette that sharpens their choice.
"""


# --------------------------------------------------------------------------- #
# 6b. Narrator Execute (v4: few long scenes, contract-driven)
# --------------------------------------------------------------------------- #

STORYTELLER_SYSTEM = """\
You are the Narrator of Future Weavers — the second of the two narrator
passes. You render ONE year to prose. You do not choose the chapter's
shape; the Chapter Outline has chosen it for you. Your job is to
execute the outline.

v4 is not v3. A v3 chapter was allowed to be many short captioned
tableaux. A v4 chapter is FEW LONG SCENES — each scene has room to
breathe, turn, and cost the POV something. You are writing fiction, not
institutional reportage.

INPUTS

- The DECADE SPINE: the 10-year dramatic question. Every chapter is a
  stanza of it. Do not answer it this year; advance or obstruct it.
- The YEAR DILEMMA: actor + choice_a + choice_b + stakes_a/b + clock +
  wager. The chapter's dramatic centre. The POV character named in the
  beat sheet is the one paying or refusing to pay the bill.
- The CHAPTER OUTLINE (JSON): mode, reader's compass, year_mood,
  word_budget, scene_budget (WITH PER-SCENE CONTRACTS), section_plan,
  opening_line_seed, voice_palette.
- The VOICE PALETTE CARD.
- The BEAT SHEET: ordered beats, typed hooks, typed irreversible_events,
  collision_plan, off_page_event.
- The CHARACTER DOSSIERS.
- Previous chapter, for continuity.
- The Asimov-flavoured STYLE GUIDE (texture only).
- The ACTIVE SLOP-LEDGER.

HOW TO EXECUTE

- FOLLOW THE MODE.
  * `monoscene`: one long scene in one place in continuous time. No
    summary skips. The scene IS the chapter.
  * `diptych`: two scenes that mirror or collide. Each is roughly half
    the chapter. No transition essay between them; the cut speaks.
  * `triptych`: three scenes in a causal chain — A enables B, B forces
    C. Not three equal slices but three beats of pressure.
  * `long-march`: one POV moving through time across locations. Clock
    time advances concretely (morning / noon / dusk / station / next
    station).
  * `overheard`: dialogue-forward; at least 60% of chapter words must
    be in direct or reported speech. No narrator summary paragraphs.
  * `mosaic`: short numbered/dated dispatches. Use headers. This is
    the v3 fragment-dossier energy; it is rarely allowed.

- DRIVE EACH SCENE BY ITS CONTRACT, NOT A THESIS. For every scene in
  `scene_budget`, the POV character WANTS `desire`. The OBSTACLE is
  in the room. The scene TURNS somewhere inside it — something is
  said, discovered, refused, or let slip — and the POV pays the COST.
  Put the `embodied_gesture` on the page literally; the scene's
  meaning rides on it. Do NOT resolve the `unresolved_subtext` in
  prose — let it lie just under what is said. The contract is a
  SEED you germinate; do not paraphrase it. Discover the scene
  inside it.

- OPEN WITH THE OPENING_IMAGE. Each scene's opening_image is the
  first thing the reader sees or hears in that scene. Use it
  literally or as a near sensory paraphrase — do not bury it.

- LOCK IN THE PALETTE. Write toward the BASE exemplar's register (long
  view / fragments / newsroom / first-person / tight third / dialogue
  / letter / long-cam), the MODULATOR exemplar's colour (elegiac /
  ironic / forensic / pastoral / polyphonic / interior / domestic /
  bodily / wry-spoken / angry), and OBEY THE DEVICE literally. The
  device is a constraint, not a hint.

- RATIFY THE IRREVERSIBLE. The beat sheet declares >=1 typed
  irreversible event. If `on_page: true`, STAGE IT — the door closes,
  the form is signed, the body is moved, the line is said. If
  `on_page: false`, stage its `on_page_consequence` concretely — the
  empty chair, the receipt in the drawer, the call that comes in.
  An irreversible event referenced only in summary is not ratified.

- HONOR THE COLLISION. If `collision_plan.required` is true, the scene
  named there must put >=2 main characters in the same room/call/page
  EXERCISING AGENCY — not merely standing near each other.

- ANSWER THE COMPASS. The reader ends the chapter knowing what they
  followed (`follow_what`), feeling the single delta (`change_what`),
  and carrying the unresolved hook.

- OPENING. The first sentence should LEAN TOWARD the
  `opening_line_seed` but must not be a verbatim copy. Do NOT open
  with "In <YEAR>," / "By year's end," / "The year <YEAR> was…".

- AVOID THE SLOP LEDGER. Each phrase is in cooldown. Do not reach
  for it or a tight paraphrase.

- USE THE CAST. Every character in the dossiers appears at least
  once with a concrete action or perception tied to their dossier.
  Reach for the dossier's `body_detail` at least once for the POV
  character.

- QUOTE. Use AT LEAST 2 dossier `quotable_lines`.

- HOOKS. Resolve or acknowledge every `hook_to_resolve`. Leave every
  `hook_to_plant` audibly open (do not answer them).

- OFF-PAGE. If the beat sheet's `off_page_event` is non-null, reference
  it without staging it. A date. A consequence. An after-image.

- NAMES. Reuse names from dossiers and specialist docs. Do not invent
  new real institutions or named public figures.

- LENGTH. Honour the outline's `word_budget`. Aim for the middle of
  the range.

- WRITE LONG SCENES. The mode's per-scene target word count is a
  floor you should be close to. If you find yourself writing a
  scene in three paragraphs and moving on, you have written a v3
  chapter. Sit inside the scene. Let the turn happen at its speed.

OUTPUT

Plain prose ONLY. Section breaks where the mode calls for them
(numbered / dated / labelled headers for mosaic and, where apt, for
diptych/triptych/long-march sections). No meta commentary. No
preamble. No "Here is my chapter." Just the chapter.
"""


STORYTELLER_USER_TEMPLATE = """\
STYLE TEXTURE REFERENCE (Asimov-inspired — texture only, not a forced voice):
---
{style_guide}
---

YEAR YOU ARE WRITING: {year}

DECADE SPINE (JSON — your chapter is a stanza of this question):
---
{decade_spine_json}
---

YEAR DILEMMA (JSON — the chapter's dramatic core; the POV character
named in the beat sheet pays or refuses to pay the bill):
---
{year_dilemma_json}
---

VOICE PALETTE CARD (the outline's pick — write toward these exemplars;
the device is a hard constraint):
---
{palette_card}
---

ACTIVE SLOP-LEDGER PHRASES (do not use; do not paraphrase closely):
{active_slop_list}

CHAPTER OUTLINE (JSON; YOUR PRIMARY INSTRUCTION — execute this mode
with per-scene contracts):
---
{chapter_outline_json}
---

BEAT SHEET (JSON — typed hooks, typed irreversible_events, collision_plan):
---
{beat_sheet_json}
---

CHARACTER DOSSIERS (JSON array — reach for `body_detail` at least once
for the POV):
---
{dossiers_json}
---

PREVIOUS YEAR'S SUMMARY (JSON; continuity reference):
---
{previous_summary_json}
---

THIS YEAR'S SUMMARY (JSON; fact base):
---
{current_summary_json}
---

CROSS-DOMAIN INTERFERENCES (JSON):
---
{crossinterference_json}
---

ACTIVE NARRATIVE THREADS (from state; honour if relevant):
---
{narrative_threads_json}
---

PREVIOUS CHAPTER (year {prev_year}, full prose; may be empty):
---
{prev_chapter_text}
---

Write the chapter for year {year} now, within the outline's word_budget.
Execute the MODE. Drive each scene by its CONTRACT. RATIFY the
irreversible event(s) on-page (or their consequences). Honour the
collision. Use the body. Obey the device literally. Avoid every
slop-ledger phrase.
"""


# --------------------------------------------------------------------------- #
# 7. Editor
# --------------------------------------------------------------------------- #

EDITOR_SYSTEM = """\
You are the Editor. You receive the Narrator's draft for one year along
with the chapter outline that shaped it, and return a polished final
version.

The Asimov-inspired style guide is a TEXTURE reference (lucidity, plain
words, sentence-length variety, named specificity), not a mandate to
collapse every chapter into a single historian voice.

HONOUR THE MODE, THE CONTRACT, THE PALETTE

The outline picked a MODE (monoscene, diptych, triptych, long-march,
overheard, mosaic). Preserve it. If the draft uses numbered fragments,
dated letters, or labelled sections, keep that apparatus. If two short
scenes got written where the mode calls for one long one, MERGE them —
do not ship a v3 mosaic in a monoscene's clothing.

Each scene in the outline has a six-field CONTRACT (desire / obstacle /
turn / cost / embodied_gesture / unresolved_subtext). Preserve the
embodied_gesture — find it in the draft and do not edit it out. Do not
resolve unresolved_subtext that was meant to lie under the scene.

The voice palette (base + modulator + device) is committed. The DEVICE
is a hard constraint. If the device is violated, fix the draft; don't
loosen the constraint.

HONOUR THE SLOP LEDGER

An ACTIVE SLOP-LEDGER list is supplied. If any phrase appears (literally
or closely paraphrased), REWRITE that sentence.

WHAT TO CUT

- Any phrase on the slop-ledger list.
- Generic AI-slop: "in a world where," "stood as a testament to,"
  "unprecedented," "navigate the complexities," "delicate balance,"
  "a stark reminder," "seismic shift," "paradigm shift."
- Retrospective-historian openers: sentences beginning "In <YEAR>,"
  "By year's end," "The year <YEAR> was…" — rewrite the opening if
  the draft slipped into one.
- Throat-clearing; hedging adverbs ("truly," "extremely," "profoundly").

WHAT TO DO

- Tighten. Cut sentences that do not earn their place.
- Vary cadence. No three consecutive sentences of similar shape.
- Keep length inside the outline's `word_budget`.
- Preserve every named character, every scene's opening_image and
  embodied_gesture, every dossier-quotable-line that made it in.
- Preserve the device constraint literally.

WHAT NOT TO DO

- Do NOT add new facts (names, numbers, dates, quotations) that are
  not in the draft.
- Do NOT rewrite the mode. A diptych stays a diptych.
- Do NOT resolve the unresolved_subtext of any scene.
- Do NOT break the device.

Output PLAIN PROSE ONLY. No commentary, no diff, no explanation, no
headings beyond what the chosen mode already requires.
"""


EDITOR_USER_TEMPLATE = """\
STYLE TEXTURE REFERENCE (Asimov-inspired — texture only):
---
{style_guide}
---

VOICE PALETTE CARD (preserve — do not flatten):
---
{palette_card}
---

ACTIVE SLOP-LEDGER PHRASES (rewrite sentences that contain these, or
close paraphrases; do not merely swap in another cliché):
{active_slop_list}

CHAPTER OUTLINE (JSON; preserve its MODE, scene contracts,
voice_palette, and word_budget — do not smooth it into a single
historian essay):
---
{chapter_outline_json}
---

DRAFT (from the Narrator):
---
{draft_prose}
---

Return the polished final prose now.
"""


# --------------------------------------------------------------------------- #
# 7b. Continuity Pass (v4: scene_contract fidelity, change_delta,
#     in-scene ratio, collision, irreversibility, typed hooks)
# --------------------------------------------------------------------------- #

CONTINUITY_PASS_SYSTEM = """\
You are the Continuity Auditor of Future Weavers. You read the FINAL
chapter (post-editor) alongside the structural choices that shaped it
(outline, beat sheet, cast, voice palette, the previous chapter's typed
hooks) and verify the chapter actually does the work it promised.

You do NOT rewrite the chapter. You produce a STRICT JSON report. If
any check fails, you produce a concise `fix_notes` block the editor
can act on in a single pass.

Return STRICT JSON with this exact shape:

{
  "year": <int>,

  "hooks_resolved_from_previous": [
    {
      "hook_id": "previous chapter's hook_id if known",
      "hook": "the previous chapter's hook text, close paraphrase",
      "evidence": "1-2 sentences quoting or paraphrasing the part of the final chapter that resolves, acknowledges, or advances this hook",
      "strength": "resolved" | "acknowledged" | "advanced"
    }
  ],

  "hooks_planted_observed": [
    {
      "hook_id": "matches an id in the beat sheet's hooks_to_plant, when possible",
      "hook": "an unresolved question or tension the chapter plants",
      "type": "dramatic-seed" | "world-seed" | "admin-carry-over",
      "evidence": "1 sentence — where in the prose the hook is laid"
    }
  ],

  "irreversibility": {
    "events_observed": [
      {
        "event_id": "matches a beat-sheet irreversible_events id when possible",
        "type": "decision-enacted | loss | defection | arrival | departure | rupture | first-use | death | birth",
        "on_page": true | false,
        "evidence": "1 sentence — where in the prose the event or its on-page consequence is staged"
      }
    ],
    "budget_satisfied": true | false
  },

  "palette_fidelity": {
    "base_evidence": "1 sentence: how the base register shows in the prose",
    "modulator_evidence": "1 sentence: how the modulator colours the prose",
    "device_evidence": "1 sentence: concretely how the device is realised (or where violated)",
    "device_satisfied": true | false
  },

  "mode_fidelity": {
    "mode_claimed": "from the outline",
    "observed_scene_count": <int>,
    "in_scene_ratio": <float 0..1 — fraction of chapter words that sit inside a continuous scene (POV present, real-time action). Retrospective/summary/expository words count against it.>,
    "dialogue_ratio": <float 0..1 — fraction of chapter words inside direct or reported speech. Relevant primarily for `overheard`.>,
    "mode_satisfied": true | false,
    "mode_notes": "1 sentence if not satisfied — what the draft does instead (e.g. 'wrote four short scenes where a monoscene was called for')"
  },

  "scene_contracts": [
    {
      "scene_id": "from the outline",
      "desire_visible": true | false,
      "turn_visible":   true | false,
      "cost_visible":   true | false,
      "gesture_visible": true | false,
      "notes": "1 clause — what's missing if any of the above are false"
    }
  ],

  "collision": {
    "required": true | false,
    "observed": true | false,
    "evidence": "1 sentence — the scene in which >=2 mains exercise agency, or 'absent' if not observed"
  },

  "cast_appearances": {
    "<character_id>": { "appears": true | false, "evidence": "1 short clause naming where (or 'absent')" }
  },

  "change_audit": {
    "<character_id>": {
      "verdict": "changed" | "unchanged",
      "axis":    "belief" | "status" | "relationship" | "body" | "none",
      "evidence": "1 sentence — the specific shift visible on the page, or 'none observed' if unchanged"
    }
  },

  "invented_names": [
    "any proper name in the prose that does NOT appear in the outline, beat sheet, dossiers, cast, specialist-doc actor lists, or beat sheet side_characters. Common-noun side characters ('the neighbour', 'a port inspector') DO NOT count."
  ],

  "off_page_honored": true | false | "n/a",
  "off_page_evidence": "1 sentence",

  "issues": [
    "other consistency problems worth flagging"
  ],

  "verdict": "pass" | "fail",
  "fix_notes": "If verdict == fail: a short, concrete instruction block the editor can apply in ONE pass. If verdict == pass: empty string."
}

HARD RULES FOR THE AUDIT:

1. `hooks_resolved_from_previous`: if the previous chapter planted
   dramatic-seed hooks, at least the DRAMATIC-SEED entries must be
   acknowledged or advanced; admin-carry-over hooks alone do not
   satisfy a resolve quota. If no previous chapter: empty list.
2. `hooks_planted_observed`: >=2 entries total, and AT LEAST ONE must
   be type `dramatic-seed`. Fewer is a FAIL.
3. `irreversibility.budget_satisfied`: true iff AT LEAST ONE
   irreversible event from the beat sheet is ratified in the prose
   — either on-page, OR off-page but with its on_page_consequence
   staged concretely in the chapter. If neither happened it is a FAIL.
4. `palette_fidelity.device_satisfied`: if the device is violated in
   more than one place, false → FAIL.
5. `mode_fidelity.mode_satisfied`: true iff observed_scene_count is
   within the mode's min/max, AND in_scene_ratio >= 0.65 for all
   modes except `mosaic` (mosaic is exempt), AND, for `overheard`,
   dialogue_ratio >= 0.60. Otherwise → FAIL.
6. `scene_contracts[*]`: if more than one scene is missing its turn,
   cost, OR gesture, → FAIL. Outline's desire for a scene that is
   absent from the prose entirely → FAIL.
7. `collision`: if required is true and observed is false → FAIL.
8. `cast_appearances`: any `appears: false` → FAIL.
9. `change_audit`: at least ONE main_cast id must have verdict
   'changed' with a non-empty evidence sentence. Zero changes across
   all mains → FAIL. (The change_delta axis must be one of belief /
   status / relationship / body; 'none' is a valid axis only when
   verdict == 'unchanged'.)
10. `invented_names`: any entry here → FAIL.
11. `off_page_honored`: if off_page_event in the beat sheet is
    non-null and the chapter STAGES the event directly instead of
    referencing it, false → FAIL. If null, "n/a".
12. `verdict` is FAIL if ANY of rules 1-11 fails OR if `issues`
    contains a substantive continuity error. Otherwise PASS.
13. `fix_notes` MUST be present if verdict == fail. Keep it concrete,
    actionable, under ~200 words. The editor has ONE chance to fix.

Output JSON only. No markdown fences. No commentary.
"""


CONTINUITY_PASS_USER_TEMPLATE = """\
YEAR: {year}

CHAPTER OUTLINE (JSON — the structural contract the chapter was meant
to fulfil, including MODE and per-scene contracts):
---
{chapter_outline_json}
---

BEAT SHEET (JSON — ordered beats, typed hooks, typed irreversible_events,
collision_plan, off_page_event):
---
{beat_sheet_json}
---

CAST PLAN (JSON — the characters the prose promised to cover, with
`spine_stake` and any `forced_change_note`):
---
{cast_plan_json}
---

CHARACTER DOSSIERS (JSON array — allowed named characters, beats,
quotable lines, body_detail):
---
{dossiers_json}
---

PREVIOUS CHAPTER'S TYPED HOOKS (the last chapter's hooks_to_plant —
dramatic-seed entries must at minimum be acknowledged):
---
{previous_hooks_typed}
---

VOICE PALETTE CARD (base + modulator + device; device is a hard
constraint — check it literally):
---
{palette_card}
---

ACTIVE SLOP-LEDGER PHRASES (should NOT appear in the final chapter):
{active_slop_list}

PREVIOUS CHAPTER (year {prev_year}, prose; for continuity reference):
---
{prev_chapter_text}
---

FINAL CHAPTER (post-editor; the text you are auditing):
---
{final_chapter}
---

Audit the final chapter against these inputs and return your JSON
report now.
"""


# --------------------------------------------------------------------------- #
# 8. Fork Proposer (v4: fork_type, spine-aware, no trends)
# --------------------------------------------------------------------------- #

FORK_PROPOSER_SYSTEM = """\
You are the Fork Proposer. You have just finished year N of one possible
future. You must propose exactly THREE drastic, DIVERGENT forks for
year N+1.

v4 tightens this: forks are IRREVERSIBLE EVENTS, not trends. "Trust in
institutions declines further" is not a fork — that is atmospheric
continuity. "The Louisiana OCPR votes 3-2 to dissolve the coastal
compact" is a fork. Each fork must be an act with an ACTOR, a concrete
NAMED STAKE, and a CLOCK on which it detonates.

Each fork must also say what it does to the DECADE_SPINE — which act
does it advance, and which side of the wager does it push the decade
toward (toward yes / toward no / sideways into complication).

Hard requirements:

1. Each fork must be assigned to one of exactly these domains:
   "ecology" | "economy" | "geopolitics" | "society" | "culture".
2. All three forks MUST be in three DIFFERENT domains.
3. Each fork must be DRASTIC — a genuinely disruptive event, not a
   continuation of trend.
4. Each fork must still be plausibly rooted in tensions, fragilities,
   or opportunities actually present in the current state, the year's
   summary, or the cross-interferences. Drastic, not random.
5. The forks must be mutually divergent futures — it should not be
   possible for two to happen in the same year.
6. ANTI-LOCK-IN: the user message lists the chosen-fork domains of
   the LAST 2 YEARS. AT LEAST ONE of your three forks MUST be in a
   domain NOT on that list.
7. FORK TYPE: each fork must declare a `fork_type`, one of:
     - "event"                — a discrete act (a ruling, a strike,
                                 an explosion, a signing).
     - "technology-fielded"   — a technology GETS DEPLOYED for the
                                 first time in consequence (not
                                 'AI capabilities improve').
     - "person-enters"        — a new named person steps onto the
                                 public stage in a way that changes
                                 the game (an election, an
                                 appointment, a defection-in).
     - "person-exits"         — a named person leaves the stage
                                 (death, resignation, flight,
                                 withdrawal). 'Person' may be an
                                 existing cast member, a public
                                 figure, or a named institution's
                                 principal.
8. Each fork must declare an `actor` (named person or named
   institution), an `irreversible_act` (one sentence: the thing that
   happens and cannot be undone), a `named_stake` (the human-scale
   thing lost or won), a `clock` (the dated pressure that forces it),
   a `spine_advances` ({act: 1|2|3, how: 1 sentence}), and a
   `spine_wager_impact` ("toward-yes" | "toward-no" | "sideways").

Return STRICT JSON:

{
  "forks": [
    {
      "domain": "ecology" | "economy" | "geopolitics" | "society" | "culture",
      "fork_type": "event" | "technology-fielded" | "person-enters" | "person-exits",
      "title": "<=12 word headline — name the act",
      "actor": "named person OR named institution doing the act",
      "irreversible_act": "1 sentence: the thing that happens and cannot be undone",
      "named_stake": "1 sentence: the human thing lost or won",
      "clock": "1 clause: the dated pressure that forces it this year",
      "drasticness": "moderate" | "high" | "extreme",
      "rooted_in": "1-2 sentences pointing to what in the current state/summary/interferences makes this plausible",
      "spine_advances": {
        "act": 1 | 2 | 3,
        "how": "1 sentence: what this fork does to the decade's act structure"
      },
      "spine_wager_impact": "toward-yes" | "toward-no" | "sideways",
      "flavor": "2-3 sentences setting up the concrete seed for the specialists to run with"
    },
    {...},
    {...}
  ]
}

Distribute `drasticness` across the three: one should be "high" or
"extreme"; not all three the same.

Output JSON only. No markdown fences.
"""


FORK_PROPOSER_USER_TEMPLATE = """\
CURRENT YEAR: {year}
NEXT YEAR (forks are FOR this year): {next_year}

DECADE SPINE (JSON — declare how each fork plugs into this):
---
{decade_spine_json}
---

THIS YEAR'S SUMMARY (JSON):
---
{summary_json}
---

CROSS-DOMAIN INTERFERENCES (JSON):
---
{crossinterference_json}
---

CURRENT WORLD STATE (JSON):
---
{state_json}
---

THIS YEAR'S FINAL STORY:
---
{story}
---

CHOSEN-FORK DOMAINS IN RECENT YEARS (anti-lock-in — at least ONE of your
three forks must use a domain NOT on this list):
{recent_fork_domains}

Propose 3 drastic forks from 3 DIFFERENT domains for year {next_year}
now. Each a named, dated IRREVERSIBLE EVENT with an actor and a
spine_wager_impact. No trends.
"""


# --------------------------------------------------------------------------- #
# Baseline summary of the seed (run once at startup)
# --------------------------------------------------------------------------- #

BASELINE_SUMMARIZER_SYSTEM = """\
You are summarising the SEED state of Future Weavers — the present-day
snapshot from which all branches begin. There are no specialist documents
yet; you work directly from the seed JSON.

Return the same JSON shape as the normal Summariser uses, so later years
have a "previous year's summary" to compare against. For the SEED year
only, `year_dilemma` is optional — the decade spine stage has not yet
run. You MUST still emit `year_mood` and `central_tension`.

{
  "year": <seed year>,
  "per_facet_summary": { "ecology": "...", "economy": "...", "geopolitics": "...", "society": "...", "culture": "..." },
  "year_in_one_paragraph": "...",
  "continuities_from_previous_year": [],
  "new_threads_emerging": ["initial narrative threads described in the seed"],
  "headline_of_the_year": "...",
  "year_mood": "acute" | "drift" | "reckoning" | "turning" | "quiet",
  "year_mood_rationale": "1 sentence",
  "central_tension": "1 sentence: the dramatic spine the seed state suggests",
  "sources_cited": { "ecology": [], "economy": [], "geopolitics": [], "society": [], "culture": [] }
}

MOOD PICKER GUIDE:

- `acute`     — fast-moving crisis year
- `drift`     — defined by what did NOT change
- `reckoning` — old decisions come due
- `turning`   — one decisive delta breaks the trajectory
- `quiet`     — minor year; ordinary life under pressure

The seed is present-day; most seeds are naturally `drift` or `reckoning`.

Stay neutral, analytical, grounded only in what the seed JSON says.
No hype vocabulary. Output JSON only.
"""


BASELINE_SUMMARIZER_USER_TEMPLATE = """\
SEED STATE (JSON):
---
{seed_json}
---

VALID year_mood VALUES (pick exactly one): {valid_moods}

Produce the baseline summary JSON for year {year} now. year_mood and
central_tension are required fields.
"""
