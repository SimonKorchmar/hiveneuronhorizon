"""Future Weavers — v5 variance + long-arc + rupture pipeline.

v4 keeps the v3 scaffolding (specialists, summariser, cross-interference,
cast/dossier/beats, continuity pass, fork proposer, replay CLI) intact.
It changes the scene economy, the dramatic contract, and the change
audit so chapters read like fiction rather than institutional reportage.

Key v4 additions (see ../concepts/v4_scene_depth_and_spine.md):

    0a. DECADE SPINE (new, one-time at run start, after cast bootstrap)
        -> runs/<run_id>/decade_spine.json
        A named dramatic question + wager + 3-act structure. Injected
        into every per-year prompt so forks, outlines, beat sheets,
        and narrator all see the same destination.

    04. SUMMARISER now emits year_dilemma {actor, choice_a, choice_b,
        stakes_a, stakes_b} + year_clock + year_wager alongside the
        legacy central_tension. Replaces v3's thesis-shaped spine
        with a binary-choice spine that has costs on both sides.

    06a. CAST PLAN sees decade_spine and any `unchanged_3yr` flags
        from the continuity ledger (v4.2 change-audit). Mains with
        unchanged_3yr must be retired, demoted, or given a forced
        fork arc this year.

    06c. BEAT SHEET now assigns the year_dilemma to a POV character,
        plants ≥1 typed `dramatic-seed` hook, and declares ≥1
        `irreversible_event` that the chapter must ratify on-page.
        Hooks are typed {dramatic-seed | world-seed | admin-carry-
        over}; only dramatic-seeds count toward the planted quota.

    06d. CHAPTER OUTLINE picks a MODE (not just a structure):
        monoscene | diptych | triptych | long-march | overheard |
        mosaic. Each scene carries a scene-craft CONTRACT — desire,
        obstacle, turn, cost, embodied gesture, subtext — instead
        of a pre-authored thesis line. `anchor` becomes
        `opening_image`; `line` is dropped. Mosaic is capped at 1
        in every 4 years. Modes cannot repeat within 2 years.
        Voice registry expanded with close-third / dialogue-scene /
        letter / long-cam bases; interior / domestic / bodily /
        wry-spoken / angry modulators; and embodiment-forcing
        devices. Suppressive devices are capped at 1-in-4.

    06b narrator. Writes FEW LONG scenes, not many short ones.
        Receives the scene contract and is told to DISCOVER what
        the scene is about inside the contract rather than
        paraphrase a thesis.

    07b. CONTINUITY PASS expands to audit:
         - scene_contract fidelity (turn/cost/gesture present?)
         - in-scene/retro ratio (>=65% in continuous-scene words)
         - collision scene (>=2 mains exercising agency if cast>=3)
         - irreversibility budget (>=1 on-page or on-page-consequence)
         - per-main change_delta {belief, status, relationship, body}
           with a `changed | unchanged` verdict; >=1 main must be
           `changed` each year
         - typed hooks (>=1 dramatic-seed planted)

    08. FORK PROPOSER emits EVENTS, not trends. fork_type must be
        one of {event | technology-fielded | person-enters |
        person-exits}; each fork declares an actor, an irreversible
        act, a named stake, a clock, and a spine_wager_impact.
        Trends are rejected by the validator.

    side_cast.json + staging_ledger.json (v4.2): named side
    characters persist with a promotion path; a character's
    signature staging may not recur within 2 years.

Pipeline per year (see ../concepts/plan.md for the v3 spine; v4
additions above layer on top):

    chosen_fork
        -> 5 specialists in parallel          (cheap tier, rich JSON each)
        -> state merger
        -> summarizer                         (mid tier, balanced JSON,
                                               also emits year_mood +
                                               central_tension — Phase 3)
        -> cross-interference analyst         (mid tier, JSON; Phase 4:
                                               rotation retry if >60% of
                                               interactions touch the
                                               chosen fork's domain)
        -> cast plan (5a)                     (mid tier, 3-6 main cast)
        -> character dossiers (5b, parallel)  (cheap tier, JSON each)
        -> beat sheet (5c)                    (mid tier, structured JSON;
                                               Phase 4: sees previous
                                               chapter's hooks_to_plant
                                               and recent off-page use)
        -> chapter outline (6a)               (mid tier; reader's compass
                                               + structure + scene budget
                                               + Phase 3 voice palette
                                               picked from code-computed
                                               candidates JSON)
        -> narrator execute (6b)              (premium tier, prose rendered
                                               to the outline; lean on the
                                               chosen palette + device)
        -> editor                             (premium tier, polish that
                                               preserves structure + avoids
                                               active slop-ledger phrases)
        -> continuity pass (7b)               (Phase 4: mid-tier auditor +
                                               code-side cross-checks; one
                                               editor retry on fail; ships
                                               `degraded: true` beyond that)
        -> fork proposer                      (mid tier, 3 drastic forks
                                               from 3 distinct domains;
                                               Phase 4: anti-lock-in)
        -> readability metrics (09)           (Phase 5: pure code. Per-year
                                               09_readability.json with
                                               cast counts, scenes, unique
                                               places, regions, hooks,
                                               palette, slop tics flagged —
                                               a one-row diffable record so
                                               long runs can be audited
                                               without re-reading prose.)

The pipeline can also be REPLAYED from any stage via `replay.py` (Phase 5):
a stage-scoped re-run that reads earlier artefacts from disk and only
recomputes from a chosen stage downstream. `generate_epoch` takes a
`start_from` parameter for exactly this — replay.py drives it.

Usage:
    pip install -r requirements.txt
    # paste key into .env
    python poc.py
"""

from __future__ import annotations

import asyncio
import copy
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

import prompts

load_dotenv(Path(__file__).parent / ".env")

# Force UTF-8 on stdout/stderr so Windows cp1252 consoles don't choke on
# em-dashes, curly quotes, box-drawing chars, or anything the models emit.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

MODELS = {
    # Each tier is a fallback list. First model that works wins.
    # Verified against https://developers.openai.com/api/docs/models/all/
    # (2026-04): the gpt-5.4 family is `gpt-5.4 / -pro / -mini / -nano`.
    # There is NO `-medium` variant. The gpt-4o family is kept as a backstop
    # in case a gpt-5.4 model isn't enabled on your account yet.
    #
    # Phase 2 split: the storyteller is now the Narrator's EXECUTE pass and
    # is promoted to premium tier (this is the one stage readers taste).
    # The Narrator's OUTLINE pass runs on `orchestrator` (mid tier) via the
    # `run_chapter_outline` call.
    "specialist":   ["gpt-5.4-nano", "gpt-4o-mini"],
    "orchestrator": ["gpt-5.4-mini", "gpt-4o"],
    "storyteller":  ["gpt-5.4",      "gpt-4o"],
    "editor":       ["gpt-5.4",      "gpt-4o"],
}

VALID_DOMAINS = ("ecology", "economy", "geopolitics", "society", "culture")
CAST_MAX = 6                # hard ceiling on main_cast per epoch
FRESHNESS_WINDOW = 2        # epochs — prefer introducing a new character if none in last N
DORMANT_AFTER = 3           # epochs without appearing -> status "dormant"

# ------ Phase 4 tuning ----------------------------------------------------- #
# Cross-interference rotation (§pipeline step 4): if more than this fraction
# of interactions touch the chosen fork's domain, re-prompt for ≥2 that
# don't. The analyst otherwise over-indexes on the fork's domain and the
# world shrinks around it.
CROSS_INTERFERENCE_FORK_DOMAIN_LIMIT = 0.60

# Anti-lock-in on forks: at least one of the three proposed forks must be
# in a domain NOT used as the chosen fork in the last N years (plan §2
# pipeline step 9 — "at least one fork must come from a region/topic not
# dominant in the last 2 years").
FORK_ANTI_LOCKIN_WINDOW = 2

# Off-page-event consecutive-use guard. If the last N years ALL used the
# off-page tool, the beat-sheet prompt is told to prefer on-page for this
# year unless the dramatic fit is strong. Tracked via chapter_index.json
# (plan §10 Phase 4: "track off-page-event use so consecutive years don't
# all evade the big event").
OFF_PAGE_CONSECUTIVE_LIMIT = 2

# Continuity pass (plan §pipeline step 8). One retry max via the editor
# with a targeted FIX: block; beyond that, the chapter ships with
# degraded: true in the continuity report for later human review.
CONTINUITY_RETRY_MAX = 1
CONTINUITY_MIN_HOOKS_RESOLVED = 2   # if previous chapter exists
CONTINUITY_MIN_HOOKS_PLANTED = 2

# ------ v4 tuning ---------------------------------------------------------- #
# v4 plan §3 (dramatic spine), §5 (scene contract + change audit).

# Fork types (v4 plan §2.3). Forks must be named, irreversible acts; trends
# are rejected. "technology-fielded" is a technology that GOT DEPLOYED —
# the first shot, the first convoy, the first ruling — not an abstract
# capability-increase.
VALID_FORK_TYPES: tuple[str, ...] = (
    "event",
    "technology-fielded",
    "person-enters",
    "person-exits",
)

# Hook types (v4 plan §3.5). `dramatic-seed` is a promise of drama in the
# next 1–3 years; `world-seed` is a slower worldbuilding thread;
# `admin-carry-over` is the procedural residue of THIS year (a pending
# audit, a scheduled hearing) that must be mentioned but doesn't need
# to generate scenes on its own. Only dramatic-seeds count toward the
# planted-hooks quota.
VALID_HOOK_TYPES: tuple[str, ...] = (
    "dramatic-seed", "world-seed", "admin-carry-over",
)
DRAMATIC_SEED_MIN_PER_YEAR = 1  # v4 floor

# Irreversible event types (v4 plan §3.3). A chapter must ratify at least
# one irreversible act on-page (or, if off-page, by depicting its
# aftermath in scene). "decision-enacted" is a decision that is carried
# out in the world, not just deliberated.
VALID_IRREVERSIBLE_TYPES: tuple[str, ...] = (
    "decision-enacted",
    "loss",
    "defection",
    "arrival",
    "departure",
    "rupture",
    "first-use",
    "death",
    "birth",
)
IRREVERSIBLE_MIN_PER_YEAR = 1

# Scene-contract fields (v4 plan §2.2). Every scene in the outline must
# declare these six beats. `embodied-gesture` is the specific physical
# action the scene's meaning rides on; `unresolved-subtext` is what the
# scene refuses to resolve. These are the v4 replacement for v3's `line`.
SCENE_CONTRACT_FIELDS: tuple[str, ...] = (
    "desire",                 # what the POV character wants IN THIS MOMENT
    "obstacle",               # what prevents them getting it
    "turn",                   # how the scene's pressure changes direction
    "cost",                   # the price paid for the turn (even if off-stage)
    "embodied_gesture",       # a specific physical action the meaning rides on
    "unresolved_subtext",     # the thing the scene refuses to resolve
)

# Continuity-pass v4 additions.
CHANGE_AUDIT_MIN_CHANGED_MAINS = 1   # ≥1 main must be `changed` each year
CHANGE_AUDIT_UNCHANGED_STREAK_LIMIT = 3  # flag mains unchanged N years running
IN_SCENE_WORDS_MIN_RATIO = 0.65      # ≥65% of chapter words in continuous scene
COLLISION_CAST_THRESHOLD = 3         # ≥N mains => require a collision scene

# Year-dilemma (v4 plan §3.2): summariser emits choice_a/choice_b with
# equal stakes, a clock, and a wager. A dilemma is stronger than a
# thesis because both options have a cost.
YEAR_DILEMMA_REQUIRED_FIELDS: tuple[str, ...] = (
    "actor", "choice_a", "choice_b", "stakes_a", "stakes_b",
    "clock", "wager",
)

# Decade spine (v4 plan §3.1; v5 adds promise_lines). Written once, at run
# start, after the cast bootstrap. It names the 10-year dramatic question, the
# countdown, the three-act structure, and the wager. Injected into every
# per-year stage.
DECADE_SPINE_REQUIRED_FIELDS: tuple[str, ...] = (
    "question", "wager", "countdown", "acts",
)
DECADE_SPINE_ACT_FIELDS: tuple[str, ...] = (
    "act", "name", "promise", "year_range",
)

# ------ v5 tuning ---------------------------------------------------------- #
# v5 plan: variance budget, long-arc debt ledger, and typed rupture slot.

VALID_TIME_SCALES: tuple[str, ...] = (
    "single-hour-real-time",
    "single-day",
    "weeks-compressed",
    "season",
    "multi-year-flashforward",
    "letter-from-future",
    "historical-zoom",
    "dream-or-rumour",
)

VALID_PLOT_SHAPES: tuple[str, ...] = (
    "decision-under-pressure",
    "pursuit",
    "arrival",
    "departure",
    "failure-and-its-aftermath",
    "discovery",
    "ambush",
    "confession",
    "negotiation",
    "reckoning",
)

SETTING_COOLDOWNS: dict[str, int] = {
    "place_signature": 3,
    "place_family": 2,
    "pov_gravity_well_id": 2,
    "time_scale": 2,
    "plot_shape": 2,
    "irreversible_event_types": 2,
}
VARIANCE_OVERRIDE_WINDOW = 4

VALID_HORIZON_CLASSES: tuple[str, ...] = ("near", "mid", "long", "decade")
LONG_HORIZON_CLASSES: tuple[str, ...] = ("long", "decade")
DEBT_NEAR_MAX_FRACTION = 0.60

VALID_RUPTURE_TYPES: tuple[str, ...] = (
    "withheld-information-revealed",
    "side-character-takeover",
    "off-stage-rupture-on-stage",
    "expected-outcome-reversed",
    "time-jump-mid-chapter",
    "unscheduled-character-loss",
    "rumour-or-omen",
    "genre-tilt",
)
RUPTURE_FORCED_AFTER_QUIET_YEARS = 4
RUPTURE_CONSECUTIVE_CAP = 3

# ------ Phase 5 tuning ----------------------------------------------------- #
# Ordered pipeline stages per year. The ids mirror the numeric prefixes used
# in year_<YYYY>/ folders so `ls` and `--from-stage` share a vocabulary.
# `replay.py <run_id> --from-stage <id>` loads everything before the chosen
# stage from disk and recomputes from there. See `generate_epoch(start_from=)`.
#
# Ids are deliberately string-typed because one of them is "06a" / "06b" /
# "06c" / "06d" (the mastermind sub-stages) — a plain integer index would
# lose the letter.
STAGE_ORDER: tuple[str, ...] = (
    "02",    # specialists (+ 03 state merger, which is a pure code op)
    "04",    # summariser (v4: emits year_dilemma)
    "05",    # cross-interference
    "06a",   # cast plan (v4: decade_spine + unchanged-streak aware)
    "06b",   # character dossiers
    "06c",   # beat sheet (v4: typed hooks + irreversible events)
    "06d",   # chapter outline (v4: mode + scene contract)
    "06e",   # rupture authorisation (v5: cheap, optional, typed)
    "06f",   # narrator execute (writes 06f_story_draft.md)
    "07",    # editor (writes 07_story_final.md)
    "07b",   # continuity pass (v4: change_delta, in-scene ratio,
             # collision, irreversibility). May retry the editor once
             # and overwrite 07_story_final.md
    "08",    # fork proposer (v4: typed forks with spine_wager_impact)
    "09",    # readability metrics (pure code)
)

# v4 decade_spine is a ONE-TIME run artefact at runs/<run_id>/00_decade_spine.json
# (not per-year), so it sits outside STAGE_ORDER's per-year flow. It is
# computed in main() after cast bootstrap and read by per-year stages.

# ------ Phase 2: chapter structure menu + mood budgets --------------------- #
# LEGACY (pre-v4). The v3 "structure" menu is kept for backward-compat reads
# of existing chapter_index.json entries and for replay on old runs. NEW
# outlines emit `mode` (see below) instead. chapter_index stores both for
# a grace period — whichever is populated wins.
STRUCTURE_MENU: tuple[str, ...] = (
    "braided-povs",
    "fragment-dossier",
    "single-pov-year",
    "before-during-after",
    "case-study-frame",
    "chorus",
    "recursive",
    "committee-ledger",
    "letters",
    "historian-introduces-witness",
)

STRUCTURE_WINDOW = 3        # same structure may not recur within N years

VALID_MOODS: tuple[str, ...] = (
    "acute", "drift", "reckoning", "turning", "quiet",
)

# ------ v4: chapter MODES (replace "structure" as the primary shape slot) -- #
# v4 plan §2.1. A mode specifies scene count, length distribution, and
# register expectations. v3's "structure" menu rewarded short captioned
# tableaux; modes force FEW LONG scenes instead. `mosaic` is what v3
# always produced by default — we cap it at 1 in every 4 years.
#
# (min_scenes, max_scenes, scene_word_low, scene_word_high, chapter_word_low,
#  chapter_word_high, notes) — the outliner's `scene_budget` length must
# sit in [min, max]; its `word_budget.low/high` must sit within
# [chapter_word_low, chapter_word_high] AND respect the mood's range
# (we take the intersection). Per-scene target length is the outline
# hint the narrator is told to hit.
CHAPTER_MODES: dict[str, dict] = {
    "monoscene": {
        "min_scenes": 1, "max_scenes": 1,
        "scene_word_low": 1800, "scene_word_high": 2600,
        "chapter_word_low": 1800, "chapter_word_high": 2600,
        "description": (
            "One long scene. One location. One continuous time (minutes to "
            "hours). Everything else is off-page. Demands interiority; bans "
            "mosaic-style dispatches."
        ),
        "allowed_moods": {"acute", "reckoning", "turning", "quiet"},
        "requires_interiority": True,
        "dialogue_floor": 0.0,
    },
    "diptych": {
        "min_scenes": 2, "max_scenes": 2,
        "scene_word_low": 900, "scene_word_high": 1300,
        "chapter_word_low": 1800, "chapter_word_high": 2400,
        "description": (
            "Two scenes that mirror or collide. Same hour or same subject, "
            "opposite institutional power. A rhyme."
        ),
        "allowed_moods": {"acute", "drift", "reckoning", "turning"},
        "requires_interiority": False,
        "dialogue_floor": 0.0,
    },
    "triptych": {
        "min_scenes": 3, "max_scenes": 3,
        "scene_word_low": 600, "scene_word_high": 900,
        "chapter_word_low": 1800, "chapter_word_high": 2400,
        "description": (
            "Three scenes in a causal chain. A -> B -> C, where A makes B "
            "possible and B forces C."
        ),
        "allowed_moods": {"acute", "drift", "reckoning", "turning"},
        "requires_interiority": False,
        "dialogue_floor": 0.0,
    },
    "long-march": {
        "min_scenes": 1, "max_scenes": 1,
        "scene_word_low": 1800, "scene_word_high": 2500,
        "chapter_word_low": 1800, "chapter_word_high": 2500,
        "description": (
            "A single continuous journey, one POV, multiple locations. "
            "Movement as dramatic engine. Time passes concretely — "
            "morning to night, station to station."
        ),
        "allowed_moods": {"acute", "drift", "reckoning", "turning", "quiet"},
        "requires_interiority": True,
        "dialogue_floor": 0.0,
    },
    "overheard": {
        "min_scenes": 2, "max_scenes": 3,
        "scene_word_low": 600, "scene_word_high": 1000,
        "chapter_word_low": 1500, "chapter_word_high": 2200,
        "description": (
            "Dialogue-forward. At least 60% of chapter words must be in "
            "direct or reported speech. No narrator summary paragraphs."
        ),
        "allowed_moods": {"acute", "drift", "reckoning", "turning"},
        "requires_interiority": False,
        "dialogue_floor": 0.60,
    },
    "mosaic": {
        "min_scenes": 4, "max_scenes": 6,
        "scene_word_low": 150, "scene_word_high": 300,
        "chapter_word_low": 900, "chapter_word_high": 1600,
        "description": (
            "Short numbered/dated dispatches. Fragment-dossier energy. "
            "CAPPED at 1 in every 4 years — this is what v3 produced by "
            "default; v4 must not default to it."
        ),
        "allowed_moods": {"drift", "reckoning", "quiet"},
        "requires_interiority": False,
        "dialogue_floor": 0.0,
    },
}

VALID_MODES: tuple[str, ...] = tuple(CHAPTER_MODES.keys())

# v4 mode-repeat window (plan §2.1): same mode may not recur within N years.
MODE_REPEAT_WINDOW = 2

# v4 mosaic cap: may not exceed 1 occurrence in every MOSAIC_CAP_WINDOW years.
MOSAIC_CAP_WINDOW = 4
MOSAIC_CAP = 1

# Legacy mood budget retained so ANY outline that still emits `structure`
# (replay on old runs) stays valid. The v4 validator prefers mode's
# chapter-word range when `mode` is populated.
MOOD_BUDGETS: dict[str, tuple[int, int, int]] = {
    "acute":     (3, 1100, 1400),
    "drift":     (2,  600,  800),
    "reckoning": (3, 1000, 1200),
    "turning":   (4, 1200, 1600),
    "quiet":     (1,  500,  700),
}

# Legacy cap retained for replay on v3 outlines. v4 outlines are capped by
# CHAPTER_MODES[mode].max_scenes instead.
SCENES_CAP = 6

# ------ Phase 3: voice palette (base x modulator x device) ----------------- #
# Plan §5.1. Each chapter composes its voice from three independent axes:
#   BASE     — overall register
#   MODULATOR — tonal colour layered on the base
#   DEVICE    — an Oulipo-style one-chapter constraint
# The outline picks one of each from a code-computed candidate set (§5.2).
# Same base/modulator/device may not recur within PALETTE_WINDOW years
# (tracked in chapter_index.json), so depth-3 runs vary audibly.
#
# Each entry carries a ~30-word EXEMPLAR so the Narrator sees a target
# texture, not an abstract description (plan §5.1).

VOICE_BASES: dict[str, dict[str, str]] = {
    # -- v3 originals (kept) ------------------------------------------------ #
    "retrospective": {
        "description": "Foundation-narrator long view. Sentences survey years; the historian stands slightly above the events.",
        "exemplar": "The Compact's early pilots were judged by their third harvest; by the fifth, only the coastal parishes were still signing.",
    },
    "dossier": {
        "description": "Encyclopedia-Galactica fragments. Numbered clippings, memos, field notes, entries — artefactual rather than narrated.",
        "exemplar": "FIELD NOTE, 17 APR — Algal mat, 9 m wide, south of the seawall. Smell: iron, faint sweetness. Apprentice who spotted it: unrecorded.",
    },
    "reported": {
        "description": "Newsroom remove. Datelines, named sources, dated verbs, quotations; the narrator is a wire-service reporter with taste.",
        "exemplar": "ABIDJAN — A truce that had held for eleven months on paper held for three days in the north, according to two officers who asked not to be named.",
    },
    "memoir": {
        "description": "Close first-person. One character's year, small in frame, interior; the camera never leaves their shoulder.",
        "exemplar": "I kept the receipt for months. Not because it mattered, but because it was the last thing my handwriting looked unchanged on.",
    },
    # -- v4 additions (plan §5.1) ------------------------------------------ #
    # Every v3 base lands in detached register. These four force embodied,
    # conversational, or sustained-location texture.
    "close-third": {
        "description": "Tight third-person POV. The camera stays on one body moving through one place. We feel skin, weight, hesitation; interiority in free indirect style.",
        "exemplar": "She lifted the clipboard and the pages lifted too late, a breath later than her hand, and she knew before she looked that the top sheet would be the one she had not meant to bring.",
    },
    "dialogue-scene": {
        "description": "Conversation as primary engine. Sustained exchanges drive the chapter. Narrator intrudes only for gesture and atmosphere.",
        "exemplar": "\"It isn't refusal, Anjali.\" \"It's a refusal with better paperwork.\" Rajiv set the form back on the desk and did not let go of it.",
    },
    "letter": {
        "description": "A single voice writing to a named other. Dated. Personal address. The reader is reading over a shoulder; the recipient is the chapter's centre of gravity.",
        "exemplar": "Dear Leila — I keep the memo in my drawer the way you used to keep the hearing transcripts. I think you were right about the second paragraph. I am not ready to say which part.",
    },
    "long-cam": {
        "description": "A single location observed across hours. Many bodies pass through. The place, not a person, is the protagonist; people are weather.",
        "exemplar": "At six the first clerk came in, at seven the queue formed, at nine the window closed for reasons the board wouldn't reveal until afternoon; the bench outside held everyone in turn.",
    },
}

VOICE_MODULATORS: dict[str, dict[str, str]] = {
    # -- v3 originals (kept) ------------------------------------------------ #
    "elegiac": {
        "description": "Loss, slow goodbyes, turning-year light. Things end without being mourned aloud.",
        "exemplar": "The pier lasted one more winter than anyone had bet on, and then it did not.",
    },
    "ironic": {
        "description": "Dry humour at the absurdity of procedure. The comedy is structural, not jokey.",
        "exemplar": "The guidance was reissued on the same date as the previous guidance, which it now superseded.",
    },
    "forensic": {
        "description": "Evidence-forward. Names, numbers, chain of custody, paper trail; feelings enter through documents.",
        "exemplar": "Exhibit 14 was a spreadsheet with 812 rows. Rows 3 through 196 had been edited on a Sunday.",
    },
    "pastoral": {
        "description": "Quiet, weather, close attention to physical objects and their persistence.",
        "exemplar": "The chicory in the lot by the substation bloomed for nine days in late August, then went to stalk.",
    },
    "polyphonic": {
        "description": "Chorus of voices; no sustained POV. Claims overlap, contradict, trail off.",
        "exemplar": "Someone said it was the heat; someone said it was the tariffs; someone said it was always going to be this way.",
    },
    # -- v4 additions (plan §5.1) ------------------------------------------ #
    # v3's five all skew detached. These five push toward inner weather, the
    # body, the kitchen table, and the ungoverned tongue.
    "interior": {
        "description": "Inward weather. Doubt, calculation, private shame, memory crossing the present. Thought rendered at sentence-level, not summarised.",
        "exemplar": "She had been ready to say no at ten, then ready to say yes at ten-fifteen; at the door she understood she had been deciding for a year, not an hour.",
    },
    "domestic": {
        "description": "Private spaces: kitchens, waiting rooms, cars, stairwells. The political flows through the personal; nothing of scale unless a body feels it.",
        "exemplar": "He made tea while she read the letter. The kettle was the loudest thing in the flat until she said his name without looking up.",
    },
    "bodily": {
        "description": "Physical register. Hands, breath, sweat, weight, stiffness, the small injury. A chapter that earns its reality through flesh.",
        "exemplar": "Her calf had been numb since the third station; she stamped it on the platform and the feeling came back in one sick wave.",
    },
    "wry-spoken": {
        "description": "Conversation with a sense of humour, dry and mostly at its own expense. Lines land with the timing of lived speech, not editorial wit.",
        "exemplar": "\"We are doing well.\" \"Are we?\" \"We are doing the paperwork for doing well, which is almost the same thing.\"",
    },
    "angry": {
        "description": "Cold or hot anger held without being declared. Fewer qualifiers. Short sentences. A line that won't be unsaid.",
        "exemplar": "She did not raise her voice. She put the pen down on the table and did not lift it again until he had left the room.",
    },
}

# Oulipo-style one-chapter constraints. The narrator must honour the chosen
# device throughout; the editor may relax it only if it actively fights
# the year_mood.
#
# v4 (plan §5.1): devices are now typed. `embodiment` devices FORCE dialogue,
# bodily detail, or sustained single-scene attention. `suppressive` devices
# (the v3 "X is forbidden"/"no Y speaks") cap at 1-in-N chapters because
# they bias the register toward detachment. `texture` devices sit between.
# `every-section-opens-on-a-date` + `one-paragraph-per-month` are retired
# as chapter-level devices in v4: they fight the mode-based scene economy
# (they belong to mosaic, which v4 caps at 1-in-4).
VOICE_DEVICES: dict[str, dict[str, str]] = {
    # -- v4 embodiment devices (new) --------------------------------------- #
    "one-scene-in-one-hour": {
        "description": "The chapter's longest scene must render a single continuous hour of clock-time in real or near-real rhythm. No summary skips inside it.",
        "exemplar": "From 2:40 to 3:30 the room did one thing: the clerk wrote, the three of them watched him write, and the radiator, at intervals, ticked.",
        "kind": "embodiment",
    },
    "two-voices-alternating": {
        "description": "Two named characters alternate line by line through a sustained exchange. No three-voice scenes. Narrator intrusion is minimal.",
        "exemplar": "\"You signed it.\" \"I signed it under the heading you suggested.\" \"Which was your sentence.\" \"Which was your edit of my sentence.\"",
        "kind": "embodiment",
    },
    "one-body-detail-per-paragraph": {
        "description": "Every paragraph contains at least one concrete body detail — a hand, a breath, weight on a chair, a hem, a limp.",
        "exemplar": "He wrote the note and folded it twice, the second fold clumsy because his thumbnail had torn earlier and the pad of his thumb was taped.",
        "kind": "embodiment",
    },
    "no-institution-named": {
        "description": "No institution, agency, party, or corporation is named in the chapter. Power exists only through persons and rooms.",
        "exemplar": "She did not say which office had sent her. She put the envelope on the table. The table had been her mother's table once.",
        "kind": "embodiment",
    },
    # -- v4 texture devices (new) ------------------------------------------ #
    "every-scene-contains-food": {
        "description": "Every scene contains food or drink being prepared, served, eaten, refused, or cleared. Domestic weight, not set-dressing.",
        "exemplar": "She poured the tea, then forgot it; the cup was cold by the time she told him. He drank it anyway, to keep his hands occupied.",
        "kind": "texture",
    },
    # -- v3 originals retained, typed ------------------------------------- #
    # kept as-is because they still earn their keep; marked so the picker
    # can cap suppressive types.
    "every-scene-contains-weather": {
        "description": "Every scene must note the weather, however briefly — light, wind, temperature, damp, dust.",
        "exemplar": "The hearing ran long; outside, the sleet that had been forecast for morning arrived, finally, at four.",
        "kind": "texture",
    },
    "exactly-three-quotations": {
        "description": "Exactly three direct quotations in the chapter — no more, no fewer. Other speech must be reported or paraphrased.",
        "exemplar": "Three sentences were said aloud in this chapter. The rest were on paper, or in the minutes, or understood.",
        "kind": "texture",
    },
    "central-character-never-described": {
        "description": "The chapter's central character is never described physically. We know them by what they do and say, not by face or body.",
        "exemplar": "You would not have recognised her in a crowd. You would have recognised her handwriting on the margin of the report.",
        "kind": "texture",
    },
    "no-abstract-noun-subjects": {
        "description": "No abstract noun is the subject of a sentence for the first 200 words. Concrete nouns only drive the opening.",
        "exemplar": "The crane stopped. The foreman climbed down. The foreman put a hand on the crane-rail and waited for it to stop being hot.",
        "kind": "texture",
    },
    # -- v3 suppressive devices, capped in v4 ----------------------------- #
    "no-public-official-dialogue": {
        "description": "No dialogue from public officials; only private citizens speak aloud. Officials may act; they may be quoted via paraphrase; they may not speak in direct speech.",
        "exemplar": "The governor's office issued a two-sentence statement. On the porch, the neighbour said only: \"My mother won't go inside.\"",
        "kind": "suppressive",
    },
    "word-history-forbidden": {
        "description": "The word 'history' (and 'historical') does not appear in the chapter. Historians may be present; the word may not be.",
        "exemplar": "They were not pretending this had not happened before. They just did not have a word for it that didn't belong to someone else.",
        "kind": "suppressive",
    },
}

# v4: suppressive devices may not be used more than SUPPRESSIVE_DEVICE_CAP
# times in SUPPRESSIVE_DEVICE_WINDOW years. They bias toward detachment;
# they are the exception, not the default.
SUPPRESSIVE_DEVICE_WINDOW = 4
SUPPRESSIVE_DEVICE_CAP = 1

# Same palette axis pick may not recur within this window (years).
PALETTE_WINDOW = 3

# ------ Phase 3: slop ledger ----------------------------------------------- #
# Plan §5.4. Seed phrases are blocked at startup and refresh their cooldown
# if they appear in a final chapter. The editor is told, per chapter, which
# phrases are currently in the window; it must avoid them. A small code-side
# scan after the editor re-arms cooldowns on any seeded phrase the editor
# let through (rather than paying for another LLM call).

SLOP_WINDOW = 3

SEEDED_SLOP_PHRASES: list[dict[str, str]] = [
    # v2's repeating tics (plan §5.4)
    {"phrase": "Every truce purchases its own breakdown.",
     "note": "v2 ledger tic — signature refrain"},
    {"phrase": "They were describing the same thing.",
     "note": "v2 dual-naming construction"},
    # Retrospective historian openers — banned by Phase 2 but tracked here too
    {"phrase": "The year YYYY was the year in which",
     "note": "retrospective-historian opener"},
    {"phrase": "By year's end",
     "note": "retrospective-historian opener"},
    {"phrase": "In YYYY,",
     "note": "retrospective-historian opener"},
    # Generic AI-essay slop
    {"phrase": "a stark reminder",
     "note": "news-slop"},
    {"phrase": "stood as a testament",
     "note": "essay-slop"},
    {"phrase": "in a world where",
     "note": "essay-slop"},
    {"phrase": "navigate the complexities",
     "note": "essay-slop"},
    {"phrase": "delicate balance",
     "note": "essay-slop"},
    {"phrase": "seismic shift",
     "note": "hype"},
    {"phrase": "paradigm shift",
     "note": "hype"},
    {"phrase": "unprecedented",
     "note": "hype adjective"},
]

HERE = Path(__file__).parent
SEED_PATH = HERE / "seed_2026.json"
STYLE_ASIMOV_PATH = HERE / "style_asimov.md"
RUNS_DIR = HERE / "runs"
CHARACTERS_SUBDIR = "characters"


# --------------------------------------------------------------------------- #
# Small utilities
# --------------------------------------------------------------------------- #

def _print_rule(title: str = "") -> None:
    bar = "-" * 78
    if title:
        print(f"\n{bar}\n  {title}\n{bar}")
    else:
        print(bar)


def _pretty_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(_pretty_json(obj), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _merge_specialist_updates(state: dict, facet_updates: dict) -> dict:
    """Top-level facet replacement."""
    new_state = copy.deepcopy(state)
    for facet, value in facet_updates.items():
        new_state[facet] = value
    return new_state


# --------------------------------------------------------------------------- #
# Chapter index (Phase 2)
#
# Per-year record of the structural choices the Narrator outline made, so the
# next outline can honor the no-repeat-within-3-years rule on `structure` and
# so later phases can read scene counts / palette without re-parsing prose.
# --------------------------------------------------------------------------- #

def _chapter_index_path(run_dir: Path) -> Path:
    return run_dir / "chapter_index.json"


def _load_chapter_index(run_dir: Path) -> dict:
    path = _chapter_index_path(run_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"chapters": []}


def _save_chapter_index(run_dir: Path, index: dict) -> None:
    _write_json(_chapter_index_path(run_dir), index)


def _recent_structures(index: dict, window: int = STRUCTURE_WINDOW) -> list[str]:
    """Most-recent-first list of structures used in the last `window`
    chapters. LEGACY (pre-v4); still consulted on replay over old runs
    where `structure` exists. New v4 outlines write `mode` instead; use
    `_recent_modes` for the v4 equivalent."""
    chapters = sorted(index.get("chapters", []),
                      key=lambda c: c.get("year", 0), reverse=True)
    return [c["structure"] for c in chapters[:window] if c.get("structure")]


def _recent_modes(index: dict, window: int = MODE_REPEAT_WINDOW) -> list[str]:
    """v4 equivalent of _recent_structures. Most-recent-first list of
    chapter `mode` values used in the last `window` chapters. Used by
    the outliner's mode-freshness rule (same mode may not recur within
    MODE_REPEAT_WINDOW years)."""
    chapters = sorted(index.get("chapters", []),
                      key=lambda c: c.get("year", 0), reverse=True)
    return [c["mode"] for c in chapters[:window] if c.get("mode")]


def _mosaic_cap_saturated(index: dict) -> bool:
    """v4: mosaic may not exceed MOSAIC_CAP occurrences in every
    MOSAIC_CAP_WINDOW years. Returns True if the cap is already met
    and the outliner must not pick mosaic."""
    chapters = sorted(index.get("chapters", []),
                      key=lambda c: c.get("year", 0), reverse=True
                      )[:MOSAIC_CAP_WINDOW]
    mosaic_count = sum(1 for c in chapters if c.get("mode") == "mosaic")
    return mosaic_count >= MOSAIC_CAP


def _unchanged_streaks(index: dict, *, current_year: int,
                       streak_limit: int = CHANGE_AUDIT_UNCHANGED_STREAK_LIMIT
                       ) -> list[str]:
    """v4: return character ids whose continuity-pass change_audit has
    marked them `unchanged` for `streak_limit` consecutive years
    (counting backwards from the most recent year < current_year). The
    cast-plan prompt must retire or force-change these characters.

    A character breaks its streak the first year it is either
    `changed` OR absent from the main_cast (absence is treated as a
    natural reset — a dormanted character is not "unchanged on-page",
    it is "elsewhere"). The old implementation iterated the year's
    cast_ids only, so an absent year became a no-op rather than a
    reset — a character who was unchanged in 2028, absent in 2029,
    then unchanged in 2030 would (wrongly) accumulate a streak of 2
    and trip the 3-year flag the next time they reappeared. Iterate
    per-character instead so absence short-circuits the run.
    """
    chapters = sorted(
        (c for c in index.get("chapters", [])
         if isinstance(c.get("year"), int) and c["year"] < current_year),
        key=lambda c: c["year"], reverse=True,
    )
    # Every id we've ever seen in a cast_ids list is a candidate.
    candidate_ids: set[str] = set()
    for c in chapters:
        for cid in (c.get("cast_ids") or []):
            if isinstance(cid, str) and cid:
                candidate_ids.add(cid)

    streaks: list[str] = []
    for cid in candidate_ids:
        run = 0
        for c in chapters:
            cast_ids = c.get("cast_ids") or []
            if cid not in cast_ids:
                break  # absence resets the consecutive run
            entry = (c.get("change_audit") or {}).get(cid) or {}
            if entry.get("verdict") == "unchanged":
                run += 1
                continue
            break  # `changed` (or missing verdict) also resets
        if run >= streak_limit:
            streaks.append(cid)
    return sorted(streaks)


def _append_chapter_index(
    index: dict, *, year: int, outline: dict,
    chosen_fork_domain: str | None = None,
    off_page_used: bool = False,
    hooks_planted: list[dict] | list[str] | None = None,
    cast_ids: list[str] | None = None,
    continuity_verdict: str | None = None,
    change_audit: dict | None = None,
    irreversible_events_observed: list[dict] | None = None,
    year_dilemma: dict | None = None,
) -> None:
    """Append this chapter's outline + Phase-4 + v4 context to the index.

    v4 additions:
    - `mode`                      — outline's chosen mode (replaces structure
                                    as the primary shape slot). `structure`
                                    is still recorded from any legacy outline
                                    that still emits it, for backward reads.
    - `change_audit`              — per-main {verdict, axis} from the
                                    continuity pass, used next year to
                                    compute `_unchanged_streaks`.
    - `irreversible_events_observed` — the continuity report's observed
                                    events; lets later stages inspect the
                                    run's irreversibility profile.
    - `year_dilemma`              — the summariser's dilemma object, kept
                                    on the chapter row for readability
                                    metrics and grep-across-run review.
    - `hooks_planted`             — now stored AS OBJECTS (hook_id, type,
                                    subtype, ripens_by_year, hook, stake)
                                    instead of plain strings. Code that
                                    reads this still handles the legacy
                                    list[str] shape.

    Idempotent on `year` (re-runs replace the entry rather than duplicate).
    """
    entry = {
        "year": year,
        "mode": outline.get("mode"),
        "structure": outline.get("structure"),
        "year_mood": outline.get("year_mood"),
        "scenes_count": len(outline.get("scene_budget", []) or []),
        "word_budget": outline.get("word_budget", {}),
        "voice_palette": outline.get("voice_palette", {}),
        "readers_compass": outline.get("readers_compass", {}),
        "chosen_fork_domain": chosen_fork_domain,
        "off_page_used": bool(off_page_used),
        "hooks_planted": list(hooks_planted or []),
        "cast_ids": list(cast_ids or []),
        "continuity_verdict": continuity_verdict,
        "change_audit": dict(change_audit or {}),
        "irreversible_events_observed": list(irreversible_events_observed or []),
        "year_dilemma": dict(year_dilemma or {}),
    }
    index["chapters"] = [c for c in index.get("chapters", []) if c.get("year") != year]
    index["chapters"].append(entry)


def _recent_chapters(index: dict, window: int) -> list[dict]:
    """Return the most-recent-first chapter entries, up to `window`."""
    chapters = sorted(index.get("chapters", []),
                      key=lambda c: c.get("year", 0), reverse=True)
    return chapters[:window]


def _recent_off_page_uses(index: dict, window: int = OFF_PAGE_CONSECUTIVE_LIMIT
                           ) -> list[int]:
    """Years in the last `window` that used an off-page event. Most recent
    first. Used by the beat sheet to avoid cumulative evasion."""
    return [c["year"] for c in _recent_chapters(index, window)
            if c.get("off_page_used")]


def _recent_fork_domains(index: dict, window: int = FORK_ANTI_LOCKIN_WINDOW
                          ) -> list[str]:
    """Chosen-fork domains from the last `window` chapters, most recent
    first. Used by the fork proposer to require ≥1 fork from outside
    that set (anti-lock-in, plan §2 step 9)."""
    return [c["chosen_fork_domain"] for c in _recent_chapters(index, window)
            if c.get("chosen_fork_domain")]


def _recent_central_tensions(index: dict, window: int = 3) -> list[str]:
    """v5: anti-repetition memory for the summariser."""
    tensions: list[str] = []
    for c in _recent_chapters(index, window):
        yd = c.get("year_dilemma") or {}
        wager = yd.get("wager") if isinstance(yd, dict) else None
        if isinstance(wager, str) and wager.strip():
            tensions.append(wager.strip())
    return tensions


def _previous_chapter_entry(index: dict, current_year: int) -> dict | None:
    """The chapter_index entry for the year just before current_year, if
    any. Used by the continuity pass to find hooks_to_plant that SHOULD
    now be resolved or acknowledged."""
    for c in sorted(index.get("chapters", []),
                    key=lambda x: x.get("year", 0), reverse=True):
        if c.get("year") == current_year - 1:
            return c
    return None


# --------------------------------------------------------------------------- #
# v5: setting ledger, debt ledger, rupture log
# --------------------------------------------------------------------------- #

def _setting_ledger_path(run_dir: Path) -> Path:
    return run_dir / "setting_ledger.json"


def _load_setting_ledger(run_dir: Path) -> dict:
    path = _setting_ledger_path(run_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"entries": []}


def _save_setting_ledger(run_dir: Path, ledger: dict) -> None:
    _write_json(_setting_ledger_path(run_dir), ledger)


def _debt_ledger_path(run_dir: Path) -> Path:
    return run_dir / "debt_ledger.json"


def _load_debt_ledger(run_dir: Path) -> dict:
    path = _debt_ledger_path(run_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"debts": []}


def _save_debt_ledger(run_dir: Path, ledger: dict) -> None:
    _write_json(_debt_ledger_path(run_dir), ledger)


def _rupture_log_path(run_dir: Path) -> Path:
    return run_dir / "rupture_log.json"


def _load_rupture_log(run_dir: Path) -> dict:
    path = _rupture_log_path(run_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"entries": []}


def _save_rupture_log(run_dir: Path, log: dict) -> None:
    _write_json(_rupture_log_path(run_dir), log)


def _horizon_class(planted_year: int, ripens_by_year: int | None) -> str:
    if not isinstance(ripens_by_year, int):
        return "near"
    delta = ripens_by_year - planted_year
    if delta <= 1:
        return "near"
    if delta <= 4:
        return "mid"
    if delta <= 7:
        return "long"
    return "decade"


def _open_debts(debt_ledger: dict) -> list[dict]:
    return [
        d for d in debt_ledger.get("debts", [])
        if isinstance(d, dict)
        and d.get("status", "open") in ("open", "advanced")
    ]


def _near_debt_fraction(debt_ledger: dict) -> float:
    debts = _open_debts(debt_ledger)
    if not debts:
        return 0.0
    near = sum(1 for d in debts if d.get("horizon_class") == "near")
    return near / len(debts)


def _act_for_year(decade_spine: dict | None, year: int) -> dict | None:
    if not decade_spine:
        return None
    for act in decade_spine.get("acts") or []:
        yr = act.get("year_range", "")
        nums = [int(n) for n in re.findall(r"\b(20\d{2}|21\d{2})\b", str(yr))]
        if len(nums) >= 2 and min(nums) <= year <= max(nums):
            return act
    return None


def _promise_line_ids_for_current_act(decade_spine: dict | None, year: int) -> set[str]:
    act = _act_for_year(decade_spine, year)
    if not act:
        return set()
    return {
        p.get("id") for p in (act.get("promise_lines") or [])
        if isinstance(p, dict) and p.get("id")
    }


def _claimed_promise_ids(setting_ledger: dict) -> set[str]:
    return {
        e.get("act_promise_claimed") for e in setting_ledger.get("entries", [])
        if isinstance(e, dict) and e.get("act_promise_claimed")
        and e.get("act_promise_realised", True) is not False
    }


def _setting_cooldown_context(setting_ledger: dict, *, current_year: int) -> dict:
    entries = [
        e for e in setting_ledger.get("entries", [])
        if isinstance(e, dict)
        and isinstance(e.get("year"), int)
        and e["year"] < current_year
    ]
    context: dict[str, list] = {}
    for axis, window in SETTING_COOLDOWNS.items():
        vals: list = []
        low = current_year - window
        for e in entries:
            if e["year"] < low:
                continue
            value = e.get(axis)
            if axis == "irreversible_event_types":
                vals.extend(value or [])
            elif value:
                vals.append(value)
        context[axis] = vals
    context["recent_variance_overrides"] = [
        e.get("year") for e in entries
        if e.get("variance_override")
        and e.get("year", 0) >= current_year - VARIANCE_OVERRIDE_WINDOW
    ]
    return context


def _outline_setting_entry(outline: dict, beat_sheet: dict, year: int) -> dict:
    irr_types = [
        ev.get("type") for ev in beat_sheet.get("irreversible_events") or []
        if isinstance(ev, dict) and ev.get("type")
    ]
    return {
        "year": year,
        "place_signature": outline.get("place_signature"),
        "place_family": outline.get("place_family"),
        "pov_gravity_well_id": outline.get("pov_gravity_well_id")
        or beat_sheet.get("dilemma_pov_character_id"),
        "time_scale": outline.get("time_scale") or outline.get("time_shape"),
        "plot_shape": outline.get("plot_shape"),
        "irreversible_event_types": irr_types,
        "act_promise_claimed": outline.get("act_promise_claimed")
        or beat_sheet.get("act_promise_claim"),
        "variance_override": outline.get("variance_override"),
    }


def _upsert_setting_ledger(
    run_dir: Path, *, year: int, outline: dict, beat_sheet: dict,
    continuity_report: dict,
) -> None:
    ledger = _load_setting_ledger(run_dir)
    entry = _outline_setting_entry(outline, beat_sheet, year)
    realised = continuity_report.get("setting_ledger_realised") or {}
    if isinstance(realised, dict):
        for k in (
            "place_signature", "place_family", "pov_gravity_well_id",
            "time_scale", "plot_shape", "irreversible_event_types",
        ):
            if realised.get(k):
                entry[k] = realised[k]
    entry["act_promise_realised"] = continuity_report.get("act_promise_realised")
    entry["setting_ledger_compliance"] = continuity_report.get("setting_ledger_compliance")
    entries = [e for e in ledger.get("entries", []) if e.get("year") != year]
    entries.append(entry)
    ledger["entries"] = sorted(entries, key=lambda e: e.get("year", 0))
    _save_setting_ledger(run_dir, ledger)


def _upsert_debt_ledger(
    run_dir: Path, *, year: int, beat_sheet: dict, continuity_report: dict,
) -> None:
    ledger = _load_debt_ledger(run_dir)
    debts = [d for d in ledger.get("debts", []) if d.get("planted_year") != year]
    by_id = {d.get("hook_id"): d for d in debts if d.get("hook_id")}

    for h in beat_sheet.get("hooks_to_plant") or []:
        if not isinstance(h, dict):
            continue
        hid = h.get("hook_id")
        if not hid:
            continue
        ripens = h.get("ripens_by_year")
        entry = {
            "hook_id": hid,
            "hook": h.get("hook", ""),
            "planted_year": year,
            "planted_in_chapter": f"year_{year}",
            "ripens_by_year": ripens,
            "horizon_class": h.get("horizon_class") or _horizon_class(year, ripens),
            "stake": h.get("stake", ""),
            "spine_act": h.get("spine_act"),
            "spine_promise_claim": h.get("spine_promise_claim")
            or beat_sheet.get("act_promise_claim"),
            "status": "open",
            "status_history": [{"year": year, "status": "open", "source": "beat_sheet"}],
        }
        by_id[hid] = entry

    for change in continuity_report.get("debt_ledger_discharged") or []:
        if not isinstance(change, dict):
            continue
        hid = change.get("hook_id")
        if not hid or hid not in by_id:
            continue
        new_status = change.get("new_status") or change.get("status") or "advanced"
        by_id[hid]["status"] = new_status
        by_id[hid].setdefault("status_history", []).append({
            "year": year,
            "status": new_status,
            "evidence": change.get("evidence", ""),
        })

    ledger["debts"] = sorted(by_id.values(), key=lambda d: (d.get("planted_year", 0), d.get("hook_id", "")))
    _save_debt_ledger(run_dir, ledger)


def _upsert_rupture_log(
    run_dir: Path, *, year: int, rupture_doc: dict, continuity_report: dict | None = None,
) -> None:
    log = _load_rupture_log(run_dir)
    rupture = rupture_doc.get("rupture") if isinstance(rupture_doc, dict) else None
    entry = {
        "year": year,
        "quiet": rupture is None,
        "rupture": rupture,
        "rupture_type": rupture.get("type") if isinstance(rupture, dict) else None,
    }
    if continuity_report:
        entry["realised"] = continuity_report.get("rupture_realised")
    entries = [e for e in log.get("entries", []) if e.get("year") != year]
    entries.append(entry)
    log["entries"] = sorted(entries, key=lambda e: e.get("year", 0))
    _save_rupture_log(run_dir, log)


def _rupture_constraints(log: dict, current_year: int) -> dict:
    entries = [
        e for e in log.get("entries", [])
        if isinstance(e, dict)
        and isinstance(e.get("year"), int)
        and e["year"] < current_year
    ]
    entries.sort(key=lambda e: e["year"], reverse=True)
    quiet_streak = 0
    ruptured_streak = 0
    for e in entries:
        if e.get("quiet"):
            if ruptured_streak:
                break
            quiet_streak += 1
            continue
        else:
            if quiet_streak:
                break
            ruptured_streak += 1
            continue
    recent_types = [e.get("rupture_type") for e in entries[:5] if e.get("rupture_type")]
    return {
        "quiet_streak": quiet_streak,
        "ruptured_streak": ruptured_streak,
        "force_rupture": quiet_streak >= RUPTURE_FORCED_AFTER_QUIET_YEARS,
        "must_be_quiet": ruptured_streak >= RUPTURE_CONSECUTIVE_CAP,
        "recent_types": recent_types,
    }


def _normalize_hooks(hooks: list) -> list[dict]:
    """v4 stores hooks_to_plant as objects; legacy runs stored plain
    strings. Normalise to a list of dicts so every consumer can treat
    them the same way. A legacy string becomes an admin-carry-over
    object (the safe default — it will not count toward the v4
    dramatic-seed quota)."""
    out: list[dict] = []
    for i, h in enumerate(hooks or []):
        if isinstance(h, dict):
            out.append(h)
        elif isinstance(h, str) and h.strip():
            out.append({
                "hook_id": f"legacy-{i}",
                "hook": h,
                "type": "admin-carry-over",
                "subtype": "legacy",
                "ripens_by_year": None,
                "stake": "",
            })
    return out


def _previous_hooks_typed(index: dict, current_year: int) -> list[dict]:
    """v4: return the previous chapter's hooks_to_plant as typed objects.
    Used by the beat-sheet prompt (which prioritises dramatic-seed
    pickups) and the continuity pass (which audits dramatic-seed
    resolution specifically)."""
    prev = _previous_chapter_entry(index, current_year)
    return _normalize_hooks((prev or {}).get("hooks_planted") or [])


def _previous_hooks_strings(index: dict, current_year: int) -> list[str]:
    """Legacy string-list view of previous hooks, kept for the editor
    retry block and for the read-only display strings."""
    return [h.get("hook", "") for h in _previous_hooks_typed(index, current_year)
            if h.get("hook")]


# --------------------------------------------------------------------------- #
# v4: Decade spine — one-time JSON at runs/<run_id>/00_decade_spine.json
# --------------------------------------------------------------------------- #

def _decade_spine_path(run_dir: Path) -> Path:
    return run_dir / "00_decade_spine.json"


def _load_decade_spine(run_dir: Path) -> dict | None:
    path = _decade_spine_path(run_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_decade_spine(run_dir: Path, spine: dict) -> None:
    _write_json(_decade_spine_path(run_dir), spine)


# --------------------------------------------------------------------------- #
# v4: Side-cast register + staging ledger
# --------------------------------------------------------------------------- #
# `side_cast.json` — named side characters from beat sheets, tracked so a
# recurring clerk/neighbour doesn't get reinvented year-over-year. Each
# entry: {id, name, role, first_year, last_year, appearances:[year,...]}.
# Promotion path: if a side character appears in 3+ chapters they become
# eligible for main_cast promotion (the cast_plan prompt may surface them).
#
# `staging_ledger.json` — recurring staging signatures (where + context)
# keyed by year, so the outliner can avoid repeating a character's
# "signature location" scene every year. Stops the "Okafor at the port
# authority desk again" loop.

SIDE_CAST_PROMOTION_THRESHOLD = 3


def _side_cast_path(run_dir: Path) -> Path:
    return run_dir / "side_cast.json"


def _load_side_cast(run_dir: Path) -> dict:
    path = _side_cast_path(run_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"side_characters": []}


def _save_side_cast(run_dir: Path, ledger: dict) -> None:
    _write_json(_side_cast_path(run_dir), ledger)


def _register_side_cast(run_dir: Path, beat_sheet: dict, year: int) -> None:
    """v4: record named side_characters from the beat sheet. Idempotent
    on (id, year)."""
    ledger = _load_side_cast(run_dir)
    entries = ledger.setdefault("side_characters", [])
    by_id = {e["id"]: e for e in entries if e.get("id")}
    for sc in (beat_sheet.get("side_characters") or []):
        sid = sc.get("id") or sc.get("name")
        if not sid:
            continue
        existing = by_id.get(sid)
        if existing:
            apps = existing.setdefault("appearances", [])
            if year not in apps:
                apps.append(year)
            existing["last_year"] = max(existing.get("last_year", year), year)
        else:
            new = {
                "id": sid,
                "name": sc.get("name", ""),
                "role": sc.get("role", ""),
                "first_year": year,
                "last_year": year,
                "appearances": [year],
            }
            entries.append(new)
            by_id[sid] = new
    _save_side_cast(run_dir, ledger)


def _staging_ledger_path(run_dir: Path) -> Path:
    return run_dir / "staging_ledger.json"


def _load_staging_ledger(run_dir: Path) -> dict:
    path = _staging_ledger_path(run_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"entries": []}


def _save_staging_ledger(run_dir: Path, ledger: dict) -> None:
    _write_json(_staging_ledger_path(run_dir), ledger)


STAGING_REPEAT_WINDOW = 2  # v4 plan §5.3: signature staging cooldown


def _staging_signature(scene: dict) -> str:
    """Compact string identifying a scene's signature staging: POV (or
    first who) + where. Used to detect "Okafor at the port authority
    desk" repeats across years."""
    who = scene.get("who") or []
    pov = scene.get("pov_character_id") or (who[0] if who else "")
    where = _normalize_place(scene.get("where", ""))
    return f"{pov}|{where}"


def _register_staging(run_dir: Path, outline: dict, year: int) -> None:
    """Record this chapter's scene stagings so future outlines can avoid
    repetition."""
    ledger = _load_staging_ledger(run_dir)
    entries = ledger.setdefault("entries", [])
    for scene in (outline.get("scene_budget") or []):
        sig = _staging_signature(scene)
        if not sig or sig == "|":
            continue
        entries.append({"year": year, "signature": sig,
                        "scene_id": scene.get("scene_id", "")})
    _save_staging_ledger(run_dir, ledger)


def _recent_stagings(run_dir: Path, *, current_year: int,
                     window: int = STAGING_REPEAT_WINDOW) -> set[str]:
    """Return the set of staging signatures used in the last `window`
    years (not including the current year). The outline prompt will
    be told to avoid these."""
    ledger = _load_staging_ledger(run_dir)
    low = current_year - window
    return {
        e["signature"]
        for e in ledger.get("entries", [])
        if isinstance(e.get("year"), int)
        and low <= e["year"] < current_year
        and e.get("signature")
    }


def _recent_palettes(index: dict, window: int = PALETTE_WINDOW) -> dict[str, set[str]]:
    """Return the set of voice_palette axis values used within the last `window`
    chapters, keyed by axis ('base', 'modulator', 'device'). Used by the
    palette chooser to filter candidates."""
    chapters = sorted(index.get("chapters", []),
                      key=lambda c: c.get("year", 0), reverse=True)[:window]
    recent: dict[str, set[str]] = {"base": set(), "modulator": set(), "device": set()}
    for c in chapters:
        palette = c.get("voice_palette") or {}
        for axis in recent:
            val = palette.get(axis)
            if val:
                recent[axis].add(val)
    return recent


# --------------------------------------------------------------------------- #
# Phase 3: palette chooser (code-side candidate filter; model picks)
#
# Plan §5.2: deterministic filter first, model-tunable second. The outline
# gets a small candidate set per axis; it picks one of each with a 1-
# sentence justification referencing `central_tension`. This makes
# variation a constraint problem rather than a creativity problem.
# --------------------------------------------------------------------------- #

_BASE_MOOD_FIT: dict[str, set[str]] = {
    # -- v3 (kept, but detached-register bases no longer fit every mood) -- #
    "retrospective":   {"drift", "reckoning", "quiet", "turning"},
    "dossier":         {"reckoning", "drift"},
    "reported":        {"acute", "turning", "reckoning"},
    "memoir":          {"quiet", "reckoning", "drift", "turning"},
    # -- v4 embodied/conversational bases --------------------------------- #
    "close-third":     {"acute", "turning", "reckoning", "quiet"},
    "dialogue-scene":  {"acute", "turning", "reckoning", "drift"},
    "letter":          {"quiet", "reckoning", "turning"},
    "long-cam":        {"drift", "reckoning", "acute", "quiet"},
}

_MODULATOR_MOOD_FIT: dict[str, set[str]] = {
    # -- v3 --------------------------------------------------------------- #
    "elegiac":    {"turning", "quiet", "reckoning"},
    "ironic":     {"drift", "reckoning", "acute"},
    "forensic":   {"reckoning", "acute", "turning"},
    "pastoral":   {"quiet", "drift"},
    "polyphonic": {"acute", "turning", "drift"},
    # -- v4 inward / embodied / spoken ------------------------------------ #
    "interior":   {"quiet", "reckoning", "turning", "acute"},
    "domestic":   {"quiet", "drift", "reckoning", "turning"},
    "bodily":     {"acute", "turning", "reckoning"},
    "wry-spoken": {"drift", "reckoning", "acute"},
    "angry":      {"acute", "turning", "reckoning"},
}


def _recent_suppressive_device_count(index: dict, window: int) -> int:
    """v4: how many of the last `window` chapters used a `suppressive`
    device (e.g. no-public-official-dialogue, word-history-forbidden).

    Plan §5.1: suppressive devices are capped at SUPPRESSIVE_DEVICE_CAP per
    SUPPRESSIVE_DEVICE_WINDOW because they bias the register toward
    detachment and are part of what made v3 feel institutional.
    """
    chapters = sorted(index.get("chapters", []),
                      key=lambda c: c.get("year", 0), reverse=True)[:window]
    count = 0
    for c in chapters:
        dev_id = (c.get("voice_palette") or {}).get("device")
        kind = (VOICE_DEVICES.get(dev_id) or {}).get("kind")
        if kind == "suppressive":
            count += 1
    return count


def compute_palette_candidates(
    *, year_mood: str, chapter_index: dict, window: int = PALETTE_WINDOW,
    max_per_axis: int = 5, chapter_mode: str | None = None,
) -> dict[str, list[dict]]:
    """Return candidate bases / modulators / devices for the outliner.

    Filters apply in order:
      1. axis value not used in the last `window` chapters (freshness),
      2. base/modulator fits the year_mood,
      3. fall back to mood-fit only if freshness empties the list,
      4. fall back to the full axis if mood-fit also empties it.

    v4 additions:
      - If the last SUPPRESSIVE_DEVICE_WINDOW chapters already include
        SUPPRESSIVE_DEVICE_CAP suppressive devices, suppressive devices
        are removed from the candidate set entirely.
      - If `chapter_mode` is provided, devices incompatible with it are
        removed. `overheard` cannot take `no-public-official-dialogue`;
        `monoscene` cannot take devices that fragment the chapter.

    Candidates are returned with their exemplars so the prompt can show
    target texture to the outline (and, via the outline, the narrator).
    """
    recent = _recent_palettes(chapter_index, window=window)

    def _pick(registry: dict[str, dict[str, str]], recent_used: set[str],
              fit: set[str] | None,
              hard_exclude: set[str] | None = None) -> list[str]:
        exclude = hard_exclude or set()
        fresh = [k for k in registry
                 if k not in recent_used and k not in exclude
                 and (fit is None or k in fit)]
        if fresh:
            return fresh
        mood_ok = [k for k in registry
                   if k not in exclude and (fit is None or k in fit)]
        if mood_ok:
            return mood_ok
        remaining = [k for k in registry if k not in exclude]
        return remaining or list(registry.keys())

    base_fit = set()
    for k, moods in _BASE_MOOD_FIT.items():
        if year_mood in moods:
            base_fit.add(k)
    mod_fit = set()
    for k, moods in _MODULATOR_MOOD_FIT.items():
        if year_mood in moods:
            mod_fit.add(k)

    # v4: suppressive-device cap. If the recent window is saturated with
    # suppressive devices, exclude them outright.
    dev_exclude: set[str] = set()
    supp_count = _recent_suppressive_device_count(
        chapter_index, SUPPRESSIVE_DEVICE_WINDOW)
    if supp_count >= SUPPRESSIVE_DEVICE_CAP:
        for k, meta in VOICE_DEVICES.items():
            if meta.get("kind") == "suppressive":
                dev_exclude.add(k)

    # v4: mode-incompatible devices.
    if chapter_mode == "overheard":
        # Overheard is dialogue-forward; banning official dialogue fights it.
        dev_exclude.add("no-public-official-dialogue")
    if chapter_mode == "monoscene" or chapter_mode == "long-march":
        # These modes demand a single continuous scene; devices that
        # demand multi-scene segmentation don't fit. (None currently
        # incompatible; kept as a hook for future devices.)
        pass

    bases = _pick(VOICE_BASES, recent["base"], base_fit or None)[:max_per_axis]
    modulators = _pick(VOICE_MODULATORS, recent["modulator"], mod_fit or None)[:max_per_axis]
    devices = _pick(VOICE_DEVICES, recent["device"], None,
                    hard_exclude=dev_exclude)[:max_per_axis]

    def _hydrate(keys: list[str], registry: dict[str, dict[str, str]]) -> list[dict]:
        out: list[dict] = []
        for k in keys:
            meta = dict(registry[k])
            out.append({"id": k, **meta})
        return out

    return {
        "bases": _hydrate(bases, VOICE_BASES),
        "modulators": _hydrate(modulators, VOICE_MODULATORS),
        "devices": _hydrate(devices, VOICE_DEVICES),
    }


# --------------------------------------------------------------------------- #
# Phase 3: slop ledger (dynamic, seeded from known tics)
#
# Plan §5.4. The ledger stores { phrase, source, added_year, last_seen_year,
# cooldown_until_year, note }. `active` phrases are those whose cooldown is
# still in effect relative to the current year; outline, narrator, and
# editor are told to avoid them. After the editor runs we scan the final
# prose; any seeded phrase that slipped through has its cooldown re-armed.
# --------------------------------------------------------------------------- #

def _slop_ledger_path(run_dir: Path) -> Path:
    return run_dir / "slop_ledger.json"


def _load_slop_ledger(run_dir: Path) -> dict:
    path = _slop_ledger_path(run_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"entries": []}


def _save_slop_ledger(run_dir: Path, ledger: dict) -> None:
    _write_json(_slop_ledger_path(run_dir), ledger)


def _seed_slop_ledger(run_dir: Path, seed_year: int) -> dict:
    """Seed the ledger at startup if empty. Idempotent."""
    ledger = _load_slop_ledger(run_dir)
    if ledger.get("entries"):
        return ledger
    for s in SEEDED_SLOP_PHRASES:
        ledger["entries"].append({
            "phrase": s["phrase"],
            "note": s.get("note", ""),
            "source": "seed",
            "added_year": seed_year,
            "last_seen_year": None,
            "cooldown_until_year": seed_year + SLOP_WINDOW,
        })
    _save_slop_ledger(run_dir, ledger)
    return ledger


def _active_slop_phrases(ledger: dict, current_year: int) -> list[dict]:
    """Return entries whose cooldown is still active at `current_year`.
    Each entry is returned in its full ledger shape so the prompt can
    surface the `note` alongside the phrase."""
    active = []
    for e in ledger.get("entries", []):
        cooldown = e.get("cooldown_until_year", 0) or 0
        added = e.get("added_year", 0) or 0
        if added <= current_year and cooldown > current_year:
            active.append(e)
    return active


def _slop_phrase_matches(phrase: str, prose_lower: str) -> bool:
    """Case-insensitive match of a seeded slop phrase against prose.

    If the phrase contains the literal 'YYYY' placeholder, treat it as
    'any 4-digit year' (regex \\d{4}). Otherwise do a plain substring
    match. The naive .replace('yyyy','') approach is WRONG — it turns
    'In YYYY,' into 'in ,' which never matches 'in 2028,' in real prose
    (and can false-positive on unrelated comma-adjacent text).
    """
    phrase_low = (phrase or "").lower()
    if not phrase_low.strip():
        return False
    if "yyyy" in phrase_low:
        # Escape everything literal, then substitute the escaped placeholder
        # for a 4-digit-year class. re.escape may emit 'yyyy' unchanged or as
        # 'y\\y\\y\\y' depending on version; handle both defensively.
        pattern = re.escape(phrase_low)
        pattern = pattern.replace("yyyy", r"\d{4}")
        pattern = pattern.replace(r"y\y\y\y", r"\d{4}")
        return re.search(pattern, prose_lower) is not None
    return phrase_low in prose_lower


def _scan_and_refresh_slop(ledger: dict, final_prose: str, current_year: int) -> list[str]:
    """Case-insensitive scan of the editor's final prose against every
    ledger entry. Any phrase that slipped through has its cooldown
    re-armed to current_year + SLOP_WINDOW and last_seen_year updated.
    Returns the list of phrases that were caught (for logging).

    YYYY-containing seeds are matched via a \\d{4} regex (see
    _slop_phrase_matches) so the rule 'In YYYY,' actually catches
    'In 2028,' style openers in the body.
    """
    found: list[str] = []
    low = final_prose.lower()
    for entry in ledger.get("entries", []):
        phrase = entry.get("phrase") or ""
        if _slop_phrase_matches(phrase, low):
            entry["cooldown_until_year"] = current_year + SLOP_WINDOW
            entry["last_seen_year"] = current_year
            found.append(phrase)
    return found


# --------------------------------------------------------------------------- #
# Cast / character ledger helpers (v3 Phase 1)
# --------------------------------------------------------------------------- #

def _cast_path(run_dir: Path) -> Path:
    return run_dir / "cast.json"


def _char_arc_path(run_dir: Path, char_id: str) -> Path:
    return run_dir / CHARACTERS_SUBDIR / f"char_{char_id}_arc.md"


def _load_cast(run_dir: Path) -> dict:
    path = _cast_path(run_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"characters": [], "last_updated_year": None}


def _save_cast(run_dir: Path, cast: dict) -> None:
    _write_json(_cast_path(run_dir), cast)


def _get_character(cast: dict, char_id: str) -> dict | None:
    for ch in cast["characters"]:
        if ch["id"] == char_id:
            return ch
    return None


def _active_cast(cast: dict) -> list[dict]:
    return [c for c in cast["characters"] if c.get("status") == "active"]


def _recent_introductions(cast: dict, current_year: int, window: int = FRESHNESS_WINDOW) -> list[str]:
    return [
        c["id"] for c in cast["characters"]
        if c.get("introduced_year") is not None
        and current_year - c["introduced_year"] <= window
    ]


def _append_char_arc(run_dir: Path, char_id: str, year: int, body: str, *,
                     header: str | None = None) -> None:
    """Append a dated entry to a character's arc file. Creates the file on
    first write, using `header` as the bio block at the top."""
    path = _char_arc_path(run_dir, char_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(header or f"# {char_id}\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {year}\n\n{body.strip()}\n")


def _read_char_arc(run_dir: Path, char_id: str) -> str:
    path = _char_arc_path(run_dir, char_id)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _character_to_cast_entry(c: dict, year: int) -> dict:
    """Convert a bootstrap/introduced character record into a cast.json entry."""
    return {
        "id": c["id"],
        "name": c["name"],
        "role": c["role"],
        "voice_tag": c.get("voice_tag", ""),
        "home": c.get("home", ""),
        "bio": c.get("bio", ""),
        "signature_tic": c.get("signature_tic", ""),
        "signature_object_or_place": c.get("signature_object_or_place", ""),
        "introduced_year": year,
        "last_seen_year": year,
        "status": "active",
        "relationships": [],
        "per_year_notes": {},
        "initial_want": c.get("initial_want", ""),
        "initial_obstacle": c.get("initial_obstacle", ""),
        "positioned_at": c.get("positioned_at", ""),
    }


def _char_header(c: dict) -> str:
    """Markdown header block placed at the top of a character's arc file."""
    parts = [f"# {c['name']}", "", c.get("role", "")]
    if c.get("home"):
        parts.append(f"**Home:** {c['home']}")
    if c.get("voice_tag"):
        parts.append(f"**Voice:** {c['voice_tag']}")
    if c.get("bio"):
        parts.append("")
        parts.append(c["bio"])
    extras = []
    if c.get("signature_tic"):
        extras.append(f"- Tic: {c['signature_tic']}")
    if c.get("signature_object_or_place"):
        extras.append(f"- Signature: {c['signature_object_or_place']}")
    if c.get("initial_want"):
        extras.append(f"- Initial want: {c['initial_want']}")
    if c.get("initial_obstacle"):
        extras.append(f"- Initial obstacle: {c['initial_obstacle']}")
    if extras:
        parts.append("")
        parts.extend(extras)
    return "\n".join(parts) + "\n"


def _update_cast_after_epoch(cast: dict, cast_plan: dict, dossiers: dict[str, dict],
                              year: int) -> None:
    """Reconcile cast.json with this epoch's cast_plan and dossiers.

    - Mark introduced characters as active with introduced_year = year.
    - Bump last_seen_year for returning characters.
    - Mark retiring/deceased characters accordingly.
    - Auto-mark long-unseen characters as dormant.
    - Stash a 1-line per_year_note from the dossier's memorable_image.
    """
    for entry in cast_plan.get("main_cast", []):
        cid = entry["id"]
        status = entry.get("status", "returning")
        existing = _get_character(cast, cid)
        if status == "introduced":
            if existing is None:
                cast["characters"].append(_character_to_cast_entry(entry, year))
            else:
                # Existing id marked "introduced" — treat as a revival of a
                # dormant/retired character. Keep the original bio, reactivate.
                existing["status"] = "active"
                existing["last_seen_year"] = year
        elif status in ("retiring", "deceased"):
            if existing:
                existing["status"] = "retired" if status == "retiring" else "deceased"
                existing["last_seen_year"] = year
                existing["final_beat"] = entry.get("final_beat", "")
        else:  # returning
            if existing:
                existing["last_seen_year"] = year
                if existing.get("status") != "active":
                    existing["status"] = "active"
        dossier = dossiers.get(cid)
        if dossier and existing is not None:
            note = dossier.get("memorable_image") or dossier.get("unresolved_at_year_end") or ""
            if note:
                existing.setdefault("per_year_notes", {})[str(year)] = note

    # Refresh dormancy for everyone who wasn't in this epoch's cast.
    active_ids = {e["id"] for e in cast_plan.get("main_cast", [])}
    for c in cast["characters"]:
        if c["id"] in active_ids:
            continue
        if c.get("status") not in ("active",):
            continue
        last = c.get("last_seen_year") or c.get("introduced_year") or year
        if year - last >= DORMANT_AFTER:
            c["status"] = "dormant"

    cast["last_updated_year"] = year


# --------------------------------------------------------------------------- #
# OpenAI calls with model-fallback
# --------------------------------------------------------------------------- #

async def _chat(
    client: AsyncOpenAI,
    tier: str,
    messages: list[dict],
    *,
    json_mode: bool = False,
    stream: bool = False,
) -> str:
    """Call chat.completions, trying each model in MODELS[tier] in order.

    Streaming prints chunks to stdout as they arrive. JSON mode forces a
    JSON object response and disables streaming (JSON streams are not useful
    for parsing here).
    """
    kwargs: dict[str, Any] = {"messages": messages}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
        stream = False

    last_err: Exception | None = None
    for model in MODELS[tier]:
        try:
            if stream:
                full: list[str] = []
                resp = await client.chat.completions.create(
                    model=model, stream=True, **kwargs
                )
                async for chunk in resp:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        full.append(delta)
                        sys.stdout.write(delta)
                        sys.stdout.flush()
                sys.stdout.write("\n")
                return "".join(full)
            resp = await client.chat.completions.create(model=model, **kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            last_err = e
            print(f"  [tier={tier} model='{model}' failed: {type(e).__name__}: {e}]")
            continue
    raise RuntimeError(f"All models failed for tier '{tier}'. Last error: {last_err}")


def _parse_json(raw: str, *, where: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{where} returned invalid JSON: {e}\n--- raw output ---\n{raw}\n---"
        ) from e


# --------------------------------------------------------------------------- #
# Stage 1: Specialists
# --------------------------------------------------------------------------- #

async def run_specialist(
    client: AsyncOpenAI,
    facet_name: str,
    spec: dict,
    *,
    year: int,
    fork: dict,
    parent_state: dict,
    previous_summary: dict | None,
) -> dict:
    system = prompts.SPECIALIST_SYSTEM_TEMPLATE.format(
        brief=spec["brief"],
        facet_name=facet_name,
        owned_facets=", ".join(spec["facets"]),
        year=year,
    )
    user = prompts.SPECIALIST_USER_TEMPLATE.format(
        year=year,
        fork_title=fork.get("title", ""),
        fork_domain=fork.get("domain", "unspecified"),
        fork_flavor=fork.get("flavor", ""),
        parent_state_json=_pretty_json(parent_state),
        previous_summary_json=_pretty_json(previous_summary) if previous_summary else "null",
        facet_name=facet_name,
    )
    raw = await _chat(
        client, "specialist",
        [{"role": "system", "content": system},
         {"role": "user",   "content": user}],
        json_mode=True,
    )
    data = _parse_json(raw, where=f"specialist[{facet_name}]")
    required = ("facet", "headline_developments", "notes_for_storyteller", "state_updates")
    missing = [k for k in required if k not in data]
    if missing:
        raise RuntimeError(f"specialist[{facet_name}] missing keys {missing}: {data}")
    return data


# --------------------------------------------------------------------------- #
# Stage 3: Summarizer (balanced)
# --------------------------------------------------------------------------- #

async def run_summarizer(
    client: AsyncOpenAI,
    *,
    year: int,
    specialist_docs: dict[str, dict],
    state: dict,
    decade_spine: dict | None = None,
    recent_tensions: list[str] | None = None,
    retries: int = 2,
) -> dict:
    spine_json = _pretty_json(decade_spine) if decade_spine else (
        "(no decade_spine available — baseline run, infer from state)"
    )
    user = prompts.SUMMARIZER_USER_TEMPLATE.format(
        year=year,
        decade_spine_json=spine_json,
        ecology_doc=_pretty_json(specialist_docs["ecology"]),
        economy_doc=_pretty_json(specialist_docs["economy"]),
        geopolitics_doc=_pretty_json(specialist_docs["geopolitics"]),
        society_doc=_pretty_json(specialist_docs["society"]),
        culture_doc=_pretty_json(specialist_docs["culture"]),
        state_json=_pretty_json(state),
        valid_moods=", ".join(VALID_MOODS),
        recent_tensions=(
            "\n".join(f"- {t}" for t in (recent_tensions or []))
            if recent_tensions else "(none yet)"
        ),
    )

    last_err: str | None = None
    for attempt in range(retries + 1):
        raw = await _chat(
            client, "orchestrator",
            [{"role": "system", "content": prompts.SUMMARIZER_SYSTEM},
             {"role": "user",   "content": user}],
            json_mode=True,
        )
        data = _parse_json(raw, where="summarizer")
        try:
            _validate_summary_mood(data, where="summarizer",
                                   require_dilemma=True)
            return data
        except RuntimeError as e:
            last_err = str(e)
            print(f"  [summarizer attempt {attempt + 1}: {last_err}; retrying]")
            user += (
                f"\n\nPREVIOUS ATTEMPT REJECTED BECAUSE: {last_err}\n"
                f"Fix the offending field. year_dilemma must have all of "
                f"{list(YEAR_DILEMMA_REQUIRED_FIELDS)} populated with real "
                f"strings; choice_a and choice_b must be genuinely "
                f"different actions; stakes on BOTH must cost something."
            )
    raise RuntimeError(
        f"summarizer failed after {retries + 1} attempts: {last_err}"
    )


# --------------------------------------------------------------------------- #
# v4 Stage 0: Decade Spine (one-time, after cast bootstrap)
# --------------------------------------------------------------------------- #

async def run_decade_spine(
    client: AsyncOpenAI,
    *,
    seed_state: dict,
    baseline_summary: dict,
    bootstrap: dict,
    run_span_years: int = 10,
    retries: int = 2,
) -> dict:
    """v4 plan §3.1. Commit the decade to a dramatic question + wager +
    3-act structure. One-time; result injected into per-year stages.

    `run_span_years` is the nominal decade the spine covers; acts are
    distributed across this span (approx 3 / 4 / 3 years).
    """
    seed_year = seed_state["year"]
    first_year = seed_year + 1
    last_year = seed_year + run_span_years

    user = prompts.DECADE_SPINE_USER_TEMPLATE.format(
        seed_year=seed_year,
        first_year=first_year,
        last_year=last_year,
        seed_json=_pretty_json(seed_state),
        baseline_summary_json=_pretty_json(baseline_summary),
        bootstrap_json=_pretty_json(bootstrap),
    )
    last_err: str | None = None
    for attempt in range(retries + 1):
        raw = await _chat(
            client, "orchestrator",
            [{"role": "system", "content": prompts.DECADE_SPINE_SYSTEM},
             {"role": "user",   "content": user}],
            json_mode=True,
        )
        data = _parse_json(raw, where="decade_spine")
        problem = _validate_decade_spine(data)
        if not problem:
            return data
        last_err = problem
        print(f"  [decade_spine attempt {attempt + 1}: {problem}; retrying]")
        user += (
            f"\n\nPREVIOUS ATTEMPT REJECTED BECAUSE: {problem}\n"
            f"Fix it. Required fields: {list(DECADE_SPINE_REQUIRED_FIELDS)}. "
            f"`acts` must be a list of 3 entries, each carrying "
            f"{list(DECADE_SPINE_ACT_FIELDS)} plus 3..6 `promise_lines`. "
            f"`stakes_for_cast` needs at "
            f"least 2 of the 3 bootstrap character ids."
        )
    raise RuntimeError(
        f"decade_spine failed after {retries + 1} attempts: {last_err}"
    )


def _validate_decade_spine(data: dict) -> str | None:
    for k in DECADE_SPINE_REQUIRED_FIELDS:
        v = data.get(k)
        if k == "acts":
            continue
        if not isinstance(v, str) or not v.strip():
            return f"missing or empty field '{k}'"
    acts = data.get("acts")
    if not isinstance(acts, list) or len(acts) != 3:
        return f"acts must be a list of 3 entries, got {acts!r}"
    for i, a in enumerate(acts):
        if not isinstance(a, dict):
            return f"acts[{i}] must be an object"
        for k in DECADE_SPINE_ACT_FIELDS:
            v = a.get(k)
            if k == "act":
                if v != i + 1:
                    return f"acts[{i}].act must be {i + 1}, got {v!r}"
                continue
            if not isinstance(v, str) or not v.strip():
                return f"acts[{i}].{k} must be a non-empty string"
        promise_lines = a.get("promise_lines")
        if not isinstance(promise_lines, list) or not (3 <= len(promise_lines) <= 6):
            return f"acts[{i}].promise_lines must be a list of 3..6 stageable obligations"
        seen_ids: set[str] = set()
        for j, p in enumerate(promise_lines):
            if not isinstance(p, dict):
                return f"acts[{i}].promise_lines[{j}] must be an object"
            for pk in ("id", "obligation"):
                pv = p.get(pk)
                if not isinstance(pv, str) or not pv.strip():
                    return f"acts[{i}].promise_lines[{j}].{pk} must be a non-empty string"
            if p["id"] in seen_ids:
                return f"acts[{i}].promise_lines duplicate id '{p['id']}'"
            seen_ids.add(p["id"])
    stakes = data.get("stakes_for_cast")
    if not isinstance(stakes, list) or len(stakes) < 2:
        return "stakes_for_cast must list at least 2 of the founding cast"
    for i, s in enumerate(stakes):
        if not isinstance(s, dict):
            return f"stakes_for_cast[{i}] must be an object"
        for k in ("character_id", "what_they_stand_to_lose"):
            v = s.get(k)
            if not isinstance(v, str) or not v.strip():
                return f"stakes_for_cast[{i}].{k} must be a non-empty string"
    prohibited = data.get("decade_prohibited")
    if not isinstance(prohibited, list) or len(prohibited) < 2:
        return ("decade_prohibited must be a list of at least 2 guardrail "
                "phrases naming endings this run must not reach")
    return None


async def run_baseline_summarizer(
    client: AsyncOpenAI, *, seed_state: dict
) -> dict:
    user = prompts.BASELINE_SUMMARIZER_USER_TEMPLATE.format(
        seed_json=_pretty_json(seed_state),
        year=seed_state["year"],
        valid_moods=", ".join(VALID_MOODS),
    )
    raw = await _chat(
        client, "orchestrator",
        [{"role": "system", "content": prompts.BASELINE_SUMMARIZER_SYSTEM},
         {"role": "user",   "content": user}],
        json_mode=True,
    )
    data = _parse_json(raw, where="baseline_summarizer")
    _validate_summary_mood(data, where="baseline_summarizer")
    return data


def _validate_summary_mood(data: dict, *, where: str,
                           require_dilemma: bool = False) -> None:
    """Phase 3 wiring: every summary carries `year_mood` + `central_tension`
    downstream. v4 adds `year_dilemma` (required for non-baseline summaries;
    the baseline predates the decade_spine and may omit it)."""
    mood = data.get("year_mood")
    if mood not in VALID_MOODS:
        raise RuntimeError(
            f"{where}: year_mood must be one of {VALID_MOODS}, got {mood!r}"
        )
    ct = data.get("central_tension")
    if not isinstance(ct, str) or not ct.strip():
        raise RuntimeError(
            f"{where}: central_tension must be a non-empty string, got {ct!r}"
        )
    if not require_dilemma:
        return
    dil = data.get("year_dilemma")
    if not isinstance(dil, dict):
        raise RuntimeError(
            f"{where}: year_dilemma must be an object, got "
            f"{type(dil).__name__}"
        )
    for k in YEAR_DILEMMA_REQUIRED_FIELDS:
        v = dil.get(k)
        if not isinstance(v, str) or not v.strip():
            raise RuntimeError(
                f"{where}: year_dilemma.{k} must be a non-empty string, "
                f"got {v!r}"
            )
    # A dilemma where the two options differ only by negation is a thesis,
    # not a dilemma. Catch the most obvious failure mode without being
    # aggressive — the prompt already teaches this in detail.
    a = dil["choice_a"].strip().lower()
    b = dil["choice_b"].strip().lower()
    if a == b:
        raise RuntimeError(
            f"{where}: year_dilemma.choice_a and choice_b are identical; "
            f"options must be genuinely different actions"
        )


# --------------------------------------------------------------------------- #
# Stage 4: Cross-Interference
# --------------------------------------------------------------------------- #

async def run_cross_interference(
    client: AsyncOpenAI,
    *,
    year: int,
    summary: dict,
    specialist_docs: dict[str, dict],
    fork_domain: str | None = None,
    retries: int = 2,
) -> dict:
    """Cross-interference analyst with Phase-4 rotation retry.

    If more than `CROSS_INTERFERENCE_FORK_DOMAIN_LIMIT` (60%) of the
    interactions touch `fork_domain`, re-prompt for ≥2 interactions
    that do NOT involve it. Otherwise the analyst over-indexes on the
    fork's domain and the world shrinks around it (plan §2 step 4).
    """
    user = prompts.CROSS_INTERFERENCE_USER_TEMPLATE.format(
        year=year,
        summary_json=_pretty_json(summary),
        ecology_doc=_pretty_json(specialist_docs["ecology"]),
        economy_doc=_pretty_json(specialist_docs["economy"]),
        geopolitics_doc=_pretty_json(specialist_docs["geopolitics"]),
        society_doc=_pretty_json(specialist_docs["society"]),
        culture_doc=_pretty_json(specialist_docs["culture"]),
    )

    data: dict | None = None
    for attempt in range(retries + 1):
        raw = await _chat(
            client, "orchestrator",
            [{"role": "system", "content": prompts.CROSS_INTERFERENCE_SYSTEM},
             {"role": "user",   "content": user}],
            json_mode=True,
        )
        data = _parse_json(raw, where="cross_interference")
        interactions = data.get("cross_domain_interactions", [])
        if len(interactions) < 3:
            raise RuntimeError(
                f"cross_interference produced only {len(interactions)} "
                f"interactions (need >=3): {data}"
            )
        problem = _validate_cross_interference_rotation(interactions, fork_domain)
        if not problem:
            return data
        print(f"  [cross_interference attempt {attempt + 1}: {problem}; retrying]")
        user += (
            f"\n\nPREVIOUS ATTEMPT REJECTED BECAUSE: {problem}\n"
            f"The chosen fork's domain for this year is '{fork_domain}'. "
            f"Too many of your interactions revolved around it. Keep the "
            f"strongest fork-domain interactions, but REPLACE the weakest "
            f"ones so that AT LEAST 2 of the interactions do NOT include "
            f"'{fork_domain}' in `domains_involved`. Those non-fork "
            f"interactions must still be grounded in the specialist docs "
            f"(pick real headline_developments / actors from the other "
            f"four facets). This keeps the world from shrinking around "
            f"the fork."
        )

    # Exhausted retries — ship what we have but warn.
    print(f"  [cross_interference: rotation rule still violated after "
          f"{retries + 1} attempts; shipping anyway]")
    return data  # type: ignore[return-value]


def _validate_cross_interference_rotation(
    interactions: list[dict], fork_domain: str | None,
) -> str | None:
    """Return a problem string if >60% of interactions touch fork_domain,
    else None. Also requires ≥2 interactions that don't touch it so the
    rule is substantive (one token non-fork interaction doesn't pass)."""
    if not fork_domain or fork_domain not in VALID_DOMAINS:
        return None
    if not interactions:
        return None
    touching = sum(
        1 for i in interactions
        if fork_domain in (i.get("domains_involved") or [])
    )
    frac = touching / len(interactions)
    non_fork = len(interactions) - touching
    if frac > CROSS_INTERFERENCE_FORK_DOMAIN_LIMIT or non_fork < 2:
        return (
            f"{touching}/{len(interactions)} interactions "
            f"({frac:.0%}) touch the fork's domain '{fork_domain}' "
            f"(limit {CROSS_INTERFERENCE_FORK_DOMAIN_LIMIT:.0%}); need "
            f"≥2 that do NOT include '{fork_domain}'"
        )
    return None


# --------------------------------------------------------------------------- #
# Stage 5a-bis: Cast Bootstrap (one-time, runs after the baseline summary)
# --------------------------------------------------------------------------- #

async def run_cast_bootstrap(
    client: AsyncOpenAI, *, seed_state: dict, baseline_summary: dict,
) -> dict:
    user = prompts.CAST_BOOTSTRAP_USER_TEMPLATE.format(
        seed_json=_pretty_json(seed_state),
        baseline_summary_json=_pretty_json(baseline_summary),
    )
    raw = await _chat(
        client, "orchestrator",
        [{"role": "system", "content": prompts.CAST_BOOTSTRAP_SYSTEM},
         {"role": "user",   "content": user}],
        json_mode=True,
    )
    data = _parse_json(raw, where="cast_bootstrap")
    chars = data.get("characters", [])
    if len(chars) != 3:
        raise RuntimeError(
            f"cast_bootstrap expected exactly 3 characters, got {len(chars)}: {data}"
        )
    for i, c in enumerate(chars):
        for key in ("id", "name", "role", "bio"):
            if key not in c:
                raise RuntimeError(f"cast_bootstrap character[{i}] missing '{key}': {c}")
    return data


# --------------------------------------------------------------------------- #
# Stage 5a: Cast Plan (per epoch) — who appears, 3-6 main cast
# --------------------------------------------------------------------------- #

async def run_cast_plan(
    client: AsyncOpenAI,
    *,
    year: int,
    cast: dict,
    summary: dict,
    crossinterference: dict,
    prev_chapter_text: str,
    prev_year: int | None,
    decade_spine: dict | None = None,
    unchanged_streaks: list[str] | None = None,
    retries: int = 2,
) -> dict:
    active = _active_cast(cast)
    recent = _recent_introductions(cast, year)
    valid_interaction_ids = [
        i["id"] for i in crossinterference.get("cross_domain_interactions", [])
    ]
    if not valid_interaction_ids:
        raise RuntimeError("cast_plan: cross-interference has no interactions to position at")

    streaks = list(unchanged_streaks or [])
    streaks_block = (
        ", ".join(streaks) if streaks
        else "(none — no character is at the 3-year unchanged threshold)"
    )
    user = prompts.CAST_PLAN_USER_TEMPLATE.format(
        year=year,
        decade_spine_json=_pretty_json(decade_spine) if decade_spine
        else "(no decade_spine available)",
        year_dilemma_json=_pretty_json(summary.get("year_dilemma") or {}),
        unchanged_streaks=streaks_block,
        active_cast_json=_pretty_json(active),
        recent_introductions=", ".join(recent) if recent else "(none)",
        summary_json=_pretty_json(summary),
        crossinterference_json=_pretty_json(crossinterference),
        prev_chapter_text=prev_chapter_text or "(no previous chapter yet)",
        prev_year=prev_year if prev_year is not None else "n/a",
    )

    data: dict | None = None
    problem: str | None = None
    for attempt in range(retries + 1):
        raw = await _chat(
            client, "orchestrator",
            [{"role": "system", "content": prompts.CAST_PLAN_SYSTEM},
             {"role": "user",   "content": user}],
            json_mode=True,
        )
        data = _parse_json(raw, where="cast_plan")
        main_cast = data.get("main_cast", [])
        problem = _validate_cast_plan(
            main_cast, active, valid_interaction_ids,
            unchanged_streaks=streaks,
        )
        if not problem:
            return data
        print(f"  [cast_plan attempt {attempt + 1}: {problem}; retrying]")
        user += (
            f"\n\nPREVIOUS ATTEMPT REJECTED BECAUSE: {problem}\n"
            "Fix it. Every position_interaction_id MUST be one of these "
            f"exact ids from the cross-interference JSON above — copy-paste "
            f"verbatim: {valid_interaction_ids}. Every entry MUST have a "
            f"non-empty `spine_stake`. Every id in UNCHANGED_STREAKS "
            f"({streaks or 'none'}) MUST appear either as retiring/"
            f"deceased OR as returning with a non-empty `forced_change_note`."
        )

    raise RuntimeError(
        f"cast_plan failed after {retries + 1} attempts: {problem}\n{_pretty_json(data)}"
    )


def _validate_cast_plan(main_cast: list[dict], active: list[dict],
                         valid_interaction_ids: list[str],
                         *, unchanged_streaks: list[str] | None = None
                         ) -> str | None:
    if not isinstance(main_cast, list) or not (3 <= len(main_cast) <= CAST_MAX):
        return f"main_cast must have 3..{CAST_MAX} entries, got {len(main_cast) if isinstance(main_cast, list) else type(main_cast).__name__}"
    active_ids = {c["id"] for c in active}
    seen_ids: set[str] = set()
    has_returning = False
    streaks = set(unchanged_streaks or [])
    for i, entry in enumerate(main_cast):
        for k in ("id", "status", "position_interaction_id", "brief"):
            if k not in entry:
                return f"main_cast[{i}] missing '{k}'"
        status = entry["status"]
        if status not in ("returning", "introduced", "retiring", "deceased"):
            return f"main_cast[{i}] invalid status '{status}'"
        if entry["id"] in seen_ids:
            return f"main_cast[{i}] duplicate id '{entry['id']}'"
        seen_ids.add(entry["id"])
        if entry["position_interaction_id"] not in valid_interaction_ids:
            return (f"main_cast[{i}] position_interaction_id '{entry['position_interaction_id']}' "
                    f"not in cross-interference ids {valid_interaction_ids}")
        # v4: spine_stake required on every entry.
        spine_stake = entry.get("spine_stake")
        if not isinstance(spine_stake, str) or not spine_stake.strip():
            return (f"main_cast[{i}] missing 'spine_stake' — every cast "
                    f"member must have skin in the decade's dramatic "
                    f"question")
        if status == "introduced":
            for k in ("name", "role", "voice_tag", "home", "bio"):
                if not entry.get(k):
                    return f"main_cast[{i}] introduced but missing '{k}'"
            if entry["id"] in active_ids:
                return f"main_cast[{i}] marked introduced but id '{entry['id']}' already active"
        elif status in ("retiring", "deceased"):
            if entry["id"] not in active_ids:
                return f"main_cast[{i}] marked {status} but id '{entry['id']}' not in active cast"
            if not entry.get("final_beat"):
                return f"main_cast[{i}] marked {status} but missing 'final_beat'"
            has_returning = True
        else:  # returning
            if entry["id"] not in active_ids:
                return f"main_cast[{i}] returning but id '{entry['id']}' not in active cast"
            has_returning = True
    if active and not has_returning:
        return "active cast exists but no returning/retiring character in plan"
    # v4: unchanged-streak ids must be resolved.
    if streaks:
        cast_by_id = {e["id"]: e for e in main_cast}
        for sid in streaks:
            entry = cast_by_id.get(sid)
            if entry is None:
                # Omitted entirely: acceptable (the character is absent
                # from this year's cast, which breaks the streak naturally).
                continue
            status = entry.get("status")
            if status in ("retiring", "deceased"):
                continue
            fc = entry.get("forced_change_note")
            if not isinstance(fc, str) or not fc.strip():
                return (
                    f"main_cast member '{sid}' has been unchanged for "
                    f"{CHANGE_AUDIT_UNCHANGED_STREAK_LIMIT} consecutive "
                    f"years; either retire/decease them OR keep them as "
                    f"returning with a non-empty `forced_change_note` "
                    f"naming what changes for them this year"
                )
    return None


# --------------------------------------------------------------------------- #
# Stage 5b: Character Dossiers (one per cast member, parallel, cheap tier)
# --------------------------------------------------------------------------- #

async def run_character_dossier(
    client: AsyncOpenAI,
    *,
    year: int,
    character: dict,
    plan_entry: dict,
    arc_history: str,
    summary: dict,
    crossinterference: dict,
) -> dict:
    user = prompts.DOSSIER_USER_TEMPLATE.format(
        char_id=character["id"],
        name=character.get("name", ""),
        role=character.get("role", ""),
        voice_tag=character.get("voice_tag", ""),
        home=character.get("home", ""),
        bio=character.get("bio", ""),
        signature_tic=character.get("signature_tic", ""),
        signature_object=character.get("signature_object_or_place", ""),
        position_interaction_id=plan_entry["position_interaction_id"],
        brief=plan_entry.get("brief", ""),
        arc_history=arc_history or "(no prior arc; this is the character's first year)",
        year=year,
        summary_json=_pretty_json(summary),
        crossinterference_json=_pretty_json(crossinterference),
    )
    raw = await _chat(
        client, "specialist",
        [{"role": "system", "content": prompts.DOSSIER_SYSTEM},
         {"role": "user",   "content": user}],
        json_mode=True,
    )
    data = _parse_json(raw, where=f"dossier[{character['id']}]")
    required = ("id", "want", "obstacle", "this_year_beats",
                "memorable_image", "unresolved_at_year_end")
    missing = [k for k in required if k not in data]
    if missing:
        raise RuntimeError(f"dossier[{character['id']}] missing keys {missing}: {data}")
    data["id"] = character["id"]  # enforce consistent id
    data["year"] = year
    return data


async def run_character_dossiers(
    client: AsyncOpenAI,
    *,
    year: int,
    run_dir: Path,
    cast_plan: dict,
    cast: dict,
    summary: dict,
    crossinterference: dict,
) -> dict[str, dict]:
    """Fire all dossier calls in parallel. Returns {char_id: dossier_dict}."""
    tasks: dict[str, Any] = {}
    for entry in cast_plan["main_cast"]:
        cid = entry["id"]
        if entry["status"] == "introduced":
            character = entry  # contains name/role/bio/etc. inline
            arc_history = ""   # first year, no arc
        else:
            character = _get_character(cast, cid)
            if character is None:
                raise RuntimeError(
                    f"cast_plan references id '{cid}' not in cast.json; "
                    f"pipeline state is inconsistent"
                )
            arc_history = _read_char_arc(run_dir, cid)
        tasks[cid] = run_character_dossier(
            client,
            year=year,
            character=character,
            plan_entry=entry,
            arc_history=arc_history,
            summary=summary,
            crossinterference=crossinterference,
        )
    results = await asyncio.gather(*tasks.values())
    return dict(zip(tasks.keys(), results))


# --------------------------------------------------------------------------- #
# Stage 5c: Beat Sheet (mastermind structured scaffolding, not prose)
# --------------------------------------------------------------------------- #

async def run_beat_sheet(
    client: AsyncOpenAI,
    *,
    year: int,
    dossiers: dict[str, dict],
    summary: dict,
    crossinterference: dict,
    prev_chapter_text: str,
    prev_year: int | None,
    previous_hooks_typed: list[dict] | None = None,
    recent_off_page_years: list[int] | None = None,
    decade_spine: dict | None = None,
    debt_ledger: dict | None = None,
    setting_ledger: dict | None = None,
    chosen_fork: dict | None = None,
    main_cast_size: int = 0,
    retries: int = 2,
) -> dict:
    """Beat-sheet with Phase-4 continuity + off-page tracking + v4
    typed hooks, irreversible events, year_dilemma POV, collision plan.

    v4 inputs:
    - `previous_hooks_typed` — previous chapter's typed hooks list;
      dramatic-seed entries get priority in hooks_to_resolve.
    - `decade_spine` — injected so the beat sheet plants hooks that
      feed the decade's question.
    - `main_cast_size` — drives whether collision_plan.required is
      forced to true (>=3 mains => yes).
    """
    prev_hooks = list(previous_hooks_typed or [])
    if prev_hooks:
        prev_block_lines: list[str] = []
        for h in prev_hooks:
            ptype = h.get("type") or "admin-carry-over"
            hid = h.get("hook_id") or ""
            text = h.get("hook") or ""
            stake = h.get("stake") or ""
            line = f"- [{ptype}] {hid}: {text}"
            if stake:
                line += f"  (stake: {stake})"
            prev_block_lines.append(line)
        prev_hooks_block = "\n".join(prev_block_lines)
    else:
        prev_hooks_block = (
            "(no previous chapter yet — hooks_to_resolve may be an "
            "empty list)"
        )
    recent_years = recent_off_page_years or []
    if recent_years and len(recent_years) >= OFF_PAGE_CONSECUTIVE_LIMIT:
        off_page_guidance = (
            f"The last {OFF_PAGE_CONSECUTIVE_LIMIT} consecutive years "
            f"({sorted(recent_years)}) all used the OFF-PAGE tool. If "
            f"this year also keeps its big event off-page, the chapters "
            f"will cumulatively start to feel evasive. STRONG PREFERENCE: "
            f"set `off_page_event` to null this year unless the dramatic "
            f"fit is extraordinary (an elegy, an aftermath that genuinely "
            f"reads better unstaged). When in doubt, put the event "
            f"on-page this year."
        )
    elif recent_years:
        off_page_guidance = (
            f"Recent off-page use: year(s) {sorted(recent_years)}. One "
            f"more year of evasion is fine if it fits; two consecutive "
            f"will not be."
        )
    else:
        off_page_guidance = (
            "No recent off-page use. You may choose off-page freely if "
            "the year has a single dominant event and aftermath would "
            "read stronger than staging."
        )

    open_debts = _open_debts(debt_ledger or {})
    long_debts = [d for d in open_debts if d.get("horizon_class") in ("mid", "long", "decade")]
    near_fraction = _near_debt_fraction(debt_ledger or {})
    current_promises = _promise_line_ids_for_current_act(decade_spine, year)
    claimed_promises = _claimed_promise_ids(setting_ledger or {})
    unclaimed_promises = sorted(pid for pid in current_promises if pid not in claimed_promises)
    recent_event_types = _setting_cooldown_context(
        setting_ledger or {"entries": []}, current_year=year
    ).get("irreversible_event_types", [])

    user = prompts.BEAT_SHEET_USER_TEMPLATE.format(
        year=year,
        decade_spine_json=_pretty_json(decade_spine) if decade_spine
        else "(no decade_spine available)",
        year_dilemma_json=_pretty_json(summary.get("year_dilemma") or {}),
        dossiers_json=_pretty_json(list(dossiers.values())),
        summary_json=_pretty_json(summary),
        crossinterference_json=_pretty_json(crossinterference),
        prev_chapter_text=prev_chapter_text or "(no previous chapter yet)",
        prev_year=prev_year if prev_year is not None else "n/a",
        previous_hooks_typed=prev_hooks_block,
        off_page_guidance=off_page_guidance,
        main_cast_size=main_cast_size,
        debt_ledger_json=_pretty_json({"open_debts": open_debts}),
        long_debt_guidance=(
            "No standing mid/long/decade debts yet; plant one now."
            if not long_debts else _pretty_json(long_debts[:8])
        ),
        near_debt_fraction=f"{near_fraction:.2f}",
        act_promise_options=(
            ", ".join(unclaimed_promises or sorted(current_promises))
            if current_promises else "(no promise_lines available)"
        ),
        recent_irreversible_event_types=(
            ", ".join(sorted(set(recent_event_types))) if recent_event_types else "(none)"
        ),
        chosen_fork_json=_pretty_json(chosen_fork or {}),
    )

    data: dict | None = None
    problem: str | None = None
    main_cast_ids = list(dossiers.keys())
    for attempt in range(retries + 1):
        raw = await _chat(
            client, "orchestrator",
            [{"role": "system", "content": prompts.BEAT_SHEET_SYSTEM},
             {"role": "user",   "content": user}],
            json_mode=True,
        )
        data = _parse_json(raw, where="beat_sheet")
        problem = _validate_beat_sheet(
            data, dossiers, crossinterference,
            previous_hooks_typed=prev_hooks,
            main_cast_ids=main_cast_ids,
            decade_spine=decade_spine,
            setting_ledger=setting_ledger,
            debt_ledger=debt_ledger,
            current_year=year,
            chosen_fork=chosen_fork,
        )
        if not problem:
            return data
        print(f"  [beat_sheet attempt {attempt + 1}: {problem}; retrying]")
        user += (
            f"\n\nPREVIOUS ATTEMPT REJECTED BECAUSE: {problem}\n"
            "Fix it. v4 HARD RULES: ordered_beats has 5..9 entries; "
            "every main-cast character appears in at least one beat's "
            "present_characters; hooks_to_plant has >=2 entries with "
            "AT LEAST ONE of type 'dramatic-seed'; irreversible_events "
            "has >=1 entry (type from: "
            f"{list(VALID_IRREVERSIBLE_TYPES)}); dilemma_pov_character_id "
            "is a main_cast id; act_promise_claim names a current "
            "promise_line id; hooks_to_plant includes >=1 long/decade "
            "horizon hook; if main_cast_size >= 3 then "
            "collision_plan.required is true and "
            "collision_plan.description names a scene with >=2 mains "
            "exercising agency."
        )

    raise RuntimeError(
        f"beat_sheet failed after {retries + 1} attempts: {problem}\n{_pretty_json(data)}"
    )


def _validate_beat_sheet(
    data: dict, dossiers: dict[str, dict], crossinterference: dict,
    *, previous_hooks_typed: list[dict] | None = None,
    main_cast_ids: list[str] | None = None,
    decade_spine: dict | None = None,
    setting_ledger: dict | None = None,
    debt_ledger: dict | None = None,
    current_year: int | None = None,
    chosen_fork: dict | None = None,
) -> str | None:
    for k in ("central_tension", "hooks_to_resolve", "hooks_to_plant",
              "ordered_beats", "side_characters",
              "dilemma_pov_character_id", "irreversible_events",
              "collision_plan", "act_promise_claim"):
        if k not in data:
            return f"missing key '{k}'"

    cast_ids = set(main_cast_ids or list(dossiers.keys()))

    # dilemma POV must be a main cast id.
    dpov = data.get("dilemma_pov_character_id")
    if not isinstance(dpov, str) or not dpov.strip():
        return "dilemma_pov_character_id must be a non-empty string"
    if dpov not in cast_ids:
        return (f"dilemma_pov_character_id '{dpov}' must be a main_cast "
                f"id (one of {sorted(cast_ids)})")

    if current_year is not None:
        promise_ids = _promise_line_ids_for_current_act(decade_spine, current_year)
        claim = data.get("act_promise_claim")
        if promise_ids:
            if not isinstance(claim, str) or claim not in promise_ids:
                return (
                    f"act_promise_claim '{claim}' must be one of the current "
                    f"act promise_line ids {sorted(promise_ids)}"
                )
        elif not isinstance(claim, str) or not claim.strip():
            return "act_promise_claim must be a non-empty string"

    # hooks_to_resolve + hooks_to_plant: v4 typed-objects shape. The
    # prompt shows the object shape; legacy string inputs from old
    # runs are rejected here because any new generation pass is
    # writing v4 schema. (Old chapter_index entries with string hooks
    # remain readable via _normalize_hooks.)
    res = data.get("hooks_to_resolve")
    plant = data.get("hooks_to_plant")
    if not isinstance(res, list):
        return "hooks_to_resolve must be a list"
    for j, h in enumerate(res):
        if not isinstance(h, dict):
            return (f"hooks_to_resolve[{j}] must be an object "
                    f"(got {type(h).__name__})")
        if not isinstance(h.get("hook"), str) or not h["hook"].strip():
            return f"hooks_to_resolve[{j}].hook must be a non-empty string"
    if not isinstance(plant, list):
        return "hooks_to_plant must be a list"
    for j, h in enumerate(plant):
        if not isinstance(h, dict):
            return (f"hooks_to_plant[{j}] must be an object "
                    f"(got {type(h).__name__})")
        for k in ("hook_id", "hook", "type", "horizon_class", "stake"):
            v = h.get(k)
            if not isinstance(v, str) or not v.strip():
                return f"hooks_to_plant[{j}].{k} must be a non-empty string"
        if h["type"] not in VALID_HOOK_TYPES:
            return (f"hooks_to_plant[{j}].type '{h['type']}' must be one of "
                    f"{list(VALID_HOOK_TYPES)}")
        horizon = h.get("horizon_class")
        if horizon not in VALID_HORIZON_CLASSES:
            return (f"hooks_to_plant[{j}].horizon_class '{horizon}' must be "
                    f"one of {list(VALID_HORIZON_CLASSES)}")
        ripens = h.get("ripens_by_year")
        if not isinstance(ripens, int) or isinstance(ripens, bool):
            return f"hooks_to_plant[{j}].ripens_by_year must be an integer"
        if h.get("spine_act") is not None:
            if h.get("spine_act") not in (1, 2, 3):
                return f"hooks_to_plant[{j}].spine_act must be 1, 2, or 3"
        spc = h.get("spine_promise_claim")
        if spc is not None and (not isinstance(spc, str) or not spc.strip()):
            return f"hooks_to_plant[{j}].spine_promise_claim must be a non-empty string"
        if current_year is not None and horizon in LONG_HORIZON_CLASSES:
            if not isinstance(ripens, int) or ripens - current_year < 5:
                return (f"hooks_to_plant[{j}] claims long horizon but "
                        f"ripens_by_year={ripens!r}; long debts must ripen "
                        f">=5 years out")
    if len(plant) < CONTINUITY_MIN_HOOKS_PLANTED:
        return (f"hooks_to_plant has {len(plant)} entries; need >= "
                f"{CONTINUITY_MIN_HOOKS_PLANTED}")
    dramatic_seed_count = sum(1 for h in plant if h.get("type") == "dramatic-seed")
    if dramatic_seed_count < DRAMATIC_SEED_MIN_PER_YEAR:
        return (f"hooks_to_plant has {dramatic_seed_count} dramatic-seed "
                f"hook(s); need >= {DRAMATIC_SEED_MIN_PER_YEAR} to give "
                f"next year narrative propulsion")
    if current_year is not None:
        long_count = 0
        for h in plant:
            horizon = h.get("horizon_class") or _horizon_class(
                current_year, h.get("ripens_by_year")
            )
            if horizon in LONG_HORIZON_CLASSES:
                long_count += 1
        if long_count < 1:
            return "hooks_to_plant must include >=1 long or decade horizon debt"

    # Require >= required pickup of previous hooks, prioritising
    # dramatic-seed entries when available.
    prev_hooks = list(previous_hooks_typed or [])
    if prev_hooks:
        required = min(CONTINUITY_MIN_HOOKS_RESOLVED, len(prev_hooks))
        if len(res) < required:
            return (f"previous chapter planted {len(prev_hooks)} typed "
                    f"hook(s); hooks_to_resolve must include at least "
                    f"{required} (has {len(res)})")

    # irreversible_events: v4 requires >=1.
    irr = data.get("irreversible_events")
    if not isinstance(irr, list) or len(irr) < IRREVERSIBLE_MIN_PER_YEAR:
        return (f"irreversible_events must have at least "
                f"{IRREVERSIBLE_MIN_PER_YEAR} entries; got {irr!r}")
    irr_ids: set[str] = set()
    for j, ev in enumerate(irr):
        if not isinstance(ev, dict):
            return f"irreversible_events[{j}] must be an object"
        for k in ("event_id", "type", "actor", "summary"):
            v = ev.get(k)
            if not isinstance(v, str) or not v.strip():
                return f"irreversible_events[{j}].{k} must be a non-empty string"
        if ev["type"] not in VALID_IRREVERSIBLE_TYPES:
            return (f"irreversible_events[{j}].type '{ev['type']}' must be "
                    f"one of {list(VALID_IRREVERSIBLE_TYPES)}")
        on_page = ev.get("on_page")
        if not isinstance(on_page, bool):
            return f"irreversible_events[{j}].on_page must be boolean"
        if on_page is False:
            cons = ev.get("on_page_consequence")
            if not isinstance(cons, str) or not cons.strip():
                return (f"irreversible_events[{j}] is off-page but has no "
                        f"`on_page_consequence`; an off-page event must still "
                        f"be ratified on-page by its visible aftermath")
        irr_ids.add(ev["event_id"])
    if current_year is not None and setting_ledger is not None:
        recent_types = set(_setting_cooldown_context(
            setting_ledger, current_year=current_year
        ).get("irreversible_event_types", []))
        if recent_types and not any(ev.get("type") not in recent_types for ev in irr):
            return (
                "irreversible_events must include at least one type not used "
                f"in the last {SETTING_COOLDOWNS['irreversible_event_types']} "
                f"years (recent types: {sorted(recent_types)})"
            )

    # ordered_beats
    beats = data["ordered_beats"]
    if not isinstance(beats, list) or not (5 <= len(beats) <= 9):
        return f"ordered_beats must have 5..9 entries, got {len(beats) if isinstance(beats, list) else type(beats).__name__}"

    appearing: set[str] = set()
    valid_interaction_ids = {i["id"] for i in crossinterference.get("cross_domain_interactions", [])}
    irr_carried: set[str] = set()
    for i, b in enumerate(beats):
        for k in ("beat_id", "interaction_id", "present_characters", "summary", "scale", "purpose"):
            if k not in b:
                return f"ordered_beats[{i}] missing '{k}'"
        if b["scale"] not in ("world", "scene"):
            return f"ordered_beats[{i}] invalid scale '{b['scale']}'"
        iid = b["interaction_id"]
        if iid not in ("context", "character") and iid not in valid_interaction_ids:
            return (f"ordered_beats[{i}].interaction_id '{iid}' must be 'context', 'character', "
                    f"or one of {sorted(valid_interaction_ids)}")
        present = b.get("present_characters", []) or []
        if not isinstance(present, list):
            return f"ordered_beats[{i}].present_characters must be a list"
        for j, p in enumerate(present):
            if not isinstance(p, str) or not p.strip():
                return f"ordered_beats[{i}].present_characters[{j}] must be a non-empty string"
        appearing.update(present)
        cev = b.get("carries_irreversible_event_id")
        if cev:
            if cev not in irr_ids:
                return (f"ordered_beats[{i}].carries_irreversible_event_id "
                        f"'{cev}' not in irreversible_events ids "
                        f"{sorted(irr_ids)}")
            irr_carried.add(cev)

    fork_actor = (chosen_fork or {}).get("actor")
    if fork_actor and isinstance(fork_actor, str) and dpov and fork_actor != dpov:
        if not any(b.get("fork_staged_on_site") is True for b in beats):
            return (
                "chosen fork actor differs from dilemma_pov_character_id; at "
                "least one ordered_beats entry must set fork_staged_on_site=true "
                "and stage the fork's irreversible act where it happens"
            )

    missing = cast_ids - appearing
    if missing:
        return f"cast members never appear in any beat's present_characters: {sorted(missing)}"

    # collision_plan
    cp = data.get("collision_plan")
    if not isinstance(cp, dict):
        return "collision_plan must be an object"
    req = cp.get("required")
    if not isinstance(req, bool):
        return "collision_plan.required must be boolean"
    if len(cast_ids) >= COLLISION_CAST_THRESHOLD and not req:
        return (f"collision_plan.required must be true when "
                f"main_cast.size >= {COLLISION_CAST_THRESHOLD} (got "
                f"{len(cast_ids)} mains)")
    if req:
        desc = cp.get("description")
        if not isinstance(desc, str) or not desc.strip():
            return ("collision_plan.required is true but description is "
                    "empty — name the scene in which >=2 mains "
                    "exercise agency")

    # off_page_event optional
    ope = data.get("off_page_event")
    if ope is not None:
        if not isinstance(ope, dict):
            return f"off_page_event must be an object or null, got {type(ope).__name__}"
        for k in ("what", "when", "how_referenced"):
            if k not in ope:
                return f"off_page_event present but missing '{k}'"

    return None


# --------------------------------------------------------------------------- #
# Stage 6a: Chapter Outline (Narrator pass 1, mid tier — Phase 2 + 3)
#
# Picks the chapter's SHAPE: reader's compass, structure, scene budget,
# section plan, opening line seed (Phase 2); plus voice_palette
# (base/modulator/device, chosen from code-computed candidates) and
# slop-ledger awareness (Phase 3). year_mood is INHERITED from the
# summariser — the outline no longer invents it. structure must not
# recur within STRUCTURE_WINDOW years; palette axes must not recur
# within PALETTE_WINDOW years.
# --------------------------------------------------------------------------- #

async def run_chapter_outline(
    client: AsyncOpenAI,
    *,
    year: int,
    summary: dict,
    crossinterference: dict,
    dossiers: dict[str, dict],
    beat_sheet: dict,
    prev_chapter_text: str,
    prev_year: int | None,
    recent_modes: list[str],
    mosaic_saturated: bool,
    palette_candidates: dict[str, list[dict]],
    active_slop: list[dict],
    decade_spine: dict | None = None,
    recent_stagings: list[str] | None = None,
    setting_ledger: dict | None = None,
    retries: int = 2,
) -> dict:
    recent_modes_str = (
        ", ".join(recent_modes) if recent_modes else "(none — no recent chapters)"
    )
    required_mood = summary.get("year_mood")
    central_tension = summary.get("central_tension", "")
    year_dilemma = summary.get("year_dilemma") or {}
    candidate_base_ids = [b["id"] for b in palette_candidates["bases"]]
    candidate_modulator_ids = [m["id"] for m in palette_candidates["modulators"]]
    candidate_device_ids = [d["id"] for d in palette_candidates["devices"]]
    slop_for_prompt = _render_slop_list(active_slop, include_notes=True)
    stagings = list(recent_stagings or [])
    stagings_block = (
        "\n".join(f"- {s}" for s in stagings) if stagings
        else "(no recent stagings — choose freely)"
    )

    mosaic_cap_status = (
        f"saturated (mosaic already used {MOSAIC_CAP} time(s) in the last "
        f"{MOSAIC_CAP_WINDOW} years — do NOT pick mosaic)"
        if mosaic_saturated
        else f"ok (mosaic not yet saturated in the last {MOSAIC_CAP_WINDOW} years)"
    )
    # Compute the word budget intersection of the chosen year_mood's range
    # and each mode's chapter_word range — the outline picks the mode, so
    # we present all intersections as guidance.
    mood_bucket = MOOD_BUDGETS.get(required_mood)
    if isinstance(mood_bucket, tuple) and len(mood_bucket) >= 3:
        mood_low, mood_high = mood_bucket[1], mood_bucket[2]
    else:
        mood_low, mood_high = 0, 1_000_000
    hint_lines = []
    for mid, spec in CHAPTER_MODES.items():
        lo = max(spec["chapter_word_low"], mood_low)
        hi = min(spec["chapter_word_high"], mood_high)
        if lo <= hi:
            hint_lines.append(f"- {mid}: {lo}-{hi} words")
        else:
            hint_lines.append(
                f"- {mid}: (no overlap between mode "
                f"[{spec['chapter_word_low']}-"
                f"{spec['chapter_word_high']}] and mood "
                f"[{mood_low}-{mood_high}]; either pick a different mode or "
                f"widen toward mode range)"
            )
    word_budget_hint = "\n  " + "\n  ".join(hint_lines)

    chapter_modes_block = _render_chapter_modes_card()
    setting_context = _setting_cooldown_context(
        setting_ledger or {"entries": []}, current_year=year
    )

    user = prompts.CHAPTER_OUTLINE_USER_TEMPLATE.format(
        year=year,
        decade_spine_json=_pretty_json(decade_spine) if decade_spine
        else "(no decade_spine available)",
        year_dilemma_json=_pretty_json(year_dilemma),
        central_tension=central_tension,
        summary_json=_pretty_json(summary),
        crossinterference_json=_pretty_json(crossinterference),
        dossiers_json=_pretty_json(list(dossiers.values())),
        beat_sheet_json=_pretty_json(beat_sheet),
        prev_chapter_text=prev_chapter_text or "(no previous chapter yet)",
        prev_year=prev_year if prev_year is not None else "n/a",
        recent_modes=recent_modes_str,
        mosaic_cap_status=mosaic_cap_status,
        chapter_modes_block=chapter_modes_block,
        word_budget_hint=word_budget_hint,
        year_mood=required_mood,
        palette_candidates_json=_pretty_json(palette_candidates),
        candidate_base_ids=", ".join(candidate_base_ids),
        candidate_modulator_ids=", ".join(candidate_modulator_ids),
        candidate_device_ids=", ".join(candidate_device_ids),
        recent_stagings=stagings_block,
        setting_ledger_json=_pretty_json(setting_ledger or {"entries": []}),
        setting_cooldown_context_json=_pretty_json(setting_context),
        valid_time_scales=", ".join(VALID_TIME_SCALES),
        valid_plot_shapes=", ".join(VALID_PLOT_SHAPES),
        active_slop_list=slop_for_prompt,
    )

    data: dict | None = None
    problem: str | None = None
    for attempt in range(retries + 1):
        raw = await _chat(
            client, "orchestrator",
            [{"role": "system", "content": prompts.CHAPTER_OUTLINE_SYSTEM},
             {"role": "user",   "content": user}],
            json_mode=True,
        )
        data = _parse_json(raw, where="chapter_outline")
        problem = _validate_chapter_outline(
            data,
            beat_sheet=beat_sheet,
            recent_modes=recent_modes,
            mosaic_saturated=mosaic_saturated,
            required_mood=required_mood,
            candidate_base_ids=candidate_base_ids,
            candidate_modulator_ids=candidate_modulator_ids,
            candidate_device_ids=candidate_device_ids,
            setting_ledger=setting_ledger,
            current_year=year,
        )
        if not problem:
            return data
        print(f"  [chapter_outline attempt {attempt + 1}: {problem}; retrying]")
        allowed_modes = [m for m in VALID_MODES
                         if m not in recent_modes
                         and not (m == "mosaic" and mosaic_saturated)]
        if not allowed_modes:
            allowed_modes = list(VALID_MODES)
        user += (
            f"\n\nPREVIOUS ATTEMPT REJECTED BECAUSE: {problem}\n"
            f"Fix it. v4 HARD CONSTRAINTS: `mode` MUST be one of "
            f"{allowed_modes} (not in {recent_modes}; mosaic forbidden "
            f"if saturated). year_mood MUST equal '{required_mood}'. "
            f"voice_palette.base in {candidate_base_ids}, modulator in "
            f"{candidate_modulator_ids}, device in {candidate_device_ids}. "
            f"scene_budget must respect the chosen mode's min/max scenes; "
            f"each scene MUST include a `contract` object with ALL of "
            f"{list(SCENE_CONTRACT_FIELDS)} as non-empty strings; each "
            f"scene has `opening_image` (not `anchor`) and NO `line`. "
            f"v5 fields place_signature, place_family, pov_gravity_well_id, "
            f"time_scale and plot_shape are required and must respect cooldowns "
            f"unless variance_override is present. "
            f"Every beat_id appears in some section; every scene_id "
            f"appears in some section."
        )

    raise RuntimeError(
        f"chapter_outline failed after {retries + 1} attempts: {problem}\n"
        f"{_pretty_json(data)}"
    )


def _render_chapter_modes_card() -> str:
    """Human-readable table of v4 chapter modes for the outline prompt."""
    lines: list[str] = []
    for mid, spec in CHAPTER_MODES.items():
        lines.append(
            f"- {mid}: {spec['min_scenes']}-{spec['max_scenes']} scenes, "
            f"words {spec['chapter_word_low']}-{spec['chapter_word_high']}, "
            f"dialogue ratio floor {spec['dialogue_floor']:.2f} — "
            f"{spec['description']}"
        )
    return "\n".join(lines)


def _validate_chapter_outline(
    data: dict, *, beat_sheet: dict, recent_modes: list[str],
    mosaic_saturated: bool,
    required_mood: str,
    candidate_base_ids: list[str],
    candidate_modulator_ids: list[str],
    candidate_device_ids: list[str],
    setting_ledger: dict | None = None,
    current_year: int | None = None,
) -> str | None:
    # v4 required keys: `mode` replaces `structure`; `opening_image` replaces
    # per-scene `anchor`; `line` is removed. voice_palette + readers_compass
    # + scene contract remain.
    required = (
        "readers_compass", "year_mood", "mode", "mode_rationale",
        "place_signature", "place_family", "pov_gravity_well_id",
        "time_scale", "plot_shape", "act_promise_claimed",
        "word_budget", "scene_budget", "section_plan", "opening_line_seed",
        "voice_palette",
    )
    for k in required:
        if k not in data:
            return f"missing key '{k}'"

    compass = data["readers_compass"]
    if not isinstance(compass, dict):
        return "readers_compass must be an object"
    for k in ("follow_what", "change_what", "hook"):
        v = compass.get(k)
        if not isinstance(v, str) or not v.strip():
            return f"readers_compass.{k} must be a non-empty string"

    # v4: chapter mode.
    mode = data["mode"]
    if mode not in VALID_MODES:
        return f"mode '{mode}' not in {list(VALID_MODES)}"
    if mode in recent_modes:
        return (f"mode '{mode}' was used within the last "
                f"{MODE_REPEAT_WINDOW} years (recent: {recent_modes}); pick another")
    if mode == "mosaic" and mosaic_saturated:
        return (f"mode 'mosaic' is capped at {MOSAIC_CAP} use(s) per "
                f"{MOSAIC_CAP_WINDOW} years; pick another mode")
    mode_spec = CHAPTER_MODES[mode]

    for k in ("place_signature", "place_family", "pov_gravity_well_id"):
        v = data.get(k)
        if not isinstance(v, str) or not v.strip():
            return f"{k} must be a non-empty string"
    time_scale = data.get("time_scale")
    if time_scale not in VALID_TIME_SCALES:
        return f"time_scale '{time_scale}' not in {list(VALID_TIME_SCALES)}"
    plot_shape = data.get("plot_shape")
    if plot_shape not in VALID_PLOT_SHAPES:
        return f"plot_shape '{plot_shape}' not in {list(VALID_PLOT_SHAPES)}"
    if data.get("act_promise_claimed") != beat_sheet.get("act_promise_claim"):
        return (
            "act_promise_claimed must echo beat_sheet.act_promise_claim "
            f"({beat_sheet.get('act_promise_claim')!r})"
        )
    if current_year is not None and setting_ledger is not None:
        context = _setting_cooldown_context(setting_ledger, current_year=current_year)
        violations: list[str] = []
        for axis in ("place_signature", "place_family", "pov_gravity_well_id",
                     "time_scale", "plot_shape"):
            if data.get(axis) in set(context.get(axis, [])):
                violations.append(axis)
        irr_types = [
            ev.get("type") for ev in beat_sheet.get("irreversible_events") or []
            if isinstance(ev, dict) and ev.get("type")
        ]
        recent_irr = set(context.get("irreversible_event_types") or [])
        if recent_irr and irr_types and not any(t not in recent_irr for t in irr_types):
            violations.append("irreversible_event_types")
        override = data.get("variance_override")
        if violations:
            if not isinstance(override, dict) or not isinstance(override.get("justification"), str) or not override["justification"].strip():
                return (
                    f"setting cooldown violation on {violations}; provide "
                    "variance_override.justification or pick fresher axes"
                )
            if context.get("recent_variance_overrides"):
                return (
                    "variance_override already used within the last "
                    f"{VARIANCE_OVERRIDE_WINDOW} years "
                    f"({context['recent_variance_overrides']}); pick fresher axes"
                )

    # Mood: still enforced by summariser choice.
    mood = data["year_mood"]
    if mood not in VALID_MOODS:
        return f"year_mood '{mood}' not in {VALID_MOODS}"
    if mood != required_mood:
        return (f"year_mood '{mood}' must echo the summariser's "
                f"year_mood '{required_mood}' — you do not pick the mood")
    # v4: each mode carries an `allowed_moods` set; reject the obvious
    # mismatches (e.g. `mosaic` paired with the `acute` mood). This was
    # data in the registry with no enforcement — so a model that picked
    # mosaic under acute would slip through even though the mode is
    # registered as fragment-dossier-energy.
    allowed_moods = mode_spec.get("allowed_moods") or set()
    if allowed_moods and mood not in allowed_moods:
        return (f"mode '{mode}' does not support year_mood '{mood}' — "
                f"allowed moods for this mode are "
                f"{sorted(allowed_moods)}; pick a different mode")
    wb = data["word_budget"]
    if not isinstance(wb, dict) or "low" not in wb or "high" not in wb:
        return "word_budget must have 'low' and 'high' integer fields"
    try:
        wlow, whigh = int(wb["low"]), int(wb["high"])
    except (TypeError, ValueError):
        return f"word_budget.low/high must be ints, got {wb!r}"
    # Mode dictates word envelope. (Mood still constrains via MOOD_BUDGETS
    # on the legacy path but in v4 the mode is the authoritative shape.)
    cwl, cwh = mode_spec["chapter_word_low"], mode_spec["chapter_word_high"]
    if not (cwl <= wlow <= whigh <= cwh):
        return (f"word_budget {{low:{wlow}, high:{whigh}}} must sit inside "
                f"the '{mode}' mode range [{cwl}, {cwh}]")

    # Scene budget + v4 scene contract.
    scenes = data["scene_budget"]
    if not isinstance(scenes, list):
        return "scene_budget must be a list"
    smin, smax = mode_spec["min_scenes"], mode_spec["max_scenes"]
    if not (smin <= len(scenes) <= smax):
        return (f"scene_budget has {len(scenes)} scenes; mode '{mode}' "
                f"requires {smin}..{smax}")
    scene_ids: set[str] = set()
    empty_who_scenes = 0
    for i, s in enumerate(scenes):
        for k in ("scene_id", "when", "where", "who", "opening_image",
                  "contract"):
            if k not in s:
                return f"scene_budget[{i}] missing '{k}'"
        if "line" in s:
            return (f"scene_budget[{i}] has legacy field 'line'; v4 "
                    f"dropped this — move the beat into `contract.turn`")
        if "anchor" in s:
            return (f"scene_budget[{i}] has legacy field 'anchor'; v4 "
                    f"renamed to `opening_image`")
        sid = s["scene_id"]
        if not isinstance(sid, str) or not sid:
            return f"scene_budget[{i}].scene_id must be a non-empty string"
        if sid in scene_ids:
            return f"scene_budget[{i}] duplicate scene_id '{sid}'"
        scene_ids.add(sid)
        who = s.get("who") or []
        if not isinstance(who, list):
            return f"scene_budget[{i}].who must be a list"
        for j, w in enumerate(who):
            if not isinstance(w, str) or not w.strip():
                return f"scene_budget[{i}].who[{j}] must be a non-empty string"
        if not who:
            empty_who_scenes += 1
        contract = s.get("contract")
        if not isinstance(contract, dict):
            return f"scene_budget[{i}].contract must be an object"
        for ck in SCENE_CONTRACT_FIELDS:
            cv = contract.get(ck)
            if not isinstance(cv, str) or not cv.strip():
                return (f"scene_budget[{i}].contract.{ck} must be a non-"
                        f"empty string — this is the v4 scene craft "
                        f"contract (desire/obstacle/turn/cost/gesture/"
                        f"subtext)")
    if empty_who_scenes > 1:
        return (f"at most 1 scene may have empty 'who'; this chapter is "
                f"populated by people (got {empty_who_scenes})")

    # Section plan.
    sections = data["section_plan"]
    min_sections = 1 if mode in ("monoscene", "long-march") else 2
    if not isinstance(sections, list) or not (min_sections <= len(sections) <= 7):
        return (f"section_plan must have {min_sections}..7 entries, got "
                f"{len(sections) if isinstance(sections, list) else type(sections).__name__}")
    valid_beat_ids = {b["beat_id"] for b in beat_sheet.get("ordered_beats", [])}
    referenced_beats: set[str] = set()
    referenced_scenes: set[str] = set()
    for i, sec in enumerate(sections):
        for k in ("section_id", "role_in_structure", "scale", "beat_ids",
                  "scene_ids", "goal"):
            if k not in sec:
                return f"section_plan[{i}] missing '{k}'"
        if sec["scale"] not in ("world", "scene", "mixed"):
            return f"section_plan[{i}] invalid scale '{sec['scale']}'"
        sec_beat_ids = sec.get("beat_ids", []) or []
        sec_scene_ids = sec.get("scene_ids", []) or []
        if not isinstance(sec_beat_ids, list):
            return f"section_plan[{i}].beat_ids must be a list"
        if not isinstance(sec_scene_ids, list):
            return f"section_plan[{i}].scene_ids must be a list"
        for bid in sec_beat_ids:
            if not isinstance(bid, str):
                return f"section_plan[{i}].beat_ids contains non-string entry {bid!r}"
            if bid not in valid_beat_ids:
                return (f"section_plan[{i}] references beat_id '{bid}' not in "
                        f"beat sheet ids {sorted(valid_beat_ids)}")
            referenced_beats.add(bid)
        for sid in sec_scene_ids:
            if not isinstance(sid, str):
                return f"section_plan[{i}].scene_ids contains non-string entry {sid!r}"
            if sid not in scene_ids:
                return (f"section_plan[{i}] references scene_id '{sid}' not in "
                        f"scene_budget ids {sorted(scene_ids)}")
            referenced_scenes.add(sid)
    missing_beats = valid_beat_ids - referenced_beats
    if missing_beats:
        return f"section_plan does not reference every beat: missing {sorted(missing_beats)}"
    missing_scenes = scene_ids - referenced_scenes
    if missing_scenes:
        return f"section_plan does not reference every scene: missing {sorted(missing_scenes)}"

    # Opening line seed — reject the banned retrospective openers.
    opening = (data["opening_line_seed"] or "").strip().lower()
    banned_prefixes = ("in 20", "in 21", "by year's end", "by years end",
                       "the year 20", "the year 21")
    if any(opening.startswith(p) for p in banned_prefixes):
        return (f"opening_line_seed begins with a banned retrospective cliché "
                f"(got {data['opening_line_seed']!r}); choose a different opening lean")

    # Phase 3: voice palette must pick one of each axis from the supplied
    # candidate ids, plus a 1-sentence justification referencing
    # central_tension (we just check non-empty; the prompt asks for the
    # reference and the reader will judge the rest).
    palette = data["voice_palette"]
    if not isinstance(palette, dict):
        return "voice_palette must be an object"
    for k in ("base", "modulator", "device", "justification"):
        v = palette.get(k)
        if not isinstance(v, str) or not v.strip():
            return f"voice_palette.{k} must be a non-empty string"
    if palette["base"] not in candidate_base_ids:
        return (f"voice_palette.base '{palette['base']}' not in "
                f"candidate bases {candidate_base_ids}")
    if palette["modulator"] not in candidate_modulator_ids:
        return (f"voice_palette.modulator '{palette['modulator']}' not in "
                f"candidate modulators {candidate_modulator_ids}")
    if palette["device"] not in candidate_device_ids:
        return (f"voice_palette.device '{palette['device']}' not in "
                f"candidate devices {candidate_device_ids}")

    return None


# --------------------------------------------------------------------------- #
# Stage 6e: Rupture Authorisation (v5 — cheap typed surprise slot)
# --------------------------------------------------------------------------- #

async def run_rupture_authorisation(
    client: AsyncOpenAI,
    *,
    year: int,
    chapter_outline: dict,
    beat_sheet: dict,
    debt_ledger: dict,
    side_cast: dict,
    rupture_log: dict,
    retries: int = 2,
) -> dict:
    constraints = _rupture_constraints(rupture_log, year)
    user = prompts.RUPTURE_AUTH_USER_TEMPLATE.format(
        year=year,
        chapter_outline_json=_pretty_json(chapter_outline),
        beat_sheet_json=_pretty_json(beat_sheet),
        debt_ledger_json=_pretty_json({"open_debts": _open_debts(debt_ledger)}),
        side_cast_json=_pretty_json(side_cast),
        rupture_log_json=_pretty_json(rupture_log),
        rupture_constraints_json=_pretty_json(constraints),
        valid_rupture_types=", ".join(VALID_RUPTURE_TYPES),
    )
    data: dict | None = None
    problem: str | None = None
    for attempt in range(retries + 1):
        raw = await _chat(
            client, "specialist",
            [{"role": "system", "content": prompts.RUPTURE_AUTH_SYSTEM},
             {"role": "user",   "content": user}],
            json_mode=True,
        )
        data = _parse_json(raw, where="rupture_authorisation")
        problem = _validate_rupture_authorisation(data, constraints=constraints)
        if not problem:
            return data
        print(f"  [rupture attempt {attempt + 1}: {problem}; retrying]")
        user += (
            f"\n\nPREVIOUS ATTEMPT REJECTED BECAUSE: {problem}\n"
            f"Fix it. `rupture` may be null unless constraints force one. "
            f"If present, type must be one of {list(VALID_RUPTURE_TYPES)} "
            f"and actor_id/reason/expected_effect/audit_signal are required."
        )
    raise RuntimeError(
        f"rupture_authorisation failed after {retries + 1} attempts: {problem}\n"
        f"{_pretty_json(data)}"
    )


def _validate_rupture_authorisation(data: dict, *, constraints: dict) -> str | None:
    if not isinstance(data, dict):
        return "rupture authorisation must be an object"
    if "year" not in data:
        return "missing year"
    rupture = data.get("rupture")
    if rupture is None:
        if constraints.get("force_rupture"):
            return "rupture is forced after quiet streak; rupture may not be null"
        return None
    if constraints.get("must_be_quiet"):
        return "rupture_log has too many consecutive ruptured years; this year must be quiet"
    if not isinstance(rupture, dict):
        return "rupture must be an object or null"
    rtype = rupture.get("type")
    if rtype not in VALID_RUPTURE_TYPES:
        return f"rupture.type '{rtype}' not in {list(VALID_RUPTURE_TYPES)}"
    if constraints.get("recent_types") and rtype == constraints["recent_types"][0]:
        return f"rupture.type '{rtype}' repeats last year's rupture type"
    for k in ("actor_id", "reason", "expected_effect", "audit_signal"):
        v = rupture.get(k)
        if not isinstance(v, str) or not v.strip():
            return f"rupture.{k} must be a non-empty string"
    return None


# --------------------------------------------------------------------------- #
# Stage 6f: Narrator Execute (premium tier — Phase 2 + 3 + v5 rupture)
#
# Renders the outline to prose. No longer chooses shape — the outline
# already did. Honours the chosen voice_palette (base + modulator +
# device, Phase 3) and avoids phrases on the active slop ledger.
# --------------------------------------------------------------------------- #

async def run_storyteller(
    client: AsyncOpenAI,
    *,
    year: int,
    previous_summary: dict | None,
    current_summary: dict,
    crossinterference: dict,
    narrative_threads: list,
    dossiers: dict[str, dict],
    beat_sheet: dict,
    chapter_outline: dict,
    prev_chapter_text: str,
    prev_year: int | None,
    style_guide: str,
    active_slop: list[dict],
    decade_spine: dict | None = None,
    rupture: dict | None = None,
) -> str:
    palette = chapter_outline.get("voice_palette") or {}
    palette_card = _palette_card(palette)
    slop_for_prompt = _render_slop_list(active_slop, include_notes=False)
    year_dilemma = current_summary.get("year_dilemma") or {}
    user = prompts.STORYTELLER_USER_TEMPLATE.format(
        style_guide=style_guide,
        year=year,
        decade_spine_json=_pretty_json(decade_spine) if decade_spine
        else "(no decade_spine available)",
        year_dilemma_json=_pretty_json(year_dilemma),
        previous_summary_json=_pretty_json(previous_summary) if previous_summary else "null",
        current_summary_json=_pretty_json(current_summary),
        crossinterference_json=_pretty_json(crossinterference),
        narrative_threads_json=_pretty_json(narrative_threads),
        dossiers_json=_pretty_json(list(dossiers.values())),
        beat_sheet_json=_pretty_json(beat_sheet),
        chapter_outline_json=_pretty_json(chapter_outline),
        rupture_json=_pretty_json(rupture or {"rupture": None}),
        prev_chapter_text=prev_chapter_text or "(no previous chapter yet)",
        prev_year=prev_year if prev_year is not None else "n/a",
        palette_card=palette_card,
        active_slop_list=slop_for_prompt,
    )
    return await _chat(
        client, "storyteller",
        [{"role": "system", "content": prompts.STORYTELLER_SYSTEM},
         {"role": "user",   "content": user}],
        stream=True,
    )


def _render_slop_list(active_slop: list[dict], *, include_notes: bool) -> str:
    """Format the active slop-ledger phrases for a prompt. Uses a single
    conventional block across outline/narrator/editor so the models see
    the same shape everywhere. A reminder about the 'YYYY' placeholder
    is appended only if any active entry actually uses it — otherwise
    we'd be teaching a convention the model will never encounter."""
    if not active_slop:
        return "(ledger clean this year — nothing in cooldown)"
    lines: list[str] = []
    for e in active_slop:
        phrase = e.get("phrase", "")
        if include_notes:
            note = e.get("note", "")
            lines.append(f"- \"{phrase}\"  ({note})" if note else f"- \"{phrase}\"")
        else:
            lines.append(f"- \"{phrase}\"")
    if any("YYYY" in (e.get("phrase") or "") for e in active_slop):
        lines.append(
            "(NB: 'YYYY' is a placeholder for any 4-digit year — e.g. "
            "\"In YYYY,\" forbids \"In 2028,\", \"In 2031,\", etc.)"
        )
    return "\n".join(lines)


def _palette_card(palette: dict) -> str:
    """Render the chosen voice palette with exemplars as a compact prompt
    block. Keeps registry lookups code-side so prompts stay in sync as the
    registry evolves."""
    base_id = palette.get("base", "")
    mod_id = palette.get("modulator", "")
    dev_id = palette.get("device", "")
    base = VOICE_BASES.get(base_id, {})
    mod = VOICE_MODULATORS.get(mod_id, {})
    dev = VOICE_DEVICES.get(dev_id, {})
    justification = palette.get("justification", "")
    lines = [
        f"BASE        : {base_id}",
        f"  what it is: {base.get('description','')}",
        f"  exemplar  : {base.get('exemplar','')}",
        f"MODULATOR   : {mod_id}",
        f"  what it is: {mod.get('description','')}",
        f"  exemplar  : {mod.get('exemplar','')}",
        f"DEVICE      : {dev_id}",
        f"  what it is: {dev.get('description','')}",
        f"  exemplar  : {dev.get('exemplar','')}",
        f"JUSTIFICATION (outliner): {justification}",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Stage 7: Editor (premium tier — preserves outline + voice_palette,
# enforces active slop ledger)
# --------------------------------------------------------------------------- #

async def run_editor(
    client: AsyncOpenAI, *, draft_prose: str, chapter_outline: dict,
    style_guide: str, active_slop: list[dict],
    fix_block: str = "",
    year_dilemma: dict | None = None,
    beat_sheet: dict | None = None,
    rupture: dict | None = None,
) -> str:
    """Editor polish. Phase 4 adds an optional `fix_block` that's
    prepended to the user prompt on a continuity-retry so the editor
    addresses the auditor's concrete concerns in one pass. v4: editor
    also receives the year_dilemma (so retries don't flatten the choice)
    and the beat sheet (so it knows which irreversible events must stay
    on-page)."""
    palette = chapter_outline.get("voice_palette") or {}
    palette_card = _palette_card(palette)
    slop_for_prompt = _render_slop_list(active_slop, include_notes=True)
    user = prompts.EDITOR_USER_TEMPLATE.format(
        style_guide=style_guide,
        chapter_outline_json=_pretty_json(chapter_outline),
        beat_sheet_json=_pretty_json(beat_sheet) if beat_sheet
        else "(no beat sheet supplied)",
        year_dilemma_json=_pretty_json(year_dilemma or {}),
        rupture_json=_pretty_json(rupture or {"rupture": None}),
        draft_prose=draft_prose,
        palette_card=palette_card,
        active_slop_list=slop_for_prompt,
    )
    if fix_block:
        # Prepend rather than append — put the FIX: block at the top so
        # the editor sees it before the draft, not after.
        user = f"{fix_block}\n\n{user}"
    return await _chat(
        client, "editor",
        [{"role": "system", "content": prompts.EDITOR_SYSTEM},
         {"role": "user",   "content": user}],
        stream=True,
    )


# --------------------------------------------------------------------------- #
# Stage 7b: Continuity Pass (Phase 4 — mid tier, short)
#
# Reads the post-editor final chapter + its structural contract (outline,
# beat sheet, cast, dossiers, previous hooks, active slop ledger) and
# emits a structured audit. If the audit fails, a targeted fix_notes
# block goes back to the editor for one retry; beyond that, the chapter
# ships with `degraded: true` in the report.
# --------------------------------------------------------------------------- #

async def run_continuity_pass(
    client: AsyncOpenAI,
    *,
    year: int,
    final_chapter: str,
    chapter_outline: dict,
    beat_sheet: dict,
    cast_plan: dict,
    dossiers: dict[str, dict],
    previous_hooks_typed: list[dict],
    prev_chapter_text: str,
    prev_year: int | None,
    active_slop: list[dict],
    decade_spine: dict | None = None,
    year_dilemma: dict | None = None,
    rupture: dict | None = None,
    setting_ledger: dict | None = None,
    debt_ledger: dict | None = None,
    chosen_fork: dict | None = None,
) -> dict:
    palette = chapter_outline.get("voice_palette") or {}
    palette_card = _palette_card(palette)
    slop_for_prompt = _render_slop_list(active_slop, include_notes=True)
    prev_hooks = list(previous_hooks_typed or [])
    if prev_hooks:
        prev_hooks_block = "\n".join(
            f"- [{h.get('type','admin-carry-over')}] "
            f"{h.get('hook_id','(no-id)')}: {h.get('hook','')}"
            for h in prev_hooks
        )
    else:
        prev_hooks_block = (
            "(no previous chapter — hooks_resolved_from_previous may be empty)"
        )
    user = prompts.CONTINUITY_PASS_USER_TEMPLATE.format(
        year=year,
        decade_spine_json=_pretty_json(decade_spine) if decade_spine
        else "(no decade_spine available)",
        year_dilemma_json=_pretty_json(year_dilemma or {}),
        chapter_outline_json=_pretty_json(chapter_outline),
        beat_sheet_json=_pretty_json(beat_sheet),
        rupture_json=_pretty_json(rupture or {"rupture": None}),
        setting_ledger_json=_pretty_json(setting_ledger or {"entries": []}),
        debt_ledger_json=_pretty_json(debt_ledger or {"debts": []}),
        chosen_fork_json=_pretty_json(chosen_fork or {}),
        cast_plan_json=_pretty_json(cast_plan),
        dossiers_json=_pretty_json(list(dossiers.values())),
        previous_hooks_typed=prev_hooks_block,
        palette_card=palette_card,
        active_slop_list=slop_for_prompt,
        prev_chapter_text=prev_chapter_text or "(no previous chapter yet)",
        prev_year=prev_year if prev_year is not None else "n/a",
        final_chapter=final_chapter,
    )
    raw = await _chat(
        client, "orchestrator",
        [{"role": "system", "content": prompts.CONTINUITY_PASS_SYSTEM},
         {"role": "user",   "content": user}],
        json_mode=True,
    )
    data = _parse_json(raw, where="continuity_pass")

    # Code-side cross-checks — do not trust the LLM's self-reported
    # verdict alone. Build a list of concrete fix items so the editor
    # has something to act on.
    audit_problems: list[str] = _audit_continuity_report(
        data,
        cast_plan=cast_plan,
        beat_sheet=beat_sheet,
        previous_hooks_typed=prev_hooks,
        chapter_outline=chapter_outline,
        rupture=rupture,
        setting_ledger=setting_ledger,
        debt_ledger=debt_ledger,
        current_year=year,
        chosen_fork=chosen_fork,
    )
    data["code_audit_problems"] = audit_problems
    if audit_problems and data.get("verdict") == "pass":
        data["verdict"] = "fail"
        existing_fix = (data.get("fix_notes") or "").strip()
        code_fix = "CODE-SIDE AUDIT FLAGGED: " + "; ".join(audit_problems)
        data["fix_notes"] = (
            f"{existing_fix}\n{code_fix}".strip() if existing_fix else code_fix
        )
    elif audit_problems:
        # Verdict already fail; just append the code findings so the
        # editor sees both model- and code-level issues in one block.
        existing_fix = (data.get("fix_notes") or "").strip()
        code_fix = "CODE-SIDE AUDIT ALSO FLAGGED: " + "; ".join(audit_problems)
        data["fix_notes"] = (
            f"{existing_fix}\n{code_fix}".strip() if existing_fix else code_fix
        )
    return data


def _audit_continuity_report(
    data: dict, *, cast_plan: dict, beat_sheet: dict,
    previous_hooks_typed: list[dict],
    chapter_outline: dict | None = None,
    rupture: dict | None = None,
    setting_ledger: dict | None = None,
    debt_ledger: dict | None = None,
    current_year: int | None = None,
    chosen_fork: dict | None = None,
) -> list[str]:
    """Cheap deterministic cross-checks on top of the LLM's audit.

    v4 additions:
    - change_audit: every main_cast id must have a change_delta; at
      least one must be non-empty (chapter must change somebody).
    - irreversibility_audit: every beat-sheet irreversible_event_id
      must be observed on-page (or explicitly ratified off-page via
      aftermath if the beat sheet marked it off-page).
    - in_scene_ratio: flag when below IN_SCENE_WORDS_MIN_RATIO.
    - collision_audit: when beat_sheet.collision_plan.required, prose
      must stage it.
    - typed hooks: hooks_planted_observed must include >=1 dramatic-
      seed; hooks_resolved_from_previous must reference hook_ids from
      the typed previous list.
    """
    problems: list[str] = []

    # 1. Every main_cast id must have appears == true.
    expected_ids = [e["id"] for e in cast_plan.get("main_cast", [])]
    appearances = data.get("cast_appearances") or {}
    missing = []
    for cid in expected_ids:
        entry = appearances.get(cid)
        if not isinstance(entry, dict):
            missing.append(cid)
            continue
        if not entry.get("appears"):
            missing.append(cid)
    if missing:
        problems.append(
            f"cast members absent or not confirmed in prose: "
            f"{missing} (they must each appear at least once with a "
            f"concrete action or perception — retiring/deceased "
            f"characters get a final_beat sentence)"
        )

    # 2. Hooks resolved count (typed; previous hook_ids).
    prev_hooks = list(previous_hooks_typed or [])
    if prev_hooks:
        required_resolved = min(
            CONTINUITY_MIN_HOOKS_RESOLVED, len(prev_hooks)
        )
        resolved = data.get("hooks_resolved_from_previous") or []
        if len(resolved) < required_resolved:
            problems.append(
                f"only {len(resolved)} previous-chapter hook(s) picked "
                f"up (need >= {required_resolved}); the hooks waiting "
                f"to be resolved are: "
                f"{[h.get('hook_id') or h.get('hook') for h in prev_hooks]}"
            )
        # Prefer dramatic-seed pickup when one was planted.
        dramatic_ids = {h.get("hook_id") for h in prev_hooks
                        if h.get("type") == "dramatic-seed"
                        and h.get("hook_id")}
        if dramatic_ids and resolved:
            resolved_ids: set[str] = set()
            for r in resolved:
                if isinstance(r, dict):
                    rid = r.get("hook_id")
                    if rid:
                        resolved_ids.add(rid)
                elif isinstance(r, str):
                    resolved_ids.add(r)
            if not (resolved_ids & dramatic_ids):
                problems.append(
                    f"previous chapter planted dramatic-seed hook(s) "
                    f"{sorted(dramatic_ids)} but none of them were "
                    f"picked up — dramatic seeds must ripen into story, "
                    f"not evaporate"
                )

    # 3. Hooks planted count + dramatic-seed presence.
    planted = data.get("hooks_planted_observed") or []
    if len(planted) < CONTINUITY_MIN_HOOKS_PLANTED:
        problems.append(
            f"only {len(planted)} hooks observed planted (need >= "
            f"{CONTINUITY_MIN_HOOKS_PLANTED}); the chapter must leave "
            f"at least two open questions for the next one"
        )
    # The auditor may emit either strings or objects; accept both.
    planted_types: list[str] = []
    for p in planted:
        if isinstance(p, dict):
            t = p.get("type")
            if isinstance(t, str):
                planted_types.append(t)
    # Only enforce dramatic-seed presence if the auditor emitted types at
    # all. (If they emitted pure strings we trust the beat-sheet-level
    # check the validator already performed.)
    if planted_types:
        if sum(1 for t in planted_types if t == "dramatic-seed") \
                < DRAMATIC_SEED_MIN_PER_YEAR:
            problems.append(
                f"no dramatic-seed hook observed in prose "
                f"(need >= {DRAMATIC_SEED_MIN_PER_YEAR}) — the chapter "
                f"is not feeding the decade spine forward"
            )

    # 4. Device satisfaction.
    palette_fid = data.get("palette_fidelity") or {}
    if palette_fid.get("device_satisfied") is False:
        problems.append(
            "voice_palette.device constraint is not satisfied — the "
            "device is a hard constraint and must be restored"
        )

    # 5. Invented names.
    invented = data.get("invented_names") or []
    if invented:
        problems.append(
            f"invented names not traceable to dossiers/specialists: "
            f"{invented} (cut them or replace with paraphrase)"
        )

    # 6. Off-page honored when declared.
    ope = beat_sheet.get("off_page_event")
    if ope is not None:
        honored = data.get("off_page_honored")
        if honored is not True:
            problems.append(
                "off_page_event was declared in the beat sheet but "
                "the chapter does not honour it (stages it directly, "
                "or the auditor could not confirm off-page treatment) "
                "— reference the event via date / aftermath / "
                "paperwork instead of depicting it"
            )

    # 7. Change audit: shape is {cid: {verdict, axis, evidence}}.
    # Every main_cast id must have a verdict; at least
    # CHANGE_AUDIT_MIN_CHANGED_MAINS entries must be `changed`.
    change_audit = data.get("change_audit") or {}
    if expected_ids:
        missing_verdicts = [
            cid for cid in expected_ids
            if not isinstance(change_audit.get(cid), dict)
            or (change_audit.get(cid) or {}).get("verdict") not in ("changed", "unchanged")
        ]
        if missing_verdicts:
            problems.append(
                f"change_audit missing verdict for: {missing_verdicts} "
                f"— every main cast member needs a verdict of 'changed' "
                f"or 'unchanged' plus a one-line evidence"
            )
        changed = [
            cid for cid in expected_ids
            if isinstance(change_audit.get(cid), dict)
            and change_audit[cid].get("verdict") == "changed"
        ]
        if expected_ids and len(changed) < CHANGE_AUDIT_MIN_CHANGED_MAINS:
            problems.append(
                f"only {len(changed)} main cast member(s) show a "
                f"genuine change; need >= "
                f"{CHANGE_AUDIT_MIN_CHANGED_MAINS} — at least one main "
                f"must visibly change each year (belief / status / "
                f"relationship / body)"
            )

    # 8. Irreversibility audit: prompt emits
    # irreversibility = {events_observed:[{event_id,on_page,...}],
    #                    budget_satisfied: bool}. Every declared event
    # must show up with on_page=true OR its on_page_consequence (for
    # off-page declared) must be staged — the auditor encodes both
    # cases as an entry in events_observed.
    declared_events = beat_sheet.get("irreversible_events") or []
    if declared_events:
        irr_block = data.get("irreversibility") or {}
        observed_list = irr_block.get("events_observed") or []
        observed_ids = {
            e.get("event_id") for e in observed_list
            if isinstance(e, dict) and e.get("event_id")
        }
        unobserved = [
            ev.get("event_id")
            for ev in declared_events
            if ev.get("event_id") and ev["event_id"] not in observed_ids
        ]
        if unobserved:
            problems.append(
                f"irreversible event(s) declared but not observed on-"
                f"page (or their consequences unvisible): {unobserved} "
                f"— the beat sheet promised these; the prose must "
                f"ratify them"
            )
        if irr_block.get("budget_satisfied") is False:
            problems.append(
                "irreversibility.budget_satisfied is false — chapter "
                "did not ratify a single irreversible event; the beat "
                "sheet's minimum is one per year"
            )

    # 9. In-scene ratio lives under mode_fidelity in the v4 report.
    mf = data.get("mode_fidelity") or {}
    ratio = mf.get("in_scene_ratio")
    if isinstance(ratio, (int, float)) and mf.get("mode_claimed") != "mosaic":
        if ratio < IN_SCENE_WORDS_MIN_RATIO:
            problems.append(
                f"in_scene_ratio {ratio:.2f} is below the v4 floor "
                f"{IN_SCENE_WORDS_MIN_RATIO:.2f} — too much "
                f"retrospective narration; push more prose into live "
                f"scenes"
            )
    if mf.get("mode_satisfied") is False:
        note = mf.get("mode_notes") or ""
        problems.append(
            f"mode_fidelity.mode_satisfied=false — chapter does not "
            f"honour its chosen mode '{mf.get('mode_claimed')}': "
            f"{note}"
        )
    # v4: if the claimed mode carries a dialogue_floor > 0 (today that
    # is only `overheard` at 0.60), enforce it deterministically when
    # the auditor reports a dialogue_ratio. The prompt's rule 5 reads
    # the same threshold; this catches the case where the auditor
    # reports a compliant `mode_satisfied=true` but a ratio that falls
    # below the floor the registry declares.
    claimed_mode = mf.get("mode_claimed")
    dialogue_ratio = mf.get("dialogue_ratio")
    mode_spec = CHAPTER_MODES.get(claimed_mode) if isinstance(claimed_mode, str) else None
    if mode_spec and isinstance(dialogue_ratio, (int, float)):
        floor = mode_spec.get("dialogue_floor") or 0.0
        if floor > 0 and dialogue_ratio < floor:
            problems.append(
                f"dialogue_ratio {dialogue_ratio:.2f} is below the "
                f"'{claimed_mode}' mode's dialogue_floor {floor:.2f} — "
                f"this mode is dialogue-forward; more of the chapter "
                f"must live inside direct or reported speech"
            )

    # 10. Collision audit: prompt emits collision={required,observed,evidence}.
    cp = beat_sheet.get("collision_plan") or {}
    if cp.get("required"):
        coll = data.get("collision") or {}
        if coll.get("observed") is False:
            problems.append(
                "collision_plan required but no scene stages >=2 "
                "main cast members exercising agency — fix by merging "
                "two subplots into a shared scene"
            )

    # 11. Scene contract fidelity: the auditor emits scene_contracts
    # with per-scene desire/turn/cost/gesture visibility flags. More
    # than one scene missing its turn/cost/gesture is a FAIL.
    contracts = data.get("scene_contracts") or []
    missing_core = [
        c.get("scene_id") for c in contracts
        if isinstance(c, dict) and not all(
            c.get(k) is True
            for k in ("turn_visible", "cost_visible", "gesture_visible")
        )
    ]
    if len(missing_core) > 1:
        problems.append(
            f"scene_contracts missing turn/cost/gesture in {missing_core} "
            f"— v4 requires each scene's turn, cost, and embodied gesture "
            f"to be on-page"
        )

    # 12. v5 setting variance + fork staging + promise/debt/rupture checks.
    if current_year is not None and chapter_outline is not None:
        compliance = data.get("setting_ledger_compliance") or {}
        if isinstance(compliance, dict):
            bad_axes = [
                axis for axis, ok in compliance.items()
                if axis in SETTING_COOLDOWNS and ok is False
            ]
            override = chapter_outline.get("variance_override")
            if bad_axes and not override:
                problems.append(
                    f"setting cooldown violation without variance_override: {bad_axes}"
                )
        if data.get("act_promise_realised") is False:
            problems.append(
                "act_promise_realised=false — the chapter claimed a spine "
                "promise but did not dramatise it on-page"
            )
        long_planted = data.get("debt_ledger_long_planted")
        if isinstance(long_planted, int) and long_planted < 1:
            problems.append(
                "debt_ledger_long_planted is below 1 — v5 requires one "
                "long or decade debt per year"
            )
        if data.get("irreversible_event_diversity") is False:
            problems.append(
                "irreversible_event_diversity=false — no irreversible event "
                "type was fresh against the last two years"
            )
    fork_actor = (chosen_fork or {}).get("actor")
    pov_well = (chapter_outline or {}).get("pov_gravity_well_id") \
        or beat_sheet.get("dilemma_pov_character_id")
    if fork_actor and pov_well and fork_actor != pov_well:
        if data.get("fork_staged_on_site") is not True:
            problems.append(
                "fork_staged_on_site=false — chosen fork actor differs from "
                "chapter POV gravity well, so the fork's irreversible act "
                "must be staged where it happens"
            )
    rdoc = rupture or {}
    if isinstance(rdoc, dict) and rdoc.get("rupture") is not None:
        if data.get("rupture_realised") is not True:
            problems.append(
                "rupture_realised=false — authorised rupture did not meet "
                "its audit_signal and must be preserved/fixed"
            )

    return problems


def _build_fix_block(report: dict) -> str:
    """Render the continuity report's fix_notes into an editor-ready
    FIX: block that's prepended to the editor's user prompt on retry.

    Falls back to the raw `issues` list (or a generic instruction) if
    the LLM returned a fail verdict with empty fix_notes — better an
    unspecific retry that still signals "fix continuity" than a retry
    with no guidance at all.
    """
    notes = (report.get("fix_notes") or "").strip()
    audit = report.get("code_audit_problems") or []
    issues = report.get("issues") or []

    if not notes and not audit and not issues:
        return ""

    header = (
        "FIX: the continuity audit flagged the following problems with "
        "the previous pass. Address EACH of them in your final prose. "
        "Do not add new facts; use the dossiers, beat sheet, and scene "
        "budget as the source of truth."
    )
    parts: list[str] = [header, ""]
    if audit:
        parts.append("Audit points (code-side):")
        parts.extend(f"  - {a}" for a in audit)
        parts.append("")
    if notes:
        parts.append("Auditor's notes:")
        parts.append(notes)
        parts.append("")
    elif issues:
        parts.append("Auditor's issues list:")
        parts.extend(f"  - {i}" for i in issues)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


async def _run_continuity_with_retry(
    client: AsyncOpenAI,
    *,
    run_dir: Path,
    year_dir: Path,
    year: int,
    final: str,
    chapter_outline: dict,
    beat_sheet: dict,
    cast_plan: dict,
    dossiers: dict[str, dict],
    previous_hooks_typed: list[dict],
    prev_chapter_text: str,
    prev_year: int | None,
    active_slop: list[dict],
    slop_ledger: dict,
    style_guide: str,
    decade_spine: dict | None = None,
    year_dilemma: dict | None = None,
    rupture: dict | None = None,
    setting_ledger: dict | None = None,
    debt_ledger: dict | None = None,
    chosen_fork: dict | None = None,
) -> tuple[str, dict, str, bool]:
    """Run the continuity pass; on fail, retry the editor once with a
    FIX: block and re-audit. Writes the report to disk after each pass
    so a crash between passes still leaves a usable audit on disk.

    Returns (final_prose, report, verdict, degraded).
    """
    report = await run_continuity_pass(
        client,
        year=year,
        final_chapter=final,
        chapter_outline=chapter_outline,
        beat_sheet=beat_sheet,
        cast_plan=cast_plan,
        dossiers=dossiers,
        previous_hooks_typed=previous_hooks_typed,
        prev_chapter_text=prev_chapter_text,
        prev_year=prev_year,
        active_slop=active_slop,
        decade_spine=decade_spine,
        year_dilemma=year_dilemma,
        rupture=rupture,
        setting_ledger=setting_ledger,
        debt_ledger=debt_ledger,
        chosen_fork=chosen_fork,
    )
    # Persist first-pass report immediately so a crash during the
    # editor retry doesn't lose the audit evidence.
    _write_json(year_dir / "07b_continuity_report.json", report)
    verdict = report.get("verdict", "pass")
    if verdict != "fail":
        print("  [continuity: PASS]")
        return final, report, verdict, False

    retries_left = CONTINUITY_RETRY_MAX
    if retries_left <= 0:
        # No retry budget — ship the first-pass result as degraded.
        report["degraded"] = True
        _write_json(year_dir / "07b_continuity_report.json", report)
        print(f"  [continuity: FAIL with no retry budget — shipping with degraded=true "
              f"(problems: {report.get('code_audit_problems', [])})]")
        return final, report, verdict, True

    print(f"  [continuity: FAIL on first pass — "
          f"{len(report.get('code_audit_problems', []))} code-side "
          f"problem(s); retrying editor once]")
    fix_block = _build_fix_block(report)

    _print_rule(f"Year {year} — editor rewrite (continuity retry)")
    final = await run_editor(
        client, draft_prose=final,
        chapter_outline=chapter_outline, style_guide=style_guide,
        active_slop=active_slop, fix_block=fix_block,
        year_dilemma=year_dilemma, beat_sheet=beat_sheet,
        rupture=rupture,
    )
    _write_text(year_dir / "07_story_final.md", final)
    slipped = _scan_and_refresh_slop(slop_ledger, final, year)
    if slipped:
        print(f"  [slop ledger (retry): re-armed {len(slipped)} phrase(s): {slipped}]")
    _save_slop_ledger(run_dir, slop_ledger)

    # Re-audit once.
    _print_rule(f"Year {year} — continuity pass (re-audit after editor retry)")
    report = await run_continuity_pass(
        client,
        year=year,
        final_chapter=final,
        chapter_outline=chapter_outline,
        beat_sheet=beat_sheet,
        cast_plan=cast_plan,
        dossiers=dossiers,
        previous_hooks_typed=previous_hooks_typed,
        prev_chapter_text=prev_chapter_text,
        prev_year=prev_year,
        active_slop=active_slop,
        decade_spine=decade_spine,
        year_dilemma=year_dilemma,
        rupture=rupture,
        setting_ledger=setting_ledger,
        debt_ledger=debt_ledger,
        chosen_fork=chosen_fork,
    )
    verdict = report.get("verdict", "pass")
    degraded = False
    if verdict != "pass":
        degraded = True
        report["degraded"] = True
        print(f"  [continuity: still FAIL after retry — shipping with degraded=true "
              f"(problems: {report.get('code_audit_problems', [])})]")
    else:
        print("  [continuity: PASS after retry]")
    _write_json(year_dir / "07b_continuity_report.json", report)
    return final, report, verdict, degraded


# --------------------------------------------------------------------------- #
# Stage 8: Fork Proposer (drastic, cross-domain)
# --------------------------------------------------------------------------- #

async def run_fork_proposer(
    client: AsyncOpenAI,
    *,
    year: int,
    summary: dict,
    crossinterference: dict,
    state: dict,
    story: str,
    recent_fork_domains: list[str] | None = None,
    decade_spine: dict | None = None,
    debt_ledger: dict | None = None,
    setting_ledger: dict | None = None,
    retries: int = 2,
) -> list[dict]:
    """Fork proposer — v4. Forks must be typed EVENTS (not trends), with
    an actor, an irreversible act, a named stake, a clock, and an
    explicit statement of how each fork advances (or bargains against)
    the decade spine.
    """
    recent_domains = list(recent_fork_domains or [])
    avoid_note = (
        ", ".join(recent_domains) if recent_domains
        else "(none — no recent chapters to lock in)"
    )
    user = prompts.FORK_PROPOSER_USER_TEMPLATE.format(
        year=year,
        next_year=year + 1,
        decade_spine_json=_pretty_json(decade_spine) if decade_spine
        else "(no decade_spine available — baseline year; propose forks that "
             "open up the seeded world without prejudging the spine)",
        summary_json=_pretty_json(summary),
        crossinterference_json=_pretty_json(crossinterference),
        state_json=_pretty_json(state),
        story=story,
        recent_fork_domains=avoid_note,
        debt_ledger_json=_pretty_json({"open_debts": _open_debts(debt_ledger or {})}),
        recent_irreversible_event_types=", ".join(sorted(set(
            _setting_cooldown_context(setting_ledger or {"entries": []}, current_year=year + 1)
            .get("irreversible_event_types", [])
        ))) or "(none)",
        near_debt_fraction=f"{_near_debt_fraction(debt_ledger or {}):.2f}",
    )

    forks: list[dict] = []
    problem: str | None = None
    for attempt in range(retries + 1):
        raw = await _chat(
            client, "orchestrator",
            [{"role": "system", "content": prompts.FORK_PROPOSER_SYSTEM},
             {"role": "user",   "content": user}],
            json_mode=True,
        )
        data = _parse_json(raw, where="fork_proposer")
        forks = data.get("forks", [])
        problem = _validate_forks(
            forks, recent_fork_domains=recent_domains,
            have_spine=decade_spine is not None,
            debt_ledger=debt_ledger,
        )
        if not problem:
            return forks
        print(f"  [fork_proposer attempt {attempt + 1}: {problem}; retrying]")
        user += (
            f"\n\nPREVIOUS ATTEMPT REJECTED BECAUSE: {problem}\n"
            f"v4 HARD RULES: exactly 3 forks; 3 distinct domains from "
            f"{list(VALID_DOMAINS)}; >=1 domain NOT in "
            f"{recent_domains}. Each fork MUST have: fork_type in "
            f"{list(VALID_FORK_TYPES)}, actor (named or specific role), "
            f"irreversible_act (single sentence), named_stake (who or "
            f"what is at risk), clock (a deadline phrase), "
            f"spine_advances ({{act: 1|2|3, how: '1 sentence'}}), "
            f"spine_wager_impact (string, "
            f"required if a decade_spine exists). Trends are NOT forks "
            f"— if it wouldn't work as a news headline, it's not a fork."
        )

    raise RuntimeError(
        f"fork_proposer failed after {retries + 1} attempts: {problem}\n"
        f"last forks={_pretty_json(forks)}"
    )


def _validate_forks(forks: list[dict], *,
                    recent_fork_domains: list[str] | None = None,
                    have_spine: bool = False,
                    debt_ledger: dict | None = None) -> str | None:
    if not isinstance(forks, list) or len(forks) != 3:
        return f"expected exactly 3 forks, got {len(forks) if isinstance(forks, list) else type(forks).__name__}"
    domains: list[str] = []
    required_keys = (
        "domain", "title", "drasticness", "flavor",
        "fork_type", "actor", "irreversible_act", "named_stake", "clock",
        "spine_advances",
    )
    for i, f in enumerate(forks):
        if not isinstance(f, dict):
            return f"fork[{i}] must be an object"
        for k in required_keys:
            if k not in f:
                return f"fork[{i}] missing key '{k}'"
        if f["domain"] not in VALID_DOMAINS:
            return f"fork[{i}] invalid domain '{f['domain']}' (must be one of {VALID_DOMAINS})"
        if f["drasticness"] not in ("moderate", "high", "extreme"):
            return f"fork[{i}] invalid drasticness '{f['drasticness']}'"
        if f["fork_type"] not in VALID_FORK_TYPES:
            return (f"fork[{i}] invalid fork_type '{f['fork_type']}' — "
                    f"must be one of {list(VALID_FORK_TYPES)}")
        for k in ("title", "flavor", "actor", "irreversible_act",
                  "named_stake", "clock"):
            v = f.get(k)
            if not isinstance(v, str) or not v.strip():
                return f"fork[{i}].{k} must be a non-empty string"
        sa = f.get("spine_advances")
        if not isinstance(sa, dict):
            return (f"fork[{i}].spine_advances must be an object "
                    f"{{act: 1|2|3, how: '1 sentence'}} "
                    f"(got {type(sa).__name__})")
        sa_act = sa.get("act")
        if not isinstance(sa_act, int) or isinstance(sa_act, bool) \
                or sa_act not in (1, 2, 3):
            return (f"fork[{i}].spine_advances.act must be an integer "
                    f"1, 2, or 3 (got {sa_act!r})")
        sa_how = sa.get("how")
        if not isinstance(sa_how, str) or not sa_how.strip():
            return (f"fork[{i}].spine_advances.how must be a non-empty "
                    f"string naming what this fork does to the act")
        if have_spine:
            impact = f.get("spine_wager_impact")
            if not isinstance(impact, str) or not impact.strip():
                return (f"fork[{i}].spine_wager_impact must be a non-empty "
                        f"string when a decade_spine exists — name how "
                        f"this fork moves the wager (which side ticks "
                        f"forward, or what price the wager would extract)")
        role = f.get("debt_role")
        if role is not None and role not in ("ripens-existing", "plants-new-horizon", "fresh-domain"):
            return (f"fork[{i}].debt_role must be one of ripens-existing, "
                    f"plants-new-horizon, fresh-domain (got {role!r})")
        # Cheap trend-filter: `irreversible_act` should be a single clause,
        # not a list of vague trends. Reject entries that read like trends
        # ("becomes more", "continues to", "increasingly").
        act = f["irreversible_act"].lower()
        for banned in ("continues to", "becomes more", "increasingly",
                       "there is a trend", "sees a rise"):
            if banned in act:
                return (f"fork[{i}].irreversible_act contains trend-language "
                        f"('{banned}') — forks must be events, not trends; "
                        f"name a specific act by a specific actor")
        domains.append(f["domain"])
    if len(set(domains)) != 3:
        return f"forks share domains: {domains} (must be 3 distinct domains)"
    recent = set(recent_fork_domains or [])
    if recent:
        fresh = [d for d in domains if d not in recent]
        if not fresh:
            return (f"all three forks use domains from the recent "
                    f"chosen-fork set {sorted(recent)}; at least one "
                    f"fork must use a domain NOT in that set "
                    f"(anti-lock-in rule)")
    roles = {f.get("debt_role") for f in forks if f.get("debt_role")}
    if _open_debts(debt_ledger or {}) and "ripens-existing" not in roles:
        return "at least one fork must have debt_role='ripens-existing'"
    if "plants-new-horizon" not in roles:
        return "at least one fork must have debt_role='plants-new-horizon'"
    return None


# --------------------------------------------------------------------------- #
# Phase 5: stage helpers (load-or-run dispatch for replay.py)
#
# `generate_epoch` takes a `start_from` stage id. For every stage whose id
# is BEFORE `start_from` in STAGE_ORDER, the artefact is loaded from disk
# instead of recomputed. Stages AT or AFTER `start_from` run normally.
# This lets `replay.py` re-run downstream stages on an existing run for
# fast prompt iteration (plan §10 Phase 5: "Essential for safely
# iterating on prompts").
# --------------------------------------------------------------------------- #

def _stage_index(stage: str) -> int:
    if stage == "06":
        stage = "06f"  # legacy alias for pre-v5 narrator stage
    try:
        return STAGE_ORDER.index(stage)
    except ValueError as e:
        raise ValueError(
            f"unknown stage id '{stage}'; valid ids: {list(STAGE_ORDER)}"
        ) from e


def _should_run(stage: str, start_from: str) -> bool:
    """True iff `stage` is at or after `start_from` in STAGE_ORDER."""
    return _stage_index(stage) >= _stage_index(start_from)


def _load_json_strict(path: Path, *, context: str) -> Any:
    if not path.exists():
        raise FileNotFoundError(
            f"{context}: required artefact missing at {path}. Replay needs "
            f"every stage earlier than --from-stage to be present on disk."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _load_text_strict(path: Path, *, context: str) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"{context}: required artefact missing at {path}. Replay needs "
            f"every stage earlier than --from-stage to be present on disk."
        )
    return path.read_text(encoding="utf-8")


def _load_dossiers_from_disk(year_dir: Path, cast_plan: dict) -> dict[str, dict]:
    """Mirror of what `run_character_dossiers` produces. Keyed by char id,
    reading files written as `06b_dossier_<id>.json`."""
    out: dict[str, dict] = {}
    for entry in cast_plan.get("main_cast", []):
        cid = entry["id"]
        path = year_dir / f"06b_dossier_{cid}.json"
        out[cid] = _load_json_strict(path, context=f"dossier[{cid}]")
    return out


def _load_specialist_docs_from_disk(year_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for facet in VALID_DOMAINS:
        path = year_dir / f"02_specialist_{facet}.json"
        out[facet] = _load_json_strict(path, context=f"specialist[{facet}]")
    return out


# --------------------------------------------------------------------------- #
# Phase 5: readability metrics (`09_readability.json`, pure code, per epoch)
#
# Plan §8. One flat JSON row per year — cast counts, scenes, unique places,
# regions, facets covered, structure, palette, hooks resolved/planted, slop
# tics that slipped past the editor. This is how we audit a long run at a
# glance without re-reading every chapter, and how A/B prompt tuning gets
# diffable evidence instead of vibes.
#
# All fields are derived from artefacts already on disk after a normal
# epoch — no additional LLM calls.
# --------------------------------------------------------------------------- #

def _normalize_place(place: str) -> str:
    """Collapse whitespace and casing so 'The Port of Lagos' and
    'the  port of  lagos' count as the same scene_budget[].where."""
    return " ".join((place or "").strip().lower().split())


def _collect_regions(specialist_docs: dict[str, dict]) -> set[str]:
    """Union of geographic regions named across the 5 specialist docs.

    Draws on two shapes the specialist prompt emits:
      - headline_developments[*].region
      - regional_breakouts (keys)

    Normalized like places (whitespace + case). 'Global' is counted —
    a 'Global' plus 4 specific regions is still 5 regions covered
    (and the prompt rarely says 'Global' unless the scope truly is)."""
    regions: set[str] = set()
    for doc in specialist_docs.values():
        for h in doc.get("headline_developments", []) or []:
            reg = h.get("region") if isinstance(h, dict) else None
            if isinstance(reg, str) and reg.strip():
                regions.add(_normalize_place(reg))
        breakouts = doc.get("regional_breakouts")
        if isinstance(breakouts, dict):
            for reg in breakouts.keys():
                if isinstance(reg, str) and reg.strip():
                    regions.add(_normalize_place(reg))
    return regions


def _count_cast_by_status(cast_plan: dict) -> tuple[int, int, int, int]:
    """Return (named_people_count, returning, new, retired) from cast_plan.
    `retired` covers both `retiring` and `deceased`."""
    main = cast_plan.get("main_cast", []) or []
    total = len(main)
    returning = sum(1 for e in main if e.get("status") == "returning")
    new_chars = sum(1 for e in main if e.get("status") == "introduced")
    retired = sum(1 for e in main if e.get("status") in ("retiring", "deceased"))
    return total, returning, new_chars, retired


def compute_readability(
    *,
    year: int,
    cast_plan: dict,
    chapter_outline: dict,
    beat_sheet: dict,
    specialist_docs: dict[str, dict],
    crossinterference: dict,
    continuity_report: dict,
    final_prose: str,
    active_slop: list[dict],
    continuity_verdict: str | None,
    degraded: bool,
    rupture: dict | None = None,
) -> dict:
    """Build the per-epoch readability record. Plan §8 shape — with a
    few extra bookkeeping fields (`year`, `continuity_verdict`,
    `degraded`) so a grep across `runs/*/year_*/09_readability.json`
    reads as one diffable table.

    slop_tics_flagged: the active slop phrases that actually appeared
    in the final prose. Recomputed here via the same matcher the
    editor used (`_slop_phrase_matches`) so readability reflects the
    prose the reader sees, not a pre-retry draft.
    """
    total, returning, new_chars, retired = _count_cast_by_status(cast_plan)

    scenes = chapter_outline.get("scene_budget") or []
    places = {
        _normalize_place(s.get("where", ""))
        for s in scenes
        if isinstance(s, dict) and s.get("where")
    }
    regions = _collect_regions(specialist_docs)

    # Facets covered = distinct domains named across cross-interference
    # interactions. Usually 5 (every specialist is represented) but
    # falls when the world shrinks around a dominant fork, which is
    # exactly what Phase 4's rotation rule exists to prevent.
    facets: set[str] = set()
    for inter in crossinterference.get("cross_domain_interactions", []) or []:
        for d in (inter.get("domains_involved") or []):
            if isinstance(d, str) and d.strip():
                facets.add(d.strip())

    palette_out = {
        k: (chapter_outline.get("voice_palette") or {}).get(k)
        for k in ("base", "modulator", "device")
    }

    # Hooks resolved / planted: record the strings (not just counts) so
    # a diff across years can show which thread was picked up where.
    hooks_resolved = list(
        continuity_report.get("hooks_resolved_from_previous") or []
    )
    hooks_planted_raw = list(beat_sheet.get("hooks_to_plant") or [])
    # v4: readability keeps a concise string for the human-readable
    # ledger even though the beat sheet stores objects.
    hooks_planted: list[str] = []
    dramatic_seed_count = 0
    for h in hooks_planted_raw:
        if isinstance(h, dict):
            hooks_planted.append(h.get("hook", ""))
            if h.get("type") == "dramatic-seed":
                dramatic_seed_count += 1
        elif isinstance(h, str):
            hooks_planted.append(h)

    # Slop tics flagged = active ledger phrases that appear in the
    # final prose. Rescan rather than trust `_scan_and_refresh_slop`'s
    # in-memory list — replays only have the final text, not the
    # scan log, and this keeps the metric a pure function of inputs.
    final_low = (final_prose or "").lower()
    slop_tics_flagged: list[str] = []
    for entry in active_slop:
        phrase = entry.get("phrase") or ""
        if _slop_phrase_matches(phrase, final_low):
            slop_tics_flagged.append(phrase)

    # v4: change_audit, irreversibility, collision all come from the
    # continuity report. Record summary stats for the per-epoch row.
    change_audit = continuity_report.get("change_audit") or {}
    changed_mains = sum(
        1 for v in change_audit.values()
        if isinstance(v, dict) and v.get("verdict") == "changed"
    )
    irr_block = continuity_report.get("irreversibility") or {}
    irr_observed = len(irr_block.get("events_observed") or [])
    coll_block = continuity_report.get("collision") or {}
    collision_satisfied = coll_block.get("observed")
    mf = continuity_report.get("mode_fidelity") or {}
    in_scene_ratio = mf.get("in_scene_ratio")

    return {
        "year": year,
        "named_people_count": total,
        "returning_characters": returning,
        "new_characters": new_chars,
        "retired_characters": retired,
        "scenes_count": len(scenes),
        "unique_places": len(places),
        "regions_covered": len(regions),
        "facets_covered": len(facets),
        # v4: `mode` supersedes `structure`; we keep both keys (legacy
        # runs still have structure) so a grep across runs continues to
        # work.
        "mode_used": chapter_outline.get("mode"),
        "structure_used": chapter_outline.get("structure"),
        "time_shape_used": chapter_outline.get("time_scale") or chapter_outline.get("time_shape"),
        "plot_shape_used": chapter_outline.get("plot_shape"),
        "place_family": chapter_outline.get("place_family"),
        "palette": palette_out,
        "hooks_resolved": hooks_resolved,
        "hooks_planted": hooks_planted,
        "dramatic_seeds_planted": dramatic_seed_count,
        "long_debts_planted": continuity_report.get("debt_ledger_long_planted"),
        "debts_discharged": continuity_report.get("debt_ledger_discharged") or [],
        "rupture_type": (
            ((rupture or {}).get("rupture") or {}).get("type")
            if isinstance(rupture, dict) else None
        ),
        "rupture_realised": continuity_report.get("rupture_realised"),
        "changed_mains": changed_mains,
        "irreversible_events_declared": len(beat_sheet.get("irreversible_events") or []),
        "irreversible_events_observed": irr_observed,
        "collision_required": bool(
            (beat_sheet.get("collision_plan") or {}).get("required")
        ),
        "collision_satisfied": collision_satisfied,
        "in_scene_ratio": in_scene_ratio,
        "slop_tics_flagged": slop_tics_flagged,
        "continuity_verdict": continuity_verdict,
        "degraded": bool(degraded),
    }


# --------------------------------------------------------------------------- #
# Full epoch
# --------------------------------------------------------------------------- #

async def generate_epoch(
    client: AsyncOpenAI,
    *,
    run_dir: Path,
    year_dir: Path,
    parent_state: dict,
    chosen_fork: dict,
    previous_summary: dict | None,
    prev_chapter_text: str,
    prev_year: int | None,
    style_guide: str,
    start_from: str = "02",
) -> dict:
    """Run one year of the pipeline.

    Phase 5: `start_from` controls the first stage to recompute. Stages
    earlier than `start_from` in `STAGE_ORDER` are loaded from disk
    instead of run (replay.py drives this for fast prompt iteration).
    Default `"02"` runs the whole pipeline, matching pre-Phase-5
    behaviour. Post-processing (cast/arcs/chapter_index/slop_ledger
    updates, readability metrics) is gated on whether the feeder stage
    was actually re-run — idempotent replays keep the ledgers coherent.
    """
    year = parent_state["year"] + 1
    year_dir.mkdir(parents=True, exist_ok=True)

    # Fail fast on a bogus start_from so replay.py doesn't silently run
    # a default-start pipeline when someone fat-fingers a stage id.
    _ = _stage_index(start_from)

    # v4: the decade spine is a one-time artefact; load whenever present.
    # Runs seeded before v4 have no spine on disk, which is fine — every
    # consumer falls back to a neutral string when it's None.
    decade_spine = _load_decade_spine(run_dir)
    chapter_index = _load_chapter_index(run_dir)
    setting_ledger = _load_setting_ledger(run_dir)
    debt_ledger = _load_debt_ledger(run_dir)
    rupture_log = _load_rupture_log(run_dir)

    # 01 fork (not LLM-backed; replay loads from disk, fresh runs persist
    # the fork passed in).
    if _should_run("02", start_from):
        _write_json(year_dir / "01_fork.json", chosen_fork)

    # 02 + 03 specialists in parallel, then state merger (pure code)
    if _should_run("02", start_from):
        _print_rule(f"Year {year} — running 5 specialists in parallel (deeper docs)")
        specialist_tasks = {
            name: run_specialist(
                client, name, spec,
                year=year, fork=chosen_fork,
                parent_state=parent_state,
                previous_summary=previous_summary,
            )
            for name, spec in prompts.SPECIALISTS.items()
        }
        results = await asyncio.gather(*specialist_tasks.values())
        specialist_docs = dict(zip(specialist_tasks.keys(), results))
        for name, doc in specialist_docs.items():
            _write_json(year_dir / f"02_specialist_{name}.json", doc)
            heads = len(doc.get("headline_developments", []))
            actors = len(doc.get("named_actors", []))
            print(f"  v {name:<12} headlines={heads} actors={actors}")
        new_state = copy.deepcopy(parent_state)
        new_state["year"] = year
        for doc in specialist_docs.values():
            new_state = _merge_specialist_updates(
                new_state, doc.get("state_updates", {})
            )
        _write_json(year_dir / "03_state.json", new_state)
    else:
        print(f"  [replay: loading specialists + state for year {year} from disk]")
        specialist_docs = _load_specialist_docs_from_disk(year_dir)
        new_state = _load_json_strict(
            year_dir / "03_state.json", context="state"
        )

    # 04 summarizer
    if _should_run("04", start_from):
        _print_rule(f"Year {year} — summarizer (balanced, all 5 facets)")
        summary = await run_summarizer(
            client, year=year, specialist_docs=specialist_docs,
            state=new_state, decade_spine=decade_spine,
            recent_tensions=_recent_central_tensions(chapter_index),
        )
        _write_json(year_dir / "04_summary.json", summary)
        print(f"  headline: {summary.get('headline_of_the_year', '(none)')}")
    else:
        summary = _load_json_strict(
            year_dir / "04_summary.json", context="summary"
        )

    # 05 cross-interference (Phase 4 rotation retry)
    if _should_run("05", start_from):
        _print_rule(f"Year {year} — cross-interference analyst "
                    f"(rotation: <={int(CROSS_INTERFERENCE_FORK_DOMAIN_LIMIT*100)}% "
                    f"touch fork='{chosen_fork.get('domain')}')")
        crossinterference = await run_cross_interference(
            client, year=year, summary=summary, specialist_docs=specialist_docs,
            fork_domain=chosen_fork.get("domain"),
        )
        _write_json(year_dir / "05_crossinterference.json", crossinterference)
        for inter in crossinterference.get("cross_domain_interactions", []):
            print(f"  * [{'+'.join(inter.get('domains_involved', []))}] {inter.get('title', '')}")
    else:
        crossinterference = _load_json_strict(
            year_dir / "05_crossinterference.json", context="crossinterference"
        )

    # Cast.json is always loaded: downstream stages call `_get_character`
    # for name/voice/home fields even when they don't re-plan the cast.
    cast = _load_cast(run_dir)

    # 06a cast plan — v4 feeds the decade spine + unchanged streaks in.
    if _should_run("06a", start_from):
        _print_rule(f"Year {year} — cast plan (3-{CAST_MAX} main characters)")
        chapter_index_for_streaks = _load_chapter_index(run_dir)
        streaks = _unchanged_streaks(
            chapter_index_for_streaks, current_year=year
        )
        cast_plan = await run_cast_plan(
            client,
            year=year,
            cast=cast,
            summary=summary,
            crossinterference=crossinterference,
            prev_chapter_text=prev_chapter_text,
            prev_year=prev_year,
            decade_spine=decade_spine,
            unchanged_streaks=streaks,
        )
        _write_json(year_dir / "06a_cast_plan.json", cast_plan)
        for entry in cast_plan["main_cast"]:
            name = entry.get("name") or (
                _get_character(cast, entry["id"]) or {}
            ).get("name", entry["id"])
            print(f"  - [{entry['status']:<11}] {name} — {entry.get('brief','')[:100]}")
    else:
        cast_plan = _load_json_strict(
            year_dir / "06a_cast_plan.json", context="cast_plan"
        )

    # 06b dossiers (character subagents, parallel, cheap tier)
    if _should_run("06b", start_from):
        _print_rule(f"Year {year} — character dossiers (parallel)")
        dossiers = await run_character_dossiers(
            client,
            year=year,
            run_dir=run_dir,
            cast_plan=cast_plan,
            cast=cast,
            summary=summary,
            crossinterference=crossinterference,
        )
        for cid, dos in dossiers.items():
            _write_json(year_dir / f"06b_dossier_{cid}.json", dos)
            print(f"  . {cid:<30} want: {dos.get('want','')[:70]}")
    else:
        dossiers = _load_dossiers_from_disk(year_dir, cast_plan)

    # Chapter-index + off-page context are read once and reused across
    # the beat sheet, outline, fork proposer, and final append.
    chapter_index = _load_chapter_index(run_dir)
    previous_hooks_typed = _previous_hooks_typed(chapter_index, year)
    previous_hooks_strings = [h.get("hook", "") for h in previous_hooks_typed
                              if h.get("hook")]
    recent_off_page = _recent_off_page_uses(chapter_index)

    # 06c beat sheet — v4 (typed hooks, irreversible events, collision
    # plan, dilemma POV).
    if _should_run("06c", start_from):
        dramatic_seeds = sum(1 for h in previous_hooks_typed
                             if h.get("type") == "dramatic-seed")
        _print_rule(
            f"Year {year} — beat sheet "
            f"(prev_hooks={len(previous_hooks_typed)} "
            f"[dramatic-seed={dramatic_seeds}], "
            f"recent_off_page={recent_off_page or '[]'})"
        )
        main_cast_size = len(cast_plan.get("main_cast") or [])
        beat_sheet = await run_beat_sheet(
            client,
            year=year,
            dossiers=dossiers,
            summary=summary,
            crossinterference=crossinterference,
            prev_chapter_text=prev_chapter_text,
            prev_year=prev_year,
            previous_hooks_typed=previous_hooks_typed,
            recent_off_page_years=recent_off_page,
            decade_spine=decade_spine,
            debt_ledger=debt_ledger,
            setting_ledger=setting_ledger,
            chosen_fork=chosen_fork,
            main_cast_size=main_cast_size,
        )
        _write_json(year_dir / "06c_beat_sheet.json", beat_sheet)
        print(f"  central_tension: {beat_sheet.get('central_tension','')}")
        print(f"  beats: {len(beat_sheet.get('ordered_beats', []))} "
              f"| hooks_to_plant: {len(beat_sheet.get('hooks_to_plant', []))} "
              f"| irreversible: {len(beat_sheet.get('irreversible_events', []))} "
              f"| collision: {(beat_sheet.get('collision_plan') or {}).get('required', False)} "
              f"| off-page: {'yes' if beat_sheet.get('off_page_event') else 'no'}")
        # v4: register named side characters so recurring clerks /
        # neighbours persist across years.
        _register_side_cast(run_dir, beat_sheet, year)
    else:
        beat_sheet = _load_json_strict(
            year_dir / "06c_beat_sheet.json", context="beat_sheet"
        )

    # Slop ledger is always loaded: narrator + editor + continuity all
    # receive the active-phrase list, even on replay (so the scan after
    # the editor refreshes the same ledger).
    slop_ledger = _load_slop_ledger(run_dir)
    active_slop = _active_slop_phrases(slop_ledger, year)

    # 06d chapter outline — v4 (chapter modes, staging ledger, palette
    # candidates honour mode-incompat + suppressive cap).
    if _should_run("06d", start_from):
        recent_modes = _recent_modes(chapter_index)
        mosaic_saturated = _mosaic_cap_saturated(chapter_index)
        palette_candidates = compute_palette_candidates(
            year_mood=summary.get("year_mood", "drift"),
            chapter_index=chapter_index,
        )
        cand_bases = [b["id"] for b in palette_candidates["bases"]]
        cand_mods = [m["id"] for m in palette_candidates["modulators"]]
        cand_devs = [d["id"] for d in palette_candidates["devices"]]
        stagings = sorted(_recent_stagings(run_dir, current_year=year))
        _print_rule(f"Year {year} — chapter outline "
                    f"(mood={summary.get('year_mood')}; "
                    f"avoid modes {recent_modes or '[none]'}, "
                    f"mosaic={'saturated' if mosaic_saturated else 'ok'}; "
                    f"bases={cand_bases} / mods={cand_mods})")
        chapter_outline = await run_chapter_outline(
            client,
            year=year,
            summary=summary,
            crossinterference=crossinterference,
            dossiers=dossiers,
            beat_sheet=beat_sheet,
            prev_chapter_text=prev_chapter_text,
            prev_year=prev_year,
            recent_modes=recent_modes,
            mosaic_saturated=mosaic_saturated,
            palette_candidates=palette_candidates,
            active_slop=active_slop,
            decade_spine=decade_spine,
            recent_stagings=stagings,
            setting_ledger=setting_ledger,
        )
        _write_json(year_dir / "06d_chapter_outline.json", chapter_outline)
        compass = chapter_outline.get("readers_compass", {})
        wb = chapter_outline.get("word_budget", {})
        pal = chapter_outline.get("voice_palette", {})
        mode = chapter_outline.get("mode")
        print(f"  mode:         {mode}  "
              f"(mood={chapter_outline.get('year_mood')}, "
              f"scenes={len(chapter_outline.get('scene_budget', []))}, "
              f"words={wb.get('low','?')}-{wb.get('high','?')})")
        print(f"  palette:      {pal.get('base')} + {pal.get('modulator')} "
              f"+ {pal.get('device')}")
        print(f"  follow_what:  {compass.get('follow_what','')}")
        print(f"  change_what:  {compass.get('change_what','')}")
        print(f"  hook:         {compass.get('hook','')}")
        # v4: register this chapter's scene stagings.
        _register_staging(run_dir, chapter_outline, year)
    else:
        chapter_outline = _load_json_strict(
            year_dir / "06d_chapter_outline.json", context="chapter_outline"
        )

    # 06e rupture authorisation (v5; cheap tier; optional typed surprise).
    if _should_run("06e", start_from):
        _print_rule(f"Year {year} — rupture authorisation (v5 typed surprise slot)")
        side_cast = _load_side_cast(run_dir)
        rupture_doc = await run_rupture_authorisation(
            client,
            year=year,
            chapter_outline=chapter_outline,
            beat_sheet=beat_sheet,
            debt_ledger=debt_ledger,
            side_cast=side_cast,
            rupture_log=rupture_log,
        )
        _write_json(year_dir / "06e_rupture.json", rupture_doc)
        _upsert_rupture_log(run_dir, year=year, rupture_doc=rupture_doc)
        rupture_log = _load_rupture_log(run_dir)
        rupture = rupture_doc.get("rupture")
        print(f"  rupture:      {rupture.get('type') if isinstance(rupture, dict) else 'quiet'}")
    else:
        rupture_path = year_dir / "06e_rupture.json"
        if rupture_path.exists():
            rupture_doc = _load_json_strict(rupture_path, context="rupture")
        else:
            rupture_doc = {"year": year, "rupture": None}

    # 06f narrator execute (premium tier; renders outline + rupture to prose)
    if _should_run("06f", start_from):
        _print_rule(f"Year {year} — narrator (executing outline + rupture to prose)")
        draft = await run_storyteller(
            client,
            year=year,
            previous_summary=previous_summary,
            current_summary=summary,
            crossinterference=crossinterference,
            narrative_threads=new_state.get("narrative_threads", []),
            dossiers=dossiers,
            beat_sheet=beat_sheet,
            chapter_outline=chapter_outline,
            prev_chapter_text=prev_chapter_text,
            prev_year=prev_year,
            style_guide=style_guide,
            active_slop=active_slop,
            decade_spine=decade_spine,
            rupture=rupture_doc,
        )
        _write_text(year_dir / "06f_story_draft.md", draft)
        # Legacy mirror so older tooling that opens 06_story_draft.md still works.
        _write_text(year_dir / "06_story_draft.md", draft)
    else:
        draft_path = year_dir / "06f_story_draft.md"
        if not draft_path.exists():
            draft_path = year_dir / "06_story_draft.md"
        draft = _load_text_strict(draft_path, context="story_draft")

    # 07 editor polish — on replay from >07, load the saved final.
    if _should_run("07", start_from):
        _print_rule(f"Year {year} — editor polishing")
        final = await run_editor(
            client, draft_prose=draft,
            chapter_outline=chapter_outline, style_guide=style_guide,
            active_slop=active_slop,
            year_dilemma=summary.get("year_dilemma"),
            beat_sheet=beat_sheet,
            rupture=rupture_doc,
        )
        _write_text(year_dir / "07_story_final.md", final)
        # Re-arm cooldowns for any seeded slop phrase the editor let
        # through (cheap code-side scan; no extra LLM call).
        slipped = _scan_and_refresh_slop(slop_ledger, final, year)
        if slipped:
            print(f"  [slop ledger: {len(slipped)} seeded phrase(s) slipped through "
                  f"and had cooldowns re-armed: {slipped}]")
        _save_slop_ledger(run_dir, slop_ledger)
    else:
        final = _load_text_strict(
            year_dir / "07_story_final.md", context="story_final"
        )

    # 07b continuity pass (Phase 4). May retry the editor once, which
    # overwrites 07_story_final.md and mutates the slop ledger in turn.
    if _should_run("07b", start_from):
        _print_rule(f"Year {year} — continuity pass (auditing final chapter)")
        final, report, verdict, degraded = await _run_continuity_with_retry(
            client,
            run_dir=run_dir,
            year_dir=year_dir,
            year=year,
            final=final,
            chapter_outline=chapter_outline,
            beat_sheet=beat_sheet,
            cast_plan=cast_plan,
            dossiers=dossiers,
            previous_hooks_typed=previous_hooks_typed,
            prev_chapter_text=prev_chapter_text,
            prev_year=prev_year,
            active_slop=active_slop,
            slop_ledger=slop_ledger,
            style_guide=style_guide,
            decade_spine=decade_spine,
            year_dilemma=summary.get("year_dilemma"),
            rupture=rupture_doc,
            setting_ledger=setting_ledger,
            debt_ledger=debt_ledger,
            chosen_fork=chosen_fork,
        )
    else:
        report = _load_json_strict(
            year_dir / "07b_continuity_report.json", context="continuity_report"
        )
        verdict = report.get("verdict", "pass")
        degraded = bool(report.get("degraded"))

    continuity_verdict = "degraded" if degraded else verdict
    hooks_this_year = list(beat_sheet.get("hooks_to_plant") or [])
    cast_ids_this_year = [e["id"] for e in cast_plan.get("main_cast", [])]
    off_page_used = beat_sheet.get("off_page_event") is not None

    if _stage_index(start_from) <= _stage_index("07b"):
        _upsert_setting_ledger(
            run_dir, year=year, outline=chapter_outline,
            beat_sheet=beat_sheet, continuity_report=report,
        )
        _upsert_debt_ledger(
            run_dir, year=year, beat_sheet=beat_sheet,
            continuity_report=report,
        )
        _upsert_rupture_log(
            run_dir, year=year, rupture_doc=rupture_doc,
            continuity_report=report,
        )
        setting_ledger = _load_setting_ledger(run_dir)
        debt_ledger = _load_debt_ledger(run_dir)
        rupture_log = _load_rupture_log(run_dir)

    # v4: derive change_audit entries the chapter_index will persist so
    # next year's cast planner can compute unchanged streaks. The
    # report's change_audit shape is
    # {cid: {"verdict": "changed"|"unchanged", "axis": ..., "evidence": ...}}.
    change_audit_raw = (report or {}).get("change_audit") or {}
    change_audit_persist: dict[str, dict] = {}
    for cid in cast_ids_this_year:
        entry = change_audit_raw.get(cid) or {}
        verdict_v = entry.get("verdict")
        change_audit_persist[cid] = {
            "changed": verdict_v == "changed",
            "verdict": verdict_v or "unchanged",
            "axis": entry.get("axis", "") or "",
            "evidence": entry.get("evidence", "") or "",
        }
    irr_observed_persist = (
        (report or {}).get("irreversibility") or {}
    ).get("events_observed") or []

    # Chapter-index append: rewrite whenever any of this entry's inputs
    # were re-run — that's cast_plan (06a), beat_sheet (06c), outline
    # (06d), or continuity_verdict (07b). Equivalent to
    # start_from <= 07b in STAGE_ORDER. Idempotent on `year` (replaces
    # any existing entry), so replays update the record rather than
    # duplicating it.
    if _stage_index(start_from) <= _stage_index("07b"):
        _append_chapter_index(
            chapter_index,
            year=year,
            outline=chapter_outline,
            chosen_fork_domain=chosen_fork.get("domain"),
            off_page_used=off_page_used,
            hooks_planted=hooks_this_year,
            cast_ids=cast_ids_this_year,
            continuity_verdict=continuity_verdict,
            change_audit=change_audit_persist,
            irreversible_events_observed=list(irr_observed_persist),
            year_dilemma=summary.get("year_dilemma"),
        )
        _save_chapter_index(run_dir, chapter_index)

    # Cast ledger + per-character arc files: only when dossiers were
    # re-run (that's what arcs record). `_update_cast_after_epoch` is
    # idempotent on `year`; `_append_char_arc` is not, so a replay from
    # 06b-or-earlier may write a second dated section to each arc file
    # (cosmetic; arc readers are humans, the pipeline does not parse
    # arcs). A full-year re-seed should delete the year_<YYYY>/ folder
    # AND revert cast.json / arc files before running.
    if _should_run("06b", start_from):
        _update_cast_after_epoch(cast, cast_plan, dossiers, year)
        for cid, dossier in dossiers.items():
            character = _get_character(cast, cid)
            header = None
            if character and not _char_arc_path(run_dir, cid).exists():
                header = _char_header(character)
            body_parts = []
            body_parts.append(f"**Want:** {dossier.get('want','')}")
            body_parts.append(f"**Obstacle:** {dossier.get('obstacle','')}")
            if dossier.get("contradiction"):
                body_parts.append(f"**Contradiction:** {dossier['contradiction']}")
            beats = dossier.get("this_year_beats") or []
            if beats:
                body_parts.append("**Beats:**")
                body_parts.extend(f"- {b}" for b in beats)
            lines = dossier.get("quotable_lines") or []
            if lines:
                body_parts.append("**Lines:**")
                body_parts.extend(f"- “{q}”" for q in lines)
            if dossier.get("memorable_image"):
                body_parts.append(f"**Image:** {dossier['memorable_image']}")
            if dossier.get("unresolved_at_year_end"):
                body_parts.append(f"**Unresolved:** {dossier['unresolved_at_year_end']}")
            _append_char_arc(run_dir, cid, year, "\n".join(body_parts), header=header)
        _save_cast(run_dir, cast)

    # 08 fork proposer (drastic, cross-domain; Phase 4 anti-lock-in)
    if _should_run("08", start_from):
        recent_fork_domains = _recent_fork_domains(chapter_index)
        _print_rule(
            f"Year {year} — proposing 3 drastic forks from 3 distinct domains "
            f"(avoid-lock-in: at least 1 outside {recent_fork_domains or '[]'})"
        )
        forks = await run_fork_proposer(
            client, year=year, summary=summary, crossinterference=crossinterference,
            state=new_state, story=final,
            recent_fork_domains=recent_fork_domains,
            decade_spine=decade_spine,
            debt_ledger=debt_ledger,
            setting_ledger=setting_ledger,
        )
        _write_json(year_dir / "08_forks.json", {"forks": forks})
        for i, f in enumerate(forks, 1):
            print(f"\n  [{i}] ({f['domain']}, {f['drasticness']}, "
                  f"{f.get('fork_type','?')}) {f['title']}")
            print(f"      actor: {f.get('actor','')} | "
                  f"act: {f.get('irreversible_act','')}")
            print(f"      stake: {f.get('named_stake','')} | "
                  f"clock: {f.get('clock','')}")
            spine_impact = f.get("spine_wager_impact")
            if spine_impact:
                sa = f.get("spine_advances") or {}
                sa_str = (
                    f"act {sa.get('act')}: {sa.get('how')}"
                    if isinstance(sa, dict) else str(sa)
                )
                print(f"      spine: {spine_impact} (advances {sa_str})")
            print(f"      {f['flavor']}")
    else:
        forks_doc = _load_json_strict(
            year_dir / "08_forks.json", context="forks"
        )
        forks = forks_doc.get("forks", [])

    # 09 readability metrics (Phase 5, pure code — cheap to always
    # recompute; we do so whenever this stage is in scope, which is
    # every start_from that includes stage 09 — i.e., always).
    if _should_run("09", start_from):
        _print_rule(f"Year {year} — readability metrics (09_readability.json)")
        readability = compute_readability(
            year=year,
            cast_plan=cast_plan,
            chapter_outline=chapter_outline,
            beat_sheet=beat_sheet,
            specialist_docs=specialist_docs,
            crossinterference=crossinterference,
            continuity_report=report,
            final_prose=final,
            active_slop=active_slop,
            continuity_verdict=continuity_verdict,
            degraded=degraded,
            rupture=rupture_doc,
        )
        _write_json(year_dir / "09_readability.json", readability)
        palette_str = (
            f"{readability['palette'].get('base')}/"
            f"{readability['palette'].get('modulator')}/"
            f"{readability['palette'].get('device')}"
        )
        in_sc = readability.get("in_scene_ratio")
        in_sc_str = f"{in_sc:.2f}" if isinstance(in_sc, (int, float)) else "n/a"
        coll_str = str(readability.get("collision_satisfied"))
        print(
            f"  people={readability['named_people_count']} "
            f"(return={readability['returning_characters']}, "
            f"new={readability['new_characters']}, "
            f"retired={readability['retired_characters']}) | "
            f"scenes={readability['scenes_count']} | "
            f"places={readability['unique_places']} | "
            f"regions={readability['regions_covered']} | "
            f"facets={readability['facets_covered']} | "
            f"mode={readability.get('mode_used') or readability.get('structure_used')} | "
            f"palette={palette_str} | "
            f"hooks_resolved={len(readability['hooks_resolved'])} | "
            f"hooks_planted={len(readability['hooks_planted'])} "
            f"(seeds={readability.get('dramatic_seeds_planted', 0)}) | "
            f"changed_mains={readability.get('changed_mains', 0)} | "
            f"irreversible={readability.get('irreversible_events_observed', 0)}/"
            f"{readability.get('irreversible_events_declared', 0)} | "
            f"collision={coll_str} | "
            f"in_scene={in_sc_str} | "
            f"slop_flagged={len(readability['slop_tics_flagged'])} | "
            f"verdict={readability['continuity_verdict']}"
        )

    return {
        "year": year,
        "state": new_state,
        "summary": summary,
        "crossinterference": crossinterference,
        "story": final,
        "forks": forks,
    }


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #

def _prompt_fork_choice(forks: list[dict]) -> int | None:
    while True:
        raw = input("\nPick a fork [1/2/3] or q to quit: ").strip().lower()
        if raw in ("q", "quit", "exit"):
            return None
        if raw in ("1", "2", "3"):
            return int(raw) - 1
        print("  Please enter 1, 2, 3, or q.")


async def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        env_path = HERE / ".env"
        print("ERROR: OPENAI_API_KEY is empty.")
        print(f"Open {env_path} and paste your key after 'OPENAI_API_KEY='.")
        sys.exit(1)

    client = AsyncOpenAI()

    seed_state = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    style_guide = STYLE_ASIMOV_PATH.read_text(encoding="utf-8")

    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / f"year_{seed_state['year']}_seed.json", seed_state)

    _print_rule("Future Weavers v5 — variance + long arcs + rupture")
    print(f"Run folder: {run_dir}")
    print(f"Seed year:  {seed_state['year']}")

    # Baseline summary of the seed so year +1 has a "previous summary" to compare.
    _print_rule(f"Baseline summary of seed year {seed_state['year']}")
    baseline_summary = await run_baseline_summarizer(client, seed_state=seed_state)
    _write_json(run_dir / f"year_{seed_state['year']}_summary.json", baseline_summary)
    print(f"  headline: {baseline_summary.get('headline_of_the_year', '(none)')}")
    print(f"  mood:     {baseline_summary.get('year_mood','?')}  "
          f"tension: {baseline_summary.get('central_tension','')}")

    # Phase 3: seed the slop ledger with known AI tics + v2's recurring
    # refrains. Cooldowns are measured in generated years; the baseline
    # year is the origin. Idempotent — re-seeds only if the file is absent
    # or empty.
    _seed_slop_ledger(run_dir, seed_state["year"])
    _save_setting_ledger(run_dir, _load_setting_ledger(run_dir))
    _save_debt_ledger(run_dir, _load_debt_ledger(run_dir))
    _save_rupture_log(run_dir, _load_rupture_log(run_dir))

    # Cast bootstrap — seed 3 founding characters from the seed state so year +1
    # has a cast plan to call on. Writes cast.json and the three per-character
    # arc files under runs/<run_id>/characters/.
    _print_rule(f"Cast bootstrap — founding 3 characters from seed year {seed_state['year']}")
    bootstrap = await run_cast_bootstrap(
        client, seed_state=seed_state, baseline_summary=baseline_summary,
    )
    _write_json(run_dir / f"year_{seed_state['year']}_cast_bootstrap.json", bootstrap)
    cast = {"characters": [], "last_updated_year": seed_state["year"]}
    for c in bootstrap["characters"]:
        cast["characters"].append(_character_to_cast_entry(c, seed_state["year"]))
        _append_char_arc(
            run_dir, c["id"], seed_state["year"],
            body=(
                f"**Initial want:** {c.get('initial_want','')}\n"
                f"**Initial obstacle:** {c.get('initial_obstacle','')}\n"
                f"**Positioned at:** {c.get('positioned_at','')}"
            ),
            header=_char_header(c),
        )
        print(f"  + {c['name']:<30} {c['role']}")
    _save_cast(run_dir, cast)

    # v4 Stage 0: commit to a decade spine. One-time artefact read by
    # every per-year stage (summariser, cast plan, beat sheet, outline,
    # narrator, continuity, forks). Without it, later stages would fall
    # back to a neutral string, but the story loses its backbone.
    _print_rule(f"Decade spine — committing to the 10-year dramatic question")
    decade_spine = await run_decade_spine(
        client,
        seed_state=seed_state,
        baseline_summary=baseline_summary,
        bootstrap=bootstrap,
    )
    _save_decade_spine(run_dir, decade_spine)
    print(f"  question:  {decade_spine.get('question','')}")
    print(f"  wager:     {decade_spine.get('wager','')}")
    print(f"  countdown: {decade_spine.get('countdown','')}")
    for act in decade_spine.get("acts", []):
        print(f"    act {act.get('act')}: {act.get('name','')} "
              f"({act.get('year_range','')}) — {act.get('promise','')}")

    # Initial forks for year +1: use the fork proposer with dummy crossinterference
    # (seeds have no cross-interference yet; we pass the baseline summary twice so
    # the prompt has context, plus an empty interference set).
    _print_rule(f"Initial forks for year {seed_state['year'] + 1}")
    forks = await run_fork_proposer(
        client,
        year=seed_state["year"],
        summary=baseline_summary,
        crossinterference={"cross_domain_interactions": [], "emergent_themes": [],
                           "contradictions_to_flag": []},
        state=seed_state,
        story="(none — the tree has not yet branched; propose forks directly from the seed state)",
        decade_spine=decade_spine,
    )
    _write_json(run_dir / f"year_{seed_state['year'] + 1}_initial_forks.json", {"forks": forks})
    for i, f in enumerate(forks, 1):
        print(f"\n  [{i}] ({f['domain']}, {f['drasticness']}, "
              f"{f.get('fork_type','?')}) {f['title']}")
        print(f"      actor: {f.get('actor','')} | "
              f"act: {f.get('irreversible_act','')}")
        print(f"      stake: {f.get('named_stake','')} | "
              f"clock: {f.get('clock','')}")
        spine_impact = f.get("spine_wager_impact")
        if spine_impact:
            sa = f.get("spine_advances") or {}
            sa_str = (
                f"act {sa.get('act')}: {sa.get('how')}"
                if isinstance(sa, dict) else str(sa)
            )
            print(f"      spine: {spine_impact} (advances {sa_str})")
        print(f"      {f['flavor']}")

    parent_state = seed_state
    previous_summary = baseline_summary
    prev_chapter_text = ""
    prev_year: int | None = None

    while True:
        idx = _prompt_fork_choice(forks)
        if idx is None:
            print(f"\nBye. Transcripts are in: {run_dir}")
            return

        chosen = forks[idx]
        year = parent_state["year"] + 1
        year_dir = run_dir / f"year_{year}"

        epoch = await generate_epoch(
            client,
            run_dir=run_dir,
            year_dir=year_dir,
            parent_state=parent_state,
            chosen_fork=chosen,
            previous_summary=previous_summary,
            prev_chapter_text=prev_chapter_text,
            prev_year=prev_year,
            style_guide=style_guide,
        )

        _print_rule(f"YEAR {epoch['year']} — FINAL STORY")
        print(epoch["story"])
        print(f"\n[saved {year_dir}]")

        parent_state = epoch["state"]
        previous_summary = epoch["summary"]
        prev_chapter_text = epoch["story"]
        prev_year = epoch["year"]
        forks = epoch["forks"]


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
