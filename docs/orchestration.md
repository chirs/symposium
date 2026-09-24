# Orchestration

How a dialogue is generated, one exchange at a time.

## The dialogue file

A dialogue is a plain text script. Each exchange is a speaker label in capitals, a colon, and the speech, with a blank line between exchanges:

```
SOCRATES: Is not Polemarchus your heir?

CEPHALUS: To be sure.
```

A speech may span paragraphs; it runs until the next label. The user's label is `THE STRANGER`. A paragraph wrapped in square brackets is a stage direction: it is shown to the reader and sent to the model in brackets, but it is nobody's turn and does not affect the turn order.

```
[Cephalus goes away laughing to the sacrifices.]
```

The file is the state. Edit it by hand whenever you like; the engine re-reads it on every command.

## A dialogue directory

```
dialogues/<name>/
  script.json     title, setting, scene, phases
  seed.md         the whole dialogue in script form, from the Jowett text; narration becomes directions
  prompts/        one <speaker>.md per character named in the phases
  run.md          the working copy, created from seed.md on first use (gitignored)
```

`symposium new <name>` copies the seed to `run.md`; the server does the same on first access. The seed is the complete text, so reading a dialogue is reading Plato; the model only speaks after an interjection or past the end. `tools/from_corpus.py` converts the speaker-tagged corpus files; `tools/republic1.py` and `tools/symposium.py` convert the two narrated ones and record every hand correction. `script.json` carries a `setting` (one line, shown under the title) and a `scene` (a paragraph on who is present, where, and what has just happened), both optional.

## Turn order

Turn order is scripted, not chosen by the model. `script.json` lists phases, each with a cycle of speakers and a length in exchanges:

```json
{"name": "Polemarchus", "speakers": ["socrates", "polemarchus"], "length": 18}
```

The next speaker is found by counting the scripted exchanges so far (The Stranger's lines do not count) to pick the phase, then taking the speaker who follows the last scripted speaker in that phase's cycle. If the last speaker is not in the cycle, the cycle starts over, which is how Thrasymachus gets his entrance and how the Symposium moves from one encomium to the next with phases of length one. The last phase repeats indefinitely. `symposium next --speaker NAME` overrides the script for one exchange.

Because the rule keys off the last speaker rather than an index, hand edits and interjections never break alternation. Phase lengths only decide when the scene changes.

## Generation

One API call per exchange (`symposium/generate.py`):

- **System prompt**: `prompts/orchestration.md`, the rules shared by every character; then the `# System Prompt` section of `dialogues/<name>/prompts/<speaker>.md` (the profile above that heading is documentation and is not sent); then the script's `scene` under a `## The scene` heading.
- **User message**: the full transcript, one content block per exchange, then a cue naming the speaker and asking for the words alone. A cache breakpoint sits on the last transcript block so a character's later turns reuse the cached prefix.
- **Model**: `SYMPOSIUM_MODEL`, default `claude-opus-5`, with the model's default adaptive thinking. `SYMPOSIUM_EFFORT` sets `output_config.effort` when present.
- The response streams to the terminal as it arrives. Any stop reason other than `end_turn` is an error and nothing is appended. A leading speaker label, if the model adds one anyway, is stripped.

Socrates has a separate prompt in every dialogue: he tests definitions in Republic I and Euthyphro, argues to a conclusion in Crito and Gorgias, and recounts Diotima in the Symposium.

## Interjection

`symposium interject FILE "text" --at N` inserts `THE STRANGER: text` after the first N exchanges (default: the end) and discards everything after it. The next generated speaker is whoever the script says follows the last scripted speaker, so the Stranger's line never shifts the turn order.

The characters are told, in the shared preamble, that the Stranger has been present from the start, to answer the argument on its merits, and never to remark on the interruption or on the conversation changing course. Speech-givers in the Symposium are told to answer the Stranger at the opening of their encomium.

## Branching

Before the first interjection diverges from a path, the whole file is snapshotted to `<file>.original.md`. Later interjections on the same branch leave that snapshot alone. `symposium revert` restores the snapshot and deletes it. There is one saved original per working file, not a tree. Start over (web only) copies the seed back over `run.md` and clears the snapshot.

## Interactive use

`symposium run FILE` keeps a cursor. Enter shows the next existing exchange or generates one when there are none left. Typed text interjects at the cursor. `/end`, `/revert`, and `/quit` do what they say.

`symposium serve` discovers every `dialogues/*/script.json` and serves:

```
GET  /api/dialogues                    name, title, setting, characters for each
GET  /api/dialogues/{name}             exchanges, has_original, next_speaker
POST /api/dialogues/{name}/next        {speaker?}
POST /api/dialogues/{name}/interject   {text, at?}
POST /api/dialogues/{name}/revert
POST /api/dialogues/{name}/reset
```

and `web/index.html`, which shows a list of dialogues until one is chosen (`#name` in the URL), then the reading view with the same cursor model as the CLI.
