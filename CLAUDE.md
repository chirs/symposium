# Symposium

## What This Is

A simulator for Platonic dialogues using the Claude API. Each character has a system prompt capturing their argumentative style, and the dialogue builds exchange by exchange. The user can interject as "The Stranger" at any point, and the dialogue continues from there.

Five dialogues so far: Republic I, Euthyphro, Crito, Gorgias, Symposium. Each is a directory under `dialogues/` with its script, seed, and prompts. A Python CLI (`symposium`) steps, generates, interjects, and reverts a plain text file; a FastAPI server exposes every dialogue to a single-page reading view that lets the reader choose one.

## Design Principles

- **Character fidelity over features.** The quality of character system prompts is where the project succeeds or fails. Characters must argue in their distinctive styles, not converge into polite agreement.
- **Interjection without ceremony.** When the user interjects, characters respond to the actual argument without commenting on the divergence. The dialogue continues as though it always included this exchange.
- **The file is the state.** Anything the engine can do, the user can do by editing the text. Keep the format hand-editable.
- **Reading view, not chat.** Dark, lamplit, serif; speaker labels as inscriptions; no chat bubbles, no UI chrome competing with the text.
- **Stepping forward = generating.** Advancing past the last existing exchange triggers API generation for the next speaker's response.

## Simulation

- Model: `SYMPOSIUM_MODEL`, default `claude-opus-5`, adaptive thinking left at the model default. `SYMPOSIUM_EFFORT` optional.
- System prompt per call: `prompts/orchestration.md`, then the `# System Prompt` section of `dialogues/<name>/prompts/<speaker>.md`, then the script's `scene` paragraph. The transcript goes as one content block per exchange with a cache breakpoint on the last one.
- Turn order is scripted per dialogue in `script.json` phases, not model-driven. The Stranger's lines never consume a turn. Symposium uses one phase per encomium.
- Branching: an interjection discards everything after it. The first divergence snapshots the file to `<file>.original.md`; revert restores it. Start over copies the seed back.

Full spec: `docs/orchestration.md`.

## Layout

```
symposium/dialogue.py   exchange parsing/formatting, Dialogue with interject/revert, file + sidecar I/O
symposium/script.py     Script (title, setting, scene, phases, dir), next_speaker, discover()
symposium/generate.py   system prompt assembly, request params, streaming call
symposium/cli.py        new / show / next / interject / revert / run / serve
symposium/server.py     build_app(dialogues_dir, generate): /api/dialogues[/{name}[/next|interject|revert|reset]]
web/index.html          landing list + reading view, vanilla JS
prompts/orchestration.md  rules shared by every character
dialogues/<name>/       script.json, seed.md, prompts/<speaker>.md; run*.md is gitignored
corpus/                 25 Jowett dialogues, plain text
```

## Adding a dialogue

Make `dialogues/<name>/` with `script.json` (title, setting, scene, phases), `seed.md` in script form adapted from `corpus/`, and one prompt per speaker named in the phases, each with a profile above `# System Prompt` and the prompt below. `tests/test_script.py` checks every dialogue directory for completeness. Socrates gets his own prompt per dialogue; do not share one.

## Development

- `.venv/bin/pytest` and `.venv/bin/ruff check .` before declaring done. Generation is tested through a fake client in `tests/conftest.py`; nothing in the test suite calls the API.
- A live check is `symposium new <name> --force && symposium next dialogues/<name>/run.md -n 2`, then read the output for voice.

## What We're Deferring

- Persistence beyond the working file
- Branching tree visualization
- Export
- Multi-model orchestration
- Personality tuning UI

## Audience

People with a classical education who would notice if Socrates skipped a step.
