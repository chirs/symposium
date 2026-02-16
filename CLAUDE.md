# Symposium

## What This Is

A simulator for Platonic dialogues using the Anthropic API. Each character has a system prompt capturing their argumentative style, and the dialogue builds exchange by exchange. The user can interject as "The Stranger" at any point, and the dialogue continues from there.

The first target is a CLI engine (Python script). A web reading interface is a future phase.

## Design Principles

- **Character fidelity over features.** The quality of character system prompts is where the project succeeds or fails. Characters must argue in their distinctive styles, not converge into polite agreement.
- **Interjection without ceremony.** When the user interjects, characters respond to the actual argument without commenting on the divergence. The dialogue continues as though it always included this exchange.
- **Reading view, not chat.** Clean serif typography, speaker labels, generous whitespace. No chat bubbles, no UI chrome competing with the text.
- **Stepping forward = generating.** Advancing past the last existing exchange triggers API generation for the next speaker's response.

## Simulation

- Anthropic API (claude-sonnet-4-5-20250929) for generation
- Each generation call sends the full dialogue history plus the current speaker's character system prompt
- Turn order is scripted per scene, not model-driven
- Branching: when the user interjects, everything after that point is discarded. "Return to original" restores the pre-interjection path.

## Character Prompts

`prompts/` contains system prompts for 4 characters: Socrates, Thrasymachus, Polemarchus, Cephalus. Each captures the character's argumentative style and philosophical commitments for Republic Book I.

## Corpus

`corpus/` contains the full text of 25 Platonic dialogues (Jowett 3rd edition, 1892). One file per dialogue, plain text. OCR-extracted — minor artifacts but readable.

## Web Interface (future)

- React single-page app
- Dialogue state in memory — no persistence yet
- Clean serif typography, generous whitespace, the text is the interface

## What We're Deferring

- Persistence / save/load
- Branching tree visualization
- Multiple dialogue selections
- Export
- Multi-model orchestration
- Personality tuning UI

## Audience

People with a classical education who would notice if Socrates skipped a step.
