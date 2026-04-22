# Future Weavers — Concept

> A collaboratively-authored, branching **tree of futures**. Five specialist AI agents describe how the world changes, year by year, from today onward. An orchestrator weaves their notes into literary sci-fi prose; an editor polishes it. Readers walk the tree, and at any node they can **pick a different fork** to spawn a new branch — which future generations of readers will then inherit and explore further.

---

## TL;DR for AI

- **What it is:** A web app where humanity's possible futures are written, one year at a time, by a committee of LLM agents. Every user choice permanently branches the tree. The tree is a shared, growing literary artifact.
- **Core tension to manage:** Quality prose + multi-agent depth is *expensive*. The whole architecture is designed around writing each node **once, cheaply, and caching it forever** — so cost amortizes across all future readers.
- **Key design insight:** The canonical representation of the world is a **structured JSON State**, not prose. Specialists mutate state (cheap). Only the orchestrator + editor produce prose (mid/premium tier). Prose is a rendering of state, not the source of truth.
- **MVP stack:** Next.js (App Router) + Supabase (Postgres + Auth + Realtime) + OpenAI tiered (mini/standard/premium) + React Flow for the tree.
- **What's deferred:** AI images, maps, voice, user accounts beyond email magic-link, custom seeds, mobile.

---

## 1. The Core Loop (one epoch)

An **epoch = 1 year**. Each node in the tree represents one year of one possible future.

```
┌─────────────────────────────────────────────────────────────┐
│  User lands on a node (e.g. "Year 2029, branch A")          │
│  They read the literary description                         │
│  Orchestrator has surfaced 3 forks for next year, e.g.      │
│   - "Climate accords collapse"                              │
│   - "Fragile truce holds"                                   │
│   - "Geoengineering gamble succeeds"                        │
│  User picks one → new child node is generated               │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  1. Load parent State (JSON)                             │
  │  2. Fan out to 5 specialists, in parallel, CHEAP model:  │
  │     each returns a State Delta (JSON patch + 2-4         │
  │     bullet-point notes about what changed & why)         │
  │  3. Merge deltas → new State                             │
  │  4. Orchestrator (MID model): writes ~400-600 word       │
  │     literary prose describing the year, using:           │
  │       - new State                                        │
  │       - specialist notes                                 │
  │       - tone/style guide                                 │
  │  5. Editor (PREMIUM model, short context): polishes      │
  │     prose, fixes repetition, tightens voice              │
  │  6. Orchestrator (MID model): generates 3 fork options   │
  │     for next year, derived from tensions in new State    │
  │  7. Persist node + State + prose + forks (immutable)     │
  └──────────────────────────────────────────────────────────┘
```

**Why this order saves money:**
- Specialists output compact JSON, not essays → tiny token counts.
- Only *one* premium-model call per node (editor pass).
- Orchestrator reads the compact State, not concatenated specialist essays.
- Nodes are **immutable once written** — the next 1,000 readers pay $0.

---

## 2. Agents

### 2.1 Specialists (cheap model, e.g. `gpt-5-mini` / `claude-haiku` / local)

Each receives: `(parent_state, chosen_fork, year)` → returns JSON delta + short notes.

| Agent | Responsibility | State facets it owns |
|---|---|---|
| **Ecology** | Climate, biosphere, resources, disasters | `climate`, `biomes`, `resources`, `disasters[]` |
| **Economy** | Markets, tech, labor, trade, energy | `gdp_trends`, `tech_level`, `labor`, `trade`, `energy_mix` |
| **Geopolitics** | Nations, alliances, conflicts, military | `nations[]`, `alliances[]`, `conflicts[]`, `military_posture` |
| **Society** | Demographics, health, migration, politics | `population`, `health`, `migration`, `political_climate` |
| **Culture** | Art, media, religion, values, subcultures | `art_movements[]`, `media`, `values_shift`, `subcultures[]` |

Each specialist is a prompt template + JSON schema. No fine-tuning.

**Output budget per specialist:** ~200–400 tokens (JSON + 2–4 bullet notes).

### 2.2 Orchestrator (mid-tier model, e.g. `gpt-5.4-mini`)

Two jobs:
1. **Weave**: takes `new_state` + `specialist_notes` + `style_guide` → writes 400–600 words of literary sci-fi prose for the year.
2. **Fork**: analyzes tensions in `new_state` → proposes 3 meaningful divergences for the *next* year, each as a 1-sentence title + 1-paragraph flavor.

### 2.3 Editor (premium model, e.g. `gpt-5.4` or `claude-opus`)

Takes orchestrator prose → tightens, removes clichés, enforces voice. Short context (just the prose + style guide). This is the only premium call per node.

### 2.4 Style Guide (static)

A short markdown doc defining the project's literary voice (e.g. "Kim Stanley Robinson meets Ted Chiang — concrete sensory detail, avoid melodrama, ground speculation in named people and places"). Injected into orchestrator + editor prompts.

---

## 3. World State Schema (sketch)

```json
{
  "year": 2029,
  "branch_id": "uuid",
  "parent_node_id": "uuid",
  "ecology": {
    "global_temp_anomaly_c": 1.42,
    "co2_ppm": 428,
    "notable_events": ["Amazon reaches 22% deforestation tipping threshold"],
    "biomes": { "amazon": "stressed", "arctic": "ice-free-summer" }
  },
  "economy": { /* ... */ },
  "geopolitics": {
    "major_powers": ["USA", "China", "EU", "India", "Russia", "..."],
    "active_conflicts": [{ "region": "Taiwan Strait", "intensity": "cold" }],
    "key_treaties": []
  },
  "society": { /* ... */ },
  "culture": { /* ... */ },
  "narrative_threads": [
    { "id": "thread-1", "name": "The Baikal Commons experiment", "arc_so_far": "..." }
  ]
}
```

**Why `narrative_threads` matter:** they're the orchestrator's continuity tool — named characters, movements, or places that recur. Prevents each year from feeling like a disconnected news bulletin.

---

## 4. Data Model

```
users (id, email, display_name, created_at)

branches (
  id, root_node_id, creator_id, title, created_at,
  visibility (public | unlisted)
)

nodes (
  id, branch_id, parent_id (null for root),
  year, depth,
  state (jsonb),           -- full snapshot, not just delta
  prose (text),            -- final edited prose
  fork_options (jsonb),    -- 3 orchestrator-proposed forks for next year
  chosen_fork (jsonb),     -- which fork led to THIS node from parent
  author_id (user who triggered generation),
  tokens_used (int), cost_cents (int),
  created_at
)

node_reads (node_id, user_id, read_at)   -- for analytics / "popular paths"
```

**Key property:** a `node` is immutable. Forking at a node = creating a new child with a different `chosen_fork`. The new child lives on a new branch id (or the same branch, depending on UX choice).

**Storage cost:** ~10 KB per node. 10,000 nodes = 100 MB. Trivial.

---

## 5. UX Flow (MVP)

1. **Landing:** "Explore humanity's futures." Shows the root node (Year 2026, real world) + a few popular branches as entry points.
2. **Node view:** Left = prose (readable typography, ~600 words). Right = mini-map of the tree with the current node highlighted.
3. **At the end of each node:** 3 fork cards. Hover = see flavor text. Click = "Walk this path." If the fork already exists (someone generated it before), you walk into the cached node instantly. If not, a generation spinner (~10–20s) streams prose as it's written.
4. **Tree view:** Full-screen React Flow graph of the entire explored future. Nodes colored by depth / popularity / theme. Click any node to jump in.
5. **Personal bookmark:** "Your path so far" — breadcrumb of the nodes you've walked.

**No accounts required for reading.** Magic-link email only when a user first generates a new node (to attribute authorship and rate-limit).

---

## 6. Tech Stack (MVP)

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 15 App Router + TypeScript | Server components cut client JS; streaming responses are first-class |
| UI | Tailwind + shadcn/ui | Fast, beautiful defaults |
| Graph | React Flow | Best-in-class tree/graph UI, free, handles 1000s of nodes |
| Backend | Next.js route handlers + Server Actions | No separate service |
| DB | Supabase (Postgres + Auth + Realtime) | Free tier fits MVP; `jsonb` perfect for State; realtime for "someone else just forked here" |
| LLM orchestration | Vercel AI SDK | Streaming, structured output, multi-provider |
| Models (tiered) | **Specialists:** `gpt-5.4-nano` · **Orchestrator:** `gpt-5.4-mini` · **Editor:** `gpt-5.4` (or `claude-opus`) | Spend premium tokens only where users can taste them |
| Hosting | Vercel | Free tier; edge streaming |
| Observability | Vercel logs + a `generations` table tracking tokens & cost per node | Know what each node cost |

---

## 7. Cost Model (napkin math)

Per node (one year of one branch):

| Call | Model tier | Input tokens | Output tokens | Est. $/call |
|---|---|---|---|---|
| 5 × specialists (parallel) | mini | ~1.5k each | ~300 each | ~$0.004 total |
| Orchestrator (weave) | mid | ~3k | ~800 | ~$0.02 |
| Orchestrator (fork options) | mid | ~2k | ~400 | ~$0.01 |
| Editor (polish) | premium | ~1k | ~800 | ~$0.04 |
| **Per node total** | | | | **~$0.07** |

*(Exact numbers depend on 2026 pricing; order of magnitude is what matters.)*

- 1,000 generated nodes ≈ **$70**.
- Because nodes are immutable and cached, the 1,001st reader costs **$0**.
- **Rate-limit new-node generation per user** (e.g. 10/day free, unlimited paid) so a single chaotic user can't spike costs.

---

## 8. MVP Scope — What's In, What's Out

### In (v0.1)
- 5 specialists, orchestrator, editor — as described.
- Real-2026 world as the single seed. One canonical root node, hand-written with the help of real facts.
- Branching tree, 1-year epochs, up to depth ~20 (year 2046).
- Public reading, magic-link signup to generate.
- React Flow tree view + node reader view.
- Per-user daily generation quota.
- Basic moderation (profanity/toxicity filter on generated prose; soft-block extreme outputs).

### Out (deferred)
- AI-generated images / world maps / icons per epoch.
- User-written custom forks ("write your own" option) — risks spam & cost. Add after moderation story is solid.
- Multiple seeds (fictional presets).
- Characters with persistent POVs across epochs (tempting but explodes context).
- Comments, likes, sharing beyond URL copy.
- Mobile-optimized tree view (desktop-first).
- i18n.

---

## 9. Phased Roadmap

### Phase 0 — Dry-run (weekend, before any UI)
- Write the 5 specialist prompts + orchestrator + editor as plain Python/TS scripts.
- Run locally: generate 5 years of one branch end-to-end.
- Read the output. Iterate prompts until prose is actually good.
- **Goal:** prove prose quality is worth shipping. If it feels generic, no UI will save it.

### Phase 1 — MVP shell (~1–2 weeks)
- Next.js + Supabase scaffolding.
- Single-branch generator backed by DB.
- Node reader view + 3-fork selector.
- Magic-link auth + rate limit.

### Phase 2 — Tree (~1 week)
- React Flow tree visualization.
- Multi-branch forking from any node.
- Public browsing.

### Phase 3 — Polish & launch
- Style guide hardening, moderation, cost dashboard, landing page.
- Soft launch to ~50 readers. Watch cost per active user.

### Phase 4+ — Stretch
- AI images per epoch (DALL·E / gpt-image-1, one hero image per node, cached).
- World map that mutates (SVG diff based on State).
- User-authored custom forks.
- Fictional-seed mode.

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **Prose feels generic / AI-slop** | Phase 0 dry-run gate. Strong style guide. Editor pass on premium model. Named recurring `narrative_threads`. |
| **Cost spirals from trolls forking everywhere** | Per-user daily node quota. CAPTCHA on signup. Generated nodes still require human click to trigger. |
| **Specialists contradict each other** | Orchestrator is the merge authority; it reads all 5 deltas and arbitrates. Plus a `consistency_check` JSON field the orchestrator must fill. |
| **State JSON balloons over 20 epochs** | Cap `narrative_threads` at N active; retire stale ones. Roll up old events into "historical_summary" string. |
| **Offensive / dangerous content generated** | Moderation pass (OpenAI/Anthropic moderation API) on every prose output before persisting. Soft-block + regenerate on flag. |
| **Cache invalidation if we change prompts** | Never regenerate old nodes. Version the prompt stack; new nodes use new version, old ones stay. |
| **Legal / real-person claims** | System prompt rule: no real living individuals beyond public heads of state, and only in plausible policy roles. |

---

## 11. Open Questions

1. **Named characters across epochs** — enticing but risks context bloat. Start with `narrative_threads` (movements/places) only?
2. **Voting vs solo forking** — should a fork require N votes before it's "the" path, or is every click its own branch? MVP = every click branches.
3. **Language** — English only for MVP? (Yes, unless you want EN + DE from day one.)
4. **Do we want "canonical" vs "what-if" branches?** — e.g., one thick, community-curated main trunk + many side branches. Could be a v2 governance feature.
5. **When does the story end?** — hard cap at year 2100? Or open-ended until the orchestrator declares a terminal state (extinction, singularity, utopia)?

---

## 12. First Concrete Steps

1. **Today:** Finalize the style guide (~300 words) and the 5 specialist JSON schemas. These are the creative foundation.
2. **This week:** Phase 0 dry-run. Just `node scripts/generate-one-year.ts`. Ship nothing until prose is good.
3. **Decide model providers** based on dry-run A/B — try at least 2 providers for the editor pass.
4. **Only then** start the Next.js scaffold.

---

*This concept is deliberately lean. The entire architecture is built around a single mantra: **state is cheap, prose is expensive, cache everything.***
