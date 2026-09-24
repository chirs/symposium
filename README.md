# Symposium

AI-generated Platonic dialogues you can participate in.

## Concept

Symposium simulates philosophical dialogues between historical characters using the Claude API. Each character has a system prompt capturing their argumentative style, and the dialogue builds exchange by exchange. The full transcript is passed as context for each new response; turn order is scripted per scene.

The key mechanic is interjection: you can insert yourself into the conversation as "The Stranger" at any point. The characters respond to your actual argument and the dialogue continues from there. Everything after your interjection is discarded, and you can return to the original path at any time.

The dialogue is a plain text file. Edit it by hand if you like; the engine re-reads it every time.

## Quick start

```
uv venv && uv pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...
.venv/bin/symposium serve                               # pick a dialogue at http://127.0.0.1:8000
```

or in the terminal:

```
.venv/bin/symposium new gorgias                         # -> dialogues/gorgias/run.md
.venv/bin/symposium run dialogues/gorgias/run.md        # Enter steps or generates, typed text interjects
```

## Dialogues

| Name | Speakers | Text |
| --- | --- | --- |
| `republic-1` | Socrates, Cephalus, Polemarchus, Thrasymachus (Glaucon, Adeimantus, Cleitophon briefly) | Republic Book I, complete |
| `euthyphro` | Socrates, Euthyphro | complete |
| `crito` | Socrates, Crito | complete |
| `gorgias` | Socrates, Gorgias, Polus, Callicles (Chaerephon briefly) | complete |
| `symposium` | Phaedrus, Pausanias, Eryximachus, Aristophanes, Agathon, Socrates, Alcibiades | complete, from Aristodemus's arrival at Agathon's |

Each lives in `dialogues/<name>/` as `script.json` (title, setting, scene, turn order), `seed.md` (the whole dialogue in script form, from the Jowett text in `corpus/`, with narration turned into bracketed stage directions), and `prompts/<speaker>.md` (a character profile above `# System Prompt`, the prompt itself below). Socrates has a different prompt in each, because he argues differently in each.

You read Plato's text; generation happens only where you leave it: after an interjection as The Stranger, or past the end. `tools/` holds the scripts that made the seeds from the corpus.

## Commands

| Command | What it does |
| --- | --- |
| `symposium serve` | browser reading view: choose a dialogue, step, interject, revert, start over |
| `symposium new NAME [OUT]` | copy a dialogue's seed to a working file |
| `symposium show FILE` | print the dialogue |
| `symposium next FILE [-n K] [--speaker X]` | generate the next exchange(s) |
| `symposium interject FILE "text" [--at N]` | speak as The Stranger after exchange N; discard the rest |
| `symposium revert FILE` | return to the pre-interjection path |
| `symposium run FILE` | interactive: Enter steps or generates, typed text interjects |

The web view and the CLI work on the same files: `dialogues/<name>/run.md`, created from the seed on first use.

Environment: `ANTHROPIC_API_KEY`; `SYMPOSIUM_MODEL` (default `claude-opus-5`); `SYMPOSIUM_EFFORT` (`low` to `max`, optional).

How generation, turn order, and branching work: [docs/orchestration.md](docs/orchestration.md).

## Repo structure

```
symposium/      engine: dialogue file model, scripted turn order, generation, CLI, server
dialogues/      one directory per dialogue: script.json, seed.md, prompts/
prompts/        orchestration.md, the rules shared by every character
web/            the reading view, one static page
docs/           orchestration spec
corpus/         25 Platonic dialogues, full text (Jowett 3rd ed., 1892)
tests/          pytest; generation is tested against a fake client
```

## Corpus

25 dialogues in `corpus/`, full text from the Jowett translation (3rd edition, 1892):

**Early:** Apology, Charmides, Crito, Euthydemus, Euthyphro, Gorgias, Ion, Laches, Lysis, Meno, Protagoras
**Middle:** Cratylus, Phaedo, Phaedrus, Republic, Symposium, Theaetetus, Parmenides
**Late:** Critias, Laws, Philebus, Sophist, Statesman, Timaeus
**Other:** Seventh Letter

Source text is OCR-extracted; some minor artifacts remain.

## Audience

People with a classical education who would notice if Socrates skipped a step.
