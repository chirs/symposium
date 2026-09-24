# ROADMAP.md — Development Roadmap

Open work only; completed items are removed as they land (see git history).

---

## Characters

- [ ] Additional Republic speakers: Glaucon, Adeimantus
- [ ] Let minor speakers (Polemarchus, Cleitophon) interject during the Thrasymachus phase
- [ ] Corpus-informed prompt refinement: use `corpus/` texts to sharpen character voice

## Dialogues

- [ ] Read each new dialogue's generated output for voice and tighten the prompts (only Republic I has been run live)

## Reading view

- [ ] Jump to a specific exchange
- [ ] Stream generated text into the page instead of waiting for the whole speech

## Deferred

- Persistence beyond the working file: the text file is the state
- Branching tree visualization: one path at a time, with revert, is the point
- Export: the dialogue is already a text file
- Multi-model orchestration: get one model's characters right first
- Personality tuning UI: edit `prompts/*.md`
