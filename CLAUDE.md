# Symposium

## What This Is

A simulator for Platonic dialogues using the Claude API. Each character has a system prompt capturing their argumentative style, and the dialogue builds exchange by exchange. The user can interject as "The Stranger" at any point, and the dialogue continues from there.

The dialogue is a plain text file (`dialogues/republic-1/run.md`). A Python CLI (`symposium`) steps, generates, interjects, and reverts; a FastAPI server exposes the same engine to a single-page reading view.

## Design Principles

- **Character fidelity over features.** The quality of character system prompts is where the project succeeds or fails. Characters must argue in their distinctive styles, not converge into polite agreement.
- **Interjection without ceremony.** When the user interjects, characters respond to the actual argument without commenting on the divergence. The dialogue continues as though it always included this exchange.
- **The file is the state.** Anything the engine can do, the user can do by editing the text. Keep the format hand-editable.
- **Reading view, not chat.** Clean serif typography, speaker labels, generous whitespace. No chat bubbles, no UI chrome competing with the text.
- **Stepping forward = generating.** Advancing past the last existing exchange triggers API generation for the next speaker's response.

## Simulation

- Model: `SYMPOSIUM_MODEL`, default `claude-opus-5`, adaptive thinking left at the model default. `SYMPOSIUM_EFFORT` optional.
- Each call sends `prompts/orchestration.md` plus the character's `# System Prompt` section as the system prompt, and the full transcript as one content block per exchange with a cache breakpoint on the last one.
- Turn order is scripted per scene in `dialogues/<name>/script.json`, not model-driven. The Stranger's lines never consume a turn.
- Branching: an interjection discards everything after it. The first divergence snapshots the file to `<file>.original.md`; `symposium revert` restores it.

Full spec: `docs/orchestration.md`.

## Layout

```
symposium/dialogue.py   exchange parsing/formatting, Dialogue with interject/revert, file + sidecar I/O
symposium/script.py     Script/Phase, next_speaker
symposium/generate.py   system prompt assembly, request params, streaming call
symposium/cli.py        new / show / next / interject / revert / run / serve
symposium/server.py     build_app(path, name, generate) -> FastAPI
web/index.html          reading view, vanilla JS, talks to /api/*
prompts/                orchestration.md + one file per character (profile above `# System Prompt`, prompt below)
dialogues/republic-1/   script.json, seed.md; run*.md is gitignored
corpus/                 25 Jowett dialogues, plain text
```

## Character Prompts

`prompts/` contains system prompts for Socrates, Thrasymachus, Polemarchus, Cephalus. Each file has a character profile (documentation) above `# System Prompt` and the prompt itself below; only the part below is sent. Each captures the character's argumentative style and philosophical commitments for Republic Book I.

## Development

- `.venv/bin/pytest` and `.venv/bin/ruff check .` before declaring done. Generation is tested through a fake client in `tests/conftest.py`; nothing in the test suite calls the API.
- A live check is `symposium new republic-1 --force && symposium next dialogues/republic-1/run.md -n 2`, then read the output for voice: Socrates asks, Thrasymachus doesn't fold.

## What We're Deferring

- Persistence beyond the working file
- Branching tree visualization
- Multiple dialogue selections in the UI
- Export
- Multi-model orchestration
- Personality tuning UI

## Audience

People with a classical education who would notice if Socrates skipped a step.
