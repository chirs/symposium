# Roadmap

## Phase 0: Foundation

- [x] Project brief, README, CLAUDE.md
- [x] Platonic corpus — 25 Jowett dialogues in `corpus/`
- [x] Character system prompts — Socrates, Thrasymachus, Polemarchus, Cephalus in `prompts/`

## Phase 1: Orchestration & Seed

- [ ] Orchestration spec — turn order, transcript-as-context, interjection handling, branching data model
- [ ] Seed dialogue — opening exchanges of Republic Book I

## Phase 2: CLI Engine

- [ ] Generation loop — Python script, takes seed + prompts, generates next turn via Anthropic API
- [ ] Turn management — follow scripted turn order per scene
- [ ] Interjection — insert user text as "The Stranger", discard subsequent exchanges, continue from new point
- [ ] Branch revert — restore pre-interjection path

## Phase 3: Web Interface

- [ ] React SPA scaffold
- [ ] Reading view — clean serif typography, speaker labels, generous whitespace
- [ ] Step-through navigation — forward/back through exchanges
- [ ] Step-forward-generates — advancing past last exchange triggers API call
- [ ] Text input — interjecting as The Stranger
- [ ] Branch controls — return to original path

## Phase 4: Expansion

- [ ] Additional Republic speakers (Glaucon, Adeimantus)
- [ ] Prompts for a second dialogue (Symposium or Gorgias)
- [ ] Corpus-informed prompt refinement — use `corpus/` texts to sharpen character voice

## Deferred

- Persistence / save-load
- Branching tree visualization
- Dialogue selection UI
- Export
- Multi-model orchestration
- Personality tuning UI
