# Orchestration

How a dialogue is generated, one exchange at a time.

## The dialogue file

A dialogue is a plain text script. Each exchange is a speaker label in capitals, a colon, and the speech, with a blank line between exchanges:

```
SOCRATES: Is not Polemarchus your heir?

CEPHALUS: To be sure.
```

A speech may span paragraphs; it runs until the next label. The user's label is `THE STRANGER`. The file is the state. Edit it by hand whenever you like; the engine re-reads it on every command.

`symposium new republic-1` copies `dialogues/republic-1/seed.md` to `run.md` in the same directory. Everything else operates on that working file.

## Turn order

Turn order is scripted, not chosen by the model. `dialogues/<name>/script.json` lists phases, each with a cycle of speakers and a length in exchanges:

```json
{"name": "Polemarchus", "speakers": ["socrates", "polemarchus"], "length": 18}
```

The next speaker is found by counting the scripted exchanges so far (The Stranger's lines do not count) to pick the phase, then taking the speaker who follows the last scripted speaker in that phase's cycle. If the last speaker is not in the cycle, the cycle starts over, which is how Thrasymachus gets his entrance. The last phase repeats indefinitely. `symposium next --speaker NAME` overrides the script for one exchange.

Because the rule keys off the last speaker rather than an index, hand edits and interjections never break alternation. Phase lengths only decide when the scene changes.

## Generation

One API call per exchange (`symposium/generate.py`):

- **System prompt**: `prompts/orchestration.md`, the rules shared by every character, followed by the `# System Prompt` section of `prompts/<speaker>.md`. The character profile above that heading is documentation and is not sent.
- **User message**: the full transcript, one content block per exchange, then a cue naming the speaker and asking for the words alone. A cache breakpoint sits on the last transcript block so a character's later turns reuse the cached prefix.
- **Model**: `SYMPOSIUM_MODEL`, default `claude-opus-5`, with the model's default adaptive thinking. `SYMPOSIUM_EFFORT` sets `output_config.effort` when present.
- The response streams to the terminal as it arrives. Any stop reason other than `end_turn` is an error and nothing is appended. A leading speaker label, if the model adds one anyway, is stripped.

## Interjection

`symposium interject FILE "text" --at N` inserts `THE STRANGER: text` after the first N exchanges (default: the end) and discards everything after it. The next generated speaker is whoever the script says follows the last scripted speaker, so the Stranger's line never shifts the turn order.

The characters are told, in the shared preamble, that the Stranger has been present from the start, to answer the argument on its merits, and never to remark on the interruption or on the conversation changing course.

## Branching

Before the first interjection diverges from a path, the whole file is snapshotted to `<file>.original.md`. Later interjections on the same branch leave that snapshot alone. `symposium revert` restores the snapshot and deletes it. There is one saved original per working file, not a tree.

## Interactive use

`symposium run FILE` keeps a cursor. Enter shows the next existing exchange or generates one when there are none left. Typed text interjects at the cursor. `/end`, `/revert`, and `/quit` do what they say.

`symposium serve [FILE]` exposes the same operations over JSON (`/api/dialogue`, `/api/next`, `/api/interject`, `/api/revert`) and serves `web/index.html`, a reading view with the same cursor model. Without a file it works on an in-memory copy of the seed.
