# Roadmap

## Phase 0: Foundation

- [x] Project brief, README, CLAUDE.md
- [x] Platonic corpus — 25 Jowett dialogues in `corpus/`
- [ ] Character system prompts — Socrates, Thrasymachus, Polemarchus for Republic Book I
- [ ] Orchestration spec — turn order, transcript-as-context, interjection handling, branching data model
- [ ] Seed dialogue — opening exchanges of Republic Book I

## Phase 1: Dialogue Engine

- [ ] Generation loop — pass full transcript + speaker system prompt to API, get next exchange
- [ ] Turn management — determine next speaker from dialogue state
- [ ] Interjection — insert user as "The Stranger", discard everything after, continue from new branch
- [ ] Branch revert — "return to original" restores pre-interjection path

## Phase 2: Web Interface

- [ ] React SPA scaffold
- [ ] Reading view — clean serif typography, speaker labels, generous whitespace
- [ ] Step-through navigation — forward/back through exchanges
- [ ] Step-forward-generates — advancing past last exchange triggers API call
- [ ] Text input — bottom bar for interjecting as The Stranger
- [ ] Branch controls — return to original path

## Phase 3: Character Expansion

- [ ] Additional Republic speakers (Glaucon, Adeimantus, Cephalus)
- [ ] Prompts for a second dialogue (Symposium or Gorgias)
- [ ] Corpus-informed prompt refinement — use `corpus/` texts to sharpen character voice

## Deferred

- Persistence / save-load
- Branching tree visualization
- Dialogue selection UI
- Export
- Multi-model orchestration
- Personality tuning UI
