# Symposium

AI-generated Platonic dialogues you can participate in. Plus a web interface.

## Concept

Symposium simulates philosophical dialogues between historical characters using the Anthropic API. Each character has a system prompt capturing their argumentative style, and the dialogue builds exchange by exchange — the full transcript is passed as context for each new response.

The key mechanic is interjection: you can insert yourself into the conversation as "The Stranger" at any point. The characters respond to your actual argument and the dialogue continues from there, going wherever the philosophical thread leads.

A web interface provides a reading view for stepping through and interacting with dialogues.

## Corpus

25 dialogues in `corpus/`, full text from the Jowett translation (3rd edition, 1892):

**Early:** Apology, Charmides, Crito, Euthydemus, Euthyphro, Gorgias, Ion, Laches, Lysis, Meno, Protagoras
**Middle:** Cratylus, Phaedo, Phaedrus, Republic, Symposium, Theaetetus, Parmenides
**Late:** Critias, Laws, Philebus, Sophist, Statesman, Timaeus
**Other:** Seventh Letter

Source text is OCR-extracted; some minor artifacts remain.

## Audience

People with a classical education who would notice if Socrates skipped a step.
