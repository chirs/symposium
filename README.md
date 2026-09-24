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

The landing page groups them by collection.

**Plato** (Jowett, 1892):

| Name | Speakers | Text |
| --- | --- | --- |
| `republic-1` | Socrates, Cephalus, Polemarchus, Thrasymachus (Glaucon, Adeimantus, Cleitophon briefly) | Republic Book I, complete |
| `euthyphro` | Socrates, Euthyphro | complete |
| `crito` | Socrates, Crito | complete |
| `gorgias` | Socrates, Gorgias, Polus, Callicles (Chaerephon briefly) | complete |
| `symposium` | Phaedrus, Pausanias, Eryximachus, Aristophanes, Agathon, Socrates, Alcibiades | complete, from Aristodemus's arrival at Agathon's |

**New Testament** (World English Bible, public domain):

| Name | Speakers | Text |
| --- | --- | --- |
| `john-3-nicodemus` | Jesus, Nicodemus | John 3:1–21 |
| `john-4-well` | Jesus, the Samaritan woman (disciples, Samaritans) | John 4:1–42 |
| `john-18-pilate` | Pilate, Jesus, the chief priests (the crowd) | John 18:28–19:16 |
| `acts-17-athens` | Paul, a Stoic, an Epicurean | Acts 17:16–34 |
| `matthew-22-temple` | Jesus, a Pharisee, a Sadducee, a lawyer | Matthew 22:15–46 |

Each lives in `dialogues/<name>/` as `script.json` (title, collection, setting, scene, turn order), `seed.md` (the whole passage in script form, from the source text in `corpus/`, with narration turned into bracketed stage directions), and `prompts/<speaker>.md` (a character profile above `# System Prompt`, the prompt itself below). Socrates has a different prompt in each Platonic dialogue, because he argues differently in each. Characters who recur across passages live once in `prompts/characters/` (Jesus), which any dialogue falls back to and which the sandbox lists as "Shared".

You read Plato's text; generation happens only where you leave it: after an interjection as The Stranger, or past the end. `tools/` holds the scripts that made the seeds from the corpus.

## A conversation of your own

The landing page ends with a form: pick any characters from any dialogue (Socrates comes in five versions, one per dialogue), give the company a setting, a scene paragraph, and optionally an opening question that The Stranger puts to them, and begin. A small model call decides who speaks next after each exchange, since there is no script; clicking a name in the guest strip makes that character answer instead. Sandboxes live in `dialogues/sandbox-<slug>/` (gitignored), work exactly like the fixed dialogues, and can be removed from the landing page.

From the terminal:

```
.venv/bin/symposium characters
.venv/bin/symposium sandbox "Power and Justice" \
    --cast socrates@gorgias,callicles@gorgias,thrasymachus@republic-1 \
    --setting "A wine shop in the Piraeus, late" \
    --scene "They have been drinking since sundown and the question of whether the strong man is the happy man will not drop." \
    --opening "Is the man who takes what he wants happier than the man who takes what is his?"
.venv/bin/symposium run dialogues/sandbox-power-and-justice/run.md
```

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
| `symposium characters` | every character and the dialogue it comes from |
| `symposium sandbox TITLE --cast ... --setting ... --scene ... [--opening ...]` | start a conversation of your own |

The web view and the CLI work on the same files: `dialogues/<name>/run.md`, created from the seed on first use.

Environment: `ANTHROPIC_API_KEY`; `SYMPOSIUM_MODEL` (default `claude-opus-5`); `SYMPOSIUM_EFFORT` (`low` to `max`, optional); `SYMPOSIUM_DIRECTOR_MODEL` (default `claude-haiku-4-5`, the small call that picks the next speaker in a sandbox).

How generation, turn order, and branching work: [docs/orchestration.md](docs/orchestration.md).

## Repo structure

```
symposium/      engine: dialogue file model, scripted turn order, generation, CLI, server
dialogues/      one directory per dialogue: script.json, seed.md, prompts/
prompts/        orchestration.md and director.md; prompts/characters/ is the shared pool
web/            the reading view, one static page
docs/           orchestration spec
corpus/         25 Platonic dialogues (Jowett 3rd ed., 1892); corpus/nt/ holds World English Bible chapters
tests/          pytest; generation is tested against a fake client
```

## Corpus

25 dialogues in `corpus/`, full text from the Jowett translation (3rd edition, 1892), and in `corpus/nt/` the World English Bible chapters the New Testament dialogues are cut from, fetched by `tools/fetch_web.py`:

**Early:** Apology, Charmides, Crito, Euthydemus, Euthyphro, Gorgias, Ion, Laches, Lysis, Meno, Protagoras
**Middle:** Cratylus, Phaedo, Phaedrus, Republic, Symposium, Theaetetus, Parmenides
**Late:** Critias, Laws, Philebus, Sophist, Statesman, Timaeus
**Other:** Seventh Letter

Source text is OCR-extracted; some minor artifacts remain.

## Audience

People with a classical education who would notice if Socrates skipped a step.
