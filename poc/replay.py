"""Future Weavers — stage-scoped replay for an existing run (Phase 5).

Why this exists
---------------
Iterating on prompts on the full pipeline is expensive: every tweak
re-runs five specialists, a summariser, cross-interference, cast plan,
dossiers, beat sheet, outline, narrator, editor, continuity pass, and
fork proposer. That's $0.30–$0.45 and several minutes per iteration,
most of it regenerating stages the tweak didn't touch.

`replay.py` re-runs only the stages you care about on an existing run,
loading earlier artefacts from disk. A tweak to the editor prompt is
re-testable at ~$0.22 and tens of seconds with `--from-stage 07`.
Because upstream artefacts are fixed, the only variable is the change
you're debugging — apples-to-apples comparison.

See the plan (`../concepts/plan.md` §10 Phase 5) for the spec.

Usage
-----
    python replay.py <run_id> --from-stage <stage> [--year <YYYY>]

Examples:

    # Rewrite the editor + re-audit + re-propose forks + refresh readability
    python replay.py 20260419-192449 --from-stage 07

    # Re-run rupture + narrator + downstream, keeping the outline fixed
    python replay.py 20260419-192449 --from-stage 06e

    # Re-audit only (keep the existing editor output); read new continuity
    # report + refreshed readability. Skips the editor LLM call entirely.
    python replay.py 20260419-192449 --from-stage 07b

    # Recompute readability only (pure code, ~instant, no LLM call at all)
    python replay.py 20260419-192449 --from-stage 09

    # Replay year 2028 specifically (default is the latest year folder)
    python replay.py 20260419-192449 --year 2028 --from-stage 06d

Stage ids (in order):

    02  specialists (+ 03 state merger — a pure code op)
    04  summariser
    05  cross-interference
    06a cast plan
    06b character dossiers
    06c beat sheet
    06d chapter outline (narrator pass 1)
    06e rupture authorisation
    06f narrator execute (writes 06f_story_draft.md)
    07  editor (writes 07_story_final.md)
    07b continuity pass
    08  fork proposer
    09  readability metrics (pure code)

Scope notes
-----------
- Replaying an OLDER year than the latest is permitted but will make
  the run's state inconsistent (subsequent years were built on the
  old artefacts). A warning is printed; the user should either
  replay forward from that year or accept the inconsistency for a
  one-off experiment. This tool does not cascade re-runs.
- cast.json / per-character arc files are updated idempotently on
  year (cast bumps are keyed by year; arc files accept duplicate
  dated sections — cosmetic only).
- The chapter_index.json entry for the target year is removed before
  the replay and re-written by the pipeline, so freshness filters on
  structure / palette see the prior N-1 years (not a stale copy of
  the year being replayed).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Importing poc.py runs its module-level dotenv load too, but keep the
# explicit call here for clarity when replay.py is invoked standalone.
load_dotenv(Path(__file__).parent / ".env")

import poc  # noqa: E402  — intentional: load env before import


YEAR_FOLDER_RE = re.compile(r"^year_(\d{4})$")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="replay.py",
        description=(
            "Re-run a slice of the Future Weavers pipeline on an existing "
            "run. Loads all stages earlier than --from-stage from disk, "
            "recomputes from --from-stage onward. Essential for iterating "
            "on prompts (plan §10 Phase 5)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "run_id",
        help=(
            "Timestamped run folder under poc/runs/ (e.g. '20260419-192449')."
        ),
    )
    parser.add_argument(
        "--from-stage",
        required=True,
        metavar="STAGE",
        choices=list(poc.STAGE_ORDER),
        help=(
            "First stage to recompute. One of: "
            + " | ".join(poc.STAGE_ORDER)
            + ". See module docstring for what each stage writes."
        ),
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help=(
            "Target year to replay. Defaults to the latest year_YYYY/ "
            "folder under the run."
        ),
    )
    return parser.parse_args()


def _latest_year_dir(run_dir: Path) -> Path:
    """Return the highest-numbered year_YYYY/ subfolder, or raise."""
    years: list[tuple[int, Path]] = []
    for child in run_dir.iterdir():
        if not child.is_dir():
            continue
        m = YEAR_FOLDER_RE.match(child.name)
        if not m:
            continue
        years.append((int(m.group(1)), child))
    if not years:
        raise SystemExit(
            f"no year_YYYY/ folders under {run_dir} — is this a valid run?"
        )
    years.sort()
    return years[-1][1]


def _all_year_dirs(run_dir: Path) -> list[tuple[int, Path]]:
    years: list[tuple[int, Path]] = []
    for child in run_dir.iterdir():
        if not child.is_dir():
            continue
        m = YEAR_FOLDER_RE.match(child.name)
        if m:
            years.append((int(m.group(1)), child))
    years.sort()
    return years


def _load_previous_context(
    run_dir: Path, target_year: int, seed_state: dict,
) -> tuple[dict, dict | None, str, int | None]:
    """Return (parent_state, previous_summary, prev_chapter_text, prev_year)
    for the year just before `target_year`.

    Two cases:
      - target_year == seed_year + 1: parent_state = seed, previous_summary
        = baseline summary written at the run root, no prior chapter.
      - otherwise: parent_state / previous_summary come from the prior
        year's folder; prev_chapter_text from its 07_story_final.md.
    """
    seed_year = seed_state["year"]
    if target_year == seed_year + 1:
        baseline_path = run_dir / f"year_{seed_year}_summary.json"
        baseline = poc._load_json_strict(  # noqa: SLF001 — internal helper
            baseline_path, context="baseline_summary"
        )
        return seed_state, baseline, "", None

    prev_year = target_year - 1
    prev_dir = run_dir / f"year_{prev_year}"
    if not prev_dir.exists():
        raise SystemExit(
            f"previous year folder {prev_dir} is missing; cannot reconstruct "
            f"replay context for year {target_year}"
        )
    parent_state = poc._load_json_strict(  # noqa: SLF001
        prev_dir / "03_state.json", context=f"state[{prev_year}]"
    )
    previous_summary = poc._load_json_strict(  # noqa: SLF001
        prev_dir / "04_summary.json", context=f"summary[{prev_year}]"
    )
    final_path = prev_dir / "07_story_final.md"
    prev_chapter_text = (
        final_path.read_text(encoding="utf-8") if final_path.exists() else ""
    )
    return parent_state, previous_summary, prev_chapter_text, prev_year


def _strip_current_year_from_chapter_index(
    run_dir: Path, target_year: int,
) -> None:
    """Remove the current year's entry from chapter_index.json so
    freshness filters in the replay see only the years BEFORE this
    one. The pipeline re-writes this entry after the (possibly
    re-run) continuity pass. Idempotent on empty / missing index.
    """
    index = poc._load_chapter_index(run_dir)  # noqa: SLF001
    chapters = index.get("chapters", []) or []
    kept = [c for c in chapters if c.get("year") != target_year]
    if len(kept) != len(chapters):
        index["chapters"] = kept
        poc._save_chapter_index(run_dir, index)  # noqa: SLF001


async def _replay(args: argparse.Namespace) -> None:
    run_dir = poc.RUNS_DIR / args.run_id
    if not run_dir.is_dir():
        raise SystemExit(f"run folder not found: {run_dir}")

    # Only stage 09 (readability) is pure code; every other stage hits
    # the OpenAI API, so require a key everywhere else.
    if args.from_stage != "09" and not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is empty.")
        print(f"Open {poc.HERE / '.env'} and paste your key after 'OPENAI_API_KEY='.")
        sys.exit(1)

    # Pick the target year. Default: latest year_YYYY/ folder.
    if args.year is not None:
        year_dir = run_dir / f"year_{args.year}"
        if not year_dir.is_dir():
            raise SystemExit(
                f"year folder not found: {year_dir}. Available years: "
                + ", ".join(str(y) for y, _ in _all_year_dirs(run_dir))
            )
        target_year = args.year
    else:
        year_dir = _latest_year_dir(run_dir)
        m = YEAR_FOLDER_RE.match(year_dir.name)
        assert m is not None
        target_year = int(m.group(1))

    # Warn if not the latest year — replay doesn't cascade.
    all_years = _all_year_dirs(run_dir)
    latest_year = all_years[-1][0] if all_years else target_year
    if target_year != latest_year:
        print(
            f"[warn] replaying year {target_year} but the run's latest "
            f"year is {latest_year}. Later years were built on the old "
            f"artefacts and will not be refreshed — their chapter_index "
            f"entries and cast state are now inconsistent. Re-run "
            f"subsequent years manually if you need them."
        )

    seed_path = run_dir / f"year_{target_year - 1}_seed.json"
    # Seed lives at year_<seed>_seed.json. Fall back to the default seed
    # file if the replay targets a year beyond the first one.
    if not seed_path.exists():
        # Find any seed file in the run folder.
        candidates = sorted(run_dir.glob("year_*_seed.json"))
        if not candidates:
            raise SystemExit(
                f"no seed file found in {run_dir}; cannot replay without "
                f"knowing the seed year."
            )
        seed_path = candidates[0]
    seed_state = poc._load_json_strict(seed_path, context="seed")  # noqa: SLF001

    style_guide = poc.STYLE_ASIMOV_PATH.read_text(encoding="utf-8")

    parent_state, previous_summary, prev_chapter_text, prev_year = (
        _load_previous_context(run_dir, target_year, seed_state)
    )

    # Load the fork from disk — replay does not re-prompt the user.
    fork_path = year_dir / "01_fork.json"
    chosen_fork = poc._load_json_strict(fork_path, context="fork")  # noqa: SLF001

    # Strip this year's entry from chapter_index.json so the outline /
    # beat-sheet freshness windows don't see a stale self-reference
    # when we re-run them. The pipeline re-writes the entry at the end
    # of generate_epoch (when stage 06a is re-run; on higher start_from
    # values the old entry stays stripped and no replacement is written
    # — acceptable because those stages don't change the recorded
    # fields anyway).
    if poc._should_run("06a", args.from_stage):  # noqa: SLF001
        _strip_current_year_from_chapter_index(run_dir, target_year)

    poc._print_rule(  # noqa: SLF001
        f"REPLAY run={args.run_id} year={target_year} "
        f"from-stage={args.from_stage}"
    )
    print(f"  run_dir:      {run_dir}")
    print(f"  year_dir:     {year_dir}")
    print(f"  fork:         {chosen_fork.get('title','?')} "
          f"({chosen_fork.get('domain','?')})")
    print(f"  prev_year:    {prev_year if prev_year is not None else '(seed)'}")

    # Stage 09 never calls OpenAI — avoid constructing the client so
    # `replay.py --from-stage 09` works without an API key at all.
    client = AsyncOpenAI() if args.from_stage != "09" else None

    epoch = await poc.generate_epoch(
        client,
        run_dir=run_dir,
        year_dir=year_dir,
        parent_state=parent_state,
        chosen_fork=chosen_fork,
        previous_summary=previous_summary,
        prev_chapter_text=prev_chapter_text,
        prev_year=prev_year,
        style_guide=style_guide,
        start_from=args.from_stage,
    )

    poc._print_rule(f"REPLAY COMPLETE — year {epoch['year']}")  # noqa: SLF001
    # Print final prose only if we actually re-ran the narrator / editor
    # / continuity (otherwise the user just ran forks or readability;
    # the prose on disk is unchanged and printing it adds noise).
    if poc._should_run("06f", args.from_stage):  # noqa: SLF001
        print()
        print(epoch["story"])


def main() -> None:
    args = _parse_args()
    try:
        asyncio.run(_replay(args))
    except KeyboardInterrupt:
        print("\nInterrupted.")


if __name__ == "__main__":
    main()
