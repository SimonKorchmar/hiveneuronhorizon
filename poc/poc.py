"""Future Weavers — v2 storytelling pipeline (Phase 0 PoC).

Pipeline per year (see ../concepts/v2_storytelling_pipeline.md):

    chosen_fork
        -> 5 specialists in parallel          (cheap tier, rich JSON each)
        -> state merger
        -> summarizer                         (mid tier, balanced JSON)
        -> cross-interference analyst         (mid tier, JSON)
        -> storyteller                        (mid tier, Asimov prose)
        -> editor                             (premium tier, Asimov polish)
        -> fork proposer                      (mid tier, 3 drastic forks
                                               from 3 distinct domains)

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
    "specialist":   ["gpt-5.4-nano", "gpt-4o-mini"],
    "orchestrator": ["gpt-5.4-mini", "gpt-4o"],
    "storyteller":  ["gpt-5.4-mini", "gpt-4o"],
    "editor":       ["gpt-5.4",      "gpt-4o"],
}

VALID_DOMAINS = ("ecology", "economy", "geopolitics", "society", "culture")
CAST_MAX = 6                # hard ceiling on main_cast per epoch
FRESHNESS_WINDOW = 2        # epochs — prefer introducing a new character if none in last N
DORMANT_AFTER = 3           # epochs without appearing -> status "dormant"

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
) -> dict:
    user = prompts.SUMMARIZER_USER_TEMPLATE.format(
        year=year,
        ecology_doc=_pretty_json(specialist_docs["ecology"]),
        economy_doc=_pretty_json(specialist_docs["economy"]),
        geopolitics_doc=_pretty_json(specialist_docs["geopolitics"]),
        society_doc=_pretty_json(specialist_docs["society"]),
        culture_doc=_pretty_json(specialist_docs["culture"]),
        state_json=_pretty_json(state),
    )
    raw = await _chat(
        client, "orchestrator",
        [{"role": "system", "content": prompts.SUMMARIZER_SYSTEM},
         {"role": "user",   "content": user}],
        json_mode=True,
    )
    return _parse_json(raw, where="summarizer")


async def run_baseline_summarizer(
    client: AsyncOpenAI, *, seed_state: dict
) -> dict:
    user = prompts.BASELINE_SUMMARIZER_USER_TEMPLATE.format(
        seed_json=_pretty_json(seed_state),
        year=seed_state["year"],
    )
    raw = await _chat(
        client, "orchestrator",
        [{"role": "system", "content": prompts.BASELINE_SUMMARIZER_SYSTEM},
         {"role": "user",   "content": user}],
        json_mode=True,
    )
    return _parse_json(raw, where="baseline_summarizer")


# --------------------------------------------------------------------------- #
# Stage 4: Cross-Interference
# --------------------------------------------------------------------------- #

async def run_cross_interference(
    client: AsyncOpenAI,
    *,
    year: int,
    summary: dict,
    specialist_docs: dict[str, dict],
) -> dict:
    user = prompts.CROSS_INTERFERENCE_USER_TEMPLATE.format(
        year=year,
        summary_json=_pretty_json(summary),
        ecology_doc=_pretty_json(specialist_docs["ecology"]),
        economy_doc=_pretty_json(specialist_docs["economy"]),
        geopolitics_doc=_pretty_json(specialist_docs["geopolitics"]),
        society_doc=_pretty_json(specialist_docs["society"]),
        culture_doc=_pretty_json(specialist_docs["culture"]),
    )
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
            f"cross_interference produced only {len(interactions)} interactions (need >=3): {data}"
        )
    return data


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
) -> dict:
    active = _active_cast(cast)
    recent = _recent_introductions(cast, year)
    valid_interaction_ids = [
        i["id"] for i in crossinterference.get("cross_domain_interactions", [])
    ]
    if not valid_interaction_ids:
        raise RuntimeError("cast_plan: cross-interference has no interactions to position at")

    user = prompts.CAST_PLAN_USER_TEMPLATE.format(
        year=year,
        active_cast_json=_pretty_json(active),
        recent_introductions=", ".join(recent) if recent else "(none)",
        summary_json=_pretty_json(summary),
        crossinterference_json=_pretty_json(crossinterference),
        prev_chapter_text=prev_chapter_text or "(no previous chapter yet)",
        prev_year=prev_year if prev_year is not None else "n/a",
    )
    raw = await _chat(
        client, "orchestrator",
        [{"role": "system", "content": prompts.CAST_PLAN_SYSTEM},
         {"role": "user",   "content": user}],
        json_mode=True,
    )
    data = _parse_json(raw, where="cast_plan")
    cast_plan = data.get("main_cast", [])
    problem = _validate_cast_plan(cast_plan, active, valid_interaction_ids)
    if problem:
        raise RuntimeError(f"cast_plan invalid: {problem}\n{_pretty_json(data)}")
    return data


def _validate_cast_plan(main_cast: list[dict], active: list[dict],
                         valid_interaction_ids: list[str]) -> str | None:
    if not isinstance(main_cast, list) or not (3 <= len(main_cast) <= CAST_MAX):
        return f"main_cast must have 3..{CAST_MAX} entries, got {len(main_cast) if isinstance(main_cast, list) else type(main_cast).__name__}"
    active_ids = {c["id"] for c in active}
    seen_ids: set[str] = set()
    has_returning = False
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
) -> dict:
    user = prompts.BEAT_SHEET_USER_TEMPLATE.format(
        year=year,
        dossiers_json=_pretty_json(list(dossiers.values())),
        summary_json=_pretty_json(summary),
        crossinterference_json=_pretty_json(crossinterference),
        prev_chapter_text=prev_chapter_text or "(no previous chapter yet)",
        prev_year=prev_year if prev_year is not None else "n/a",
    )
    raw = await _chat(
        client, "orchestrator",
        [{"role": "system", "content": prompts.BEAT_SHEET_SYSTEM},
         {"role": "user",   "content": user}],
        json_mode=True,
    )
    data = _parse_json(raw, where="beat_sheet")
    problem = _validate_beat_sheet(data, dossiers, crossinterference)
    if problem:
        raise RuntimeError(f"beat_sheet invalid: {problem}\n{_pretty_json(data)}")
    return data


def _validate_beat_sheet(data: dict, dossiers: dict[str, dict],
                          crossinterference: dict) -> str | None:
    for k in ("central_tension", "hooks_to_resolve", "hooks_to_plant",
              "ordered_beats", "side_characters"):
        if k not in data:
            return f"missing key '{k}'"
    beats = data["ordered_beats"]
    if not isinstance(beats, list) or not (5 <= len(beats) <= 9):
        return f"ordered_beats must have 5..9 entries, got {len(beats) if isinstance(beats, list) else type(beats).__name__}"

    cast_ids = set(dossiers.keys())
    appearing: set[str] = set()
    valid_interaction_ids = {i["id"] for i in crossinterference.get("cross_domain_interactions", [])}
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
        appearing.update(b.get("present_characters", []) or [])

    missing = cast_ids - appearing
    if missing:
        return f"cast members never appear in any beat's present_characters: {sorted(missing)}"

    # off_page_event is optional; if present, must have required shape
    ope = data.get("off_page_event")
    if ope is not None:
        for k in ("what", "when", "how_referenced"):
            if k not in ope:
                return f"off_page_event present but missing '{k}'"

    return None


# --------------------------------------------------------------------------- #
# Stage 6: Storyteller (Asimov-inspired, consumes dossiers + beat sheet)
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
    prev_chapter_text: str,
    prev_year: int | None,
    style_guide: str,
) -> str:
    user = prompts.STORYTELLER_USER_TEMPLATE.format(
        style_guide=style_guide,
        year=year,
        previous_summary_json=_pretty_json(previous_summary) if previous_summary else "null",
        current_summary_json=_pretty_json(current_summary),
        crossinterference_json=_pretty_json(crossinterference),
        narrative_threads_json=_pretty_json(narrative_threads),
        dossiers_json=_pretty_json(list(dossiers.values())),
        beat_sheet_json=_pretty_json(beat_sheet),
        prev_chapter_text=prev_chapter_text or "(no previous chapter yet)",
        prev_year=prev_year if prev_year is not None else "n/a",
    )
    return await _chat(
        client, "storyteller",
        [{"role": "system", "content": prompts.STORYTELLER_SYSTEM},
         {"role": "user",   "content": user}],
        stream=True,
    )


# --------------------------------------------------------------------------- #
# Stage 7: Editor (Asimov-inspired polish)
# --------------------------------------------------------------------------- #

async def run_editor(
    client: AsyncOpenAI, *, draft_prose: str, style_guide: str
) -> str:
    user = prompts.EDITOR_USER_TEMPLATE.format(
        style_guide=style_guide, draft_prose=draft_prose
    )
    return await _chat(
        client, "editor",
        [{"role": "system", "content": prompts.EDITOR_SYSTEM},
         {"role": "user",   "content": user}],
        stream=True,
    )


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
    retries: int = 2,
) -> list[dict]:
    user = prompts.FORK_PROPOSER_USER_TEMPLATE.format(
        year=year,
        next_year=year + 1,
        summary_json=_pretty_json(summary),
        crossinterference_json=_pretty_json(crossinterference),
        state_json=_pretty_json(state),
        story=story,
    )

    for attempt in range(retries + 1):
        raw = await _chat(
            client, "orchestrator",
            [{"role": "system", "content": prompts.FORK_PROPOSER_SYSTEM},
             {"role": "user",   "content": user}],
            json_mode=True,
        )
        data = _parse_json(raw, where="fork_proposer")
        forks = data.get("forks", [])
        problem = _validate_forks(forks)
        if not problem:
            return forks
        print(f"  [fork_proposer attempt {attempt + 1}: {problem}; retrying]")
        user += f"\n\nPREVIOUS ATTEMPT REJECTED BECAUSE: {problem}\nFix it."

    raise RuntimeError(f"fork_proposer failed after {retries + 1} attempts: last forks={forks}")


def _validate_forks(forks: list[dict]) -> str | None:
    if not isinstance(forks, list) or len(forks) != 3:
        return f"expected exactly 3 forks, got {len(forks) if isinstance(forks, list) else type(forks).__name__}"
    domains = []
    for i, f in enumerate(forks):
        for k in ("domain", "title", "drasticness", "flavor"):
            if k not in f:
                return f"fork[{i}] missing key '{k}'"
        if f["domain"] not in VALID_DOMAINS:
            return f"fork[{i}] invalid domain '{f['domain']}' (must be one of {VALID_DOMAINS})"
        if f["drasticness"] not in ("moderate", "high", "extreme"):
            return f"fork[{i}] invalid drasticness '{f['drasticness']}'"
        domains.append(f["domain"])
    if len(set(domains)) != 3:
        return f"forks share domains: {domains} (must be 3 distinct domains)"
    return None


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
) -> dict:
    year = parent_state["year"] + 1
    year_dir.mkdir(parents=True, exist_ok=True)

    # 01 save the chosen fork
    _write_json(year_dir / "01_fork.json", chosen_fork)

    # 02 specialists in parallel
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

    # 03 state merger
    new_state = copy.deepcopy(parent_state)
    new_state["year"] = year
    for doc in specialist_docs.values():
        new_state = _merge_specialist_updates(new_state, doc.get("state_updates", {}))
    _write_json(year_dir / "03_state.json", new_state)

    # 04 summarizer
    _print_rule(f"Year {year} — summarizer (balanced, all 5 facets)")
    summary = await run_summarizer(
        client, year=year, specialist_docs=specialist_docs, state=new_state,
    )
    _write_json(year_dir / "04_summary.json", summary)
    print(f"  headline: {summary.get('headline_of_the_year', '(none)')}")

    # 05 cross-interference
    _print_rule(f"Year {year} — cross-interference analyst")
    crossinterference = await run_cross_interference(
        client, year=year, summary=summary, specialist_docs=specialist_docs,
    )
    _write_json(year_dir / "05_crossinterference.json", crossinterference)
    for inter in crossinterference.get("cross_domain_interactions", []):
        print(f"  * [{'+'.join(inter.get('domains_involved', []))}] {inter.get('title', '')}")

    # 06a cast plan (Character Plot Mastermind — who appears this epoch)
    _print_rule(f"Year {year} — cast plan (3-{CAST_MAX} main characters)")
    cast = _load_cast(run_dir)
    cast_plan = await run_cast_plan(
        client,
        year=year,
        cast=cast,
        summary=summary,
        crossinterference=crossinterference,
        prev_chapter_text=prev_chapter_text,
        prev_year=prev_year,
    )
    _write_json(year_dir / "06a_cast_plan.json", cast_plan)
    for entry in cast_plan["main_cast"]:
        name = entry.get("name") or (
            _get_character(cast, entry["id"]) or {}
        ).get("name", entry["id"])
        print(f"  - [{entry['status']:<11}] {name} — {entry.get('brief','')[:100]}")

    # 06b dossiers (character subagents, parallel, cheap tier)
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

    # 06c beat sheet (Character Plot Mastermind — structured scaffolding)
    _print_rule(f"Year {year} — beat sheet (mastermind scaffolding)")
    beat_sheet = await run_beat_sheet(
        client,
        year=year,
        dossiers=dossiers,
        summary=summary,
        crossinterference=crossinterference,
        prev_chapter_text=prev_chapter_text,
        prev_year=prev_year,
    )
    _write_json(year_dir / "06c_beat_sheet.json", beat_sheet)
    print(f"  central_tension: {beat_sheet.get('central_tension','')}")
    print(f"  beats: {len(beat_sheet.get('ordered_beats', []))} "
          f"| hooks_to_plant: {len(beat_sheet.get('hooks_to_plant', []))} "
          f"| off-page: {'yes' if beat_sheet.get('off_page_event') else 'no'}")

    # 06 storyteller (Asimov-inspired, streaming, consumes dossiers + beat sheet)
    _print_rule(f"Year {year} — storyteller (weaving world + character beats)")
    draft = await run_storyteller(
        client,
        year=year,
        previous_summary=previous_summary,
        current_summary=summary,
        crossinterference=crossinterference,
        narrative_threads=new_state.get("narrative_threads", []),
        dossiers=dossiers,
        beat_sheet=beat_sheet,
        prev_chapter_text=prev_chapter_text,
        prev_year=prev_year,
        style_guide=style_guide,
    )
    _write_text(year_dir / "06_story_draft.md", draft)

    # 07 editor polish
    _print_rule(f"Year {year} — editor polishing")
    final = await run_editor(client, draft_prose=draft, style_guide=style_guide)
    _write_text(year_dir / "07_story_final.md", final)

    # Update persistent ledgers: cast.json + per-character arc files.
    _update_cast_after_epoch(cast, cast_plan, dossiers, year)
    for cid, dossier in dossiers.items():
        character = _get_character(cast, cid)
        # For newly-introduced characters, create the arc file with a header.
        header = None
        if character and not _char_arc_path(run_dir, cid).exists():
            header = _char_header(character)
        # Body: a compact markdown block summarising the year from the dossier.
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

    # 08 fork proposer (drastic, cross-domain)
    _print_rule(f"Year {year} — proposing 3 drastic forks from 3 distinct domains")
    forks = await run_fork_proposer(
        client, year=year, summary=summary, crossinterference=crossinterference,
        state=new_state, story=final,
    )
    _write_json(year_dir / "08_forks.json", {"forks": forks})
    for i, f in enumerate(forks, 1):
        print(f"\n  [{i}] ({f['domain']}, {f['drasticness']}) {f['title']}")
        print(f"      rooted_in: {f.get('rooted_in', '')}")
        print(f"      {f['flavor']}")

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

    _print_rule("Future Weavers v2 — storytelling pipeline")
    print(f"Run folder: {run_dir}")
    print(f"Seed year:  {seed_state['year']}")

    # Baseline summary of the seed so year +1 has a "previous summary" to compare.
    _print_rule(f"Baseline summary of seed year {seed_state['year']}")
    baseline_summary = await run_baseline_summarizer(client, seed_state=seed_state)
    _write_json(run_dir / f"year_{seed_state['year']}_summary.json", baseline_summary)
    print(f"  headline: {baseline_summary.get('headline_of_the_year', '(none)')}")

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
    )
    _write_json(run_dir / f"year_{seed_state['year'] + 1}_initial_forks.json", {"forks": forks})
    for i, f in enumerate(forks, 1):
        print(f"\n  [{i}] ({f['domain']}, {f['drasticness']}) {f['title']}")
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
