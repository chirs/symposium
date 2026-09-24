"""symposium: step through a Platonic dialogue, interject, revert."""

from __future__ import annotations

import argparse
import shutil
import sys
import textwrap
from pathlib import Path

from symposium.dialogue import Dialogue, Exchange
from symposium.generate import GenerationError, generate
from symposium.script import DIALOGUES, Script

WIDTH = 88


def render(e: Exchange) -> str:
    if e.is_stage:
        return textwrap.fill(f"[{e.text}]", WIDTH) + "\n"
    paragraphs = [textwrap.fill(p, WIDTH) for p in e.text.split("\n\n")]
    return f"{e.speaker}\n" + "\n\n".join(paragraphs) + "\n"


def resolve_script(path: Path, name: str | None) -> Script:
    if name:
        return Script.named(name)
    local = path.parent / "script.json"
    if local.exists():
        return Script.load(local)
    sys.exit(f"cannot find script.json next to {path}; pass --dialogue NAME")


def step(dialogue: Dialogue, script: Script, speaker: str | None, out) -> Exchange:
    speaker = speaker or script.next_speaker(dialogue)
    print(speaker.upper(), file=out)
    text = generate(
        dialogue, speaker, script, on_text=lambda t: print(t, end="", file=out, flush=True)
    )
    print("\n", file=out)
    return dialogue.append(speaker, text)


def cmd_new(args) -> None:
    seed = DIALOGUES / args.name / "seed.md"
    if not seed.exists():
        sys.exit(f"no such dialogue: {args.name} (looked for {seed})")
    out = Path(args.out) if args.out else seed.with_name("run.md")
    if out.exists() and not args.force:
        sys.exit(f"{out} exists; pass --force to overwrite")
    shutil.copy(seed, out)
    print(out)


def cmd_show(args) -> None:
    d = Dialogue.load(Path(args.file))
    for e in d.exchanges:
        print(render(e))
    if d.has_original:
        print("(diverged from the original; `symposium revert` returns to it)")


def cmd_next(args) -> None:
    path = Path(args.file)
    d = Dialogue.load(path)
    script = resolve_script(path, args.dialogue)
    for _ in range(args.count):
        step(d, script, args.speaker, sys.stdout)
        d.save(path)


def cmd_interject(args) -> None:
    path = Path(args.file)
    d = Dialogue.load(path)
    at = args.at if args.at is not None else len(d.exchanges)
    dropped = len(d.exchanges) - at
    d.interject(args.text, at=at)
    d.save(path)
    print(f"interjected after exchange {at}; {dropped} discarded")


def cmd_revert(args) -> None:
    path = Path(args.file)
    d = Dialogue.load(path)
    try:
        d.revert()
    except ValueError as err:
        sys.exit(str(err))
    d.save(path)
    print(f"restored original ({len(d.exchanges)} exchanges)")


HELP = """Enter      show the next exchange, or generate it if there are no more
text       speak as The Stranger at this point; what follows is discarded
/end       jump to the last exchange
/revert    return to the original path
/quit      leave"""


def cmd_run(args) -> None:
    path = Path(args.file)
    d = Dialogue.load(path)
    script = resolve_script(path, args.dialogue)
    cursor = 0
    print(f"{script.title}\n{HELP}\n")
    while True:
        try:
            line = input(f"[{cursor}/{len(d.exchanges)}] ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line == "/quit":
            return
        if line == "/end":
            for e in d.exchanges[cursor:]:
                print(render(e))
            cursor = len(d.exchanges)
        elif line == "/revert":
            try:
                d.revert()
            except ValueError as err:
                print(err)
                continue
            d.save(path)
            cursor = min(cursor, len(d.exchanges))
            print("returned to the original path\n")
        elif line:
            d.interject(line, at=cursor)
            d.save(path)
            print(render(d.exchanges[-1]))
            cursor = len(d.exchanges)
        elif cursor < len(d.exchanges):
            print(render(d.exchanges[cursor]))
            cursor += 1
        else:
            try:
                step(d, script, None, sys.stdout)
            except GenerationError as err:
                print(err)
                continue
            d.save(path)
            cursor = len(d.exchanges)


def cmd_serve(args) -> None:
    import uvicorn

    from symposium.server import build_app

    uvicorn.run(build_app(), host=args.host, port=args.port)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="symposium", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("new", help="start a working copy of a dialogue's seed")
    s.add_argument("name")
    s.add_argument("out", nargs="?")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_new)

    s = sub.add_parser("show", help="print the dialogue")
    s.add_argument("file")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("next", help="generate the next exchange(s)")
    s.add_argument("file")
    s.add_argument("-n", "--count", type=int, default=1)
    s.add_argument("--speaker", help="override the scripted speaker")
    s.add_argument("--dialogue", help="script name if not next to FILE")
    s.set_defaults(func=cmd_next)

    s = sub.add_parser("interject", help="speak as The Stranger; discard what follows")
    s.add_argument("file")
    s.add_argument("text")
    s.add_argument("--at", type=int, help="insert after this many exchanges (default: end)")
    s.set_defaults(func=cmd_interject)

    s = sub.add_parser("revert", help="return to the pre-interjection path")
    s.add_argument("file")
    s.set_defaults(func=cmd_revert)

    s = sub.add_parser("run", help="step through interactively")
    s.add_argument("file")
    s.add_argument("--dialogue")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("serve", help="serve the reading view in a browser")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    s.set_defaults(func=cmd_serve)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except GenerationError as err:
        sys.exit(str(err))


if __name__ == "__main__":
    main()
