#!/usr/bin/env python3
"""Resolve every path and skill name in poteto-mode from the skill folder and report misses."""
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ADAPTER = SKILL_DIR / "../../docs/harness/claude-code.md"
PATH_PREFIXES = ("playbooks/", "references/", "scripts/", "../", "docs/", "skills/")
FENCE = re.compile(r"`{3,}.*")
BACKTICK =re.compile(r"`([^`]+)`")
SKILL_NAME = re.compile(r"\*\*([a-z0-9-]+)\*\*(?= (?:principle )?skill)|\*\*(principle-[a-z0-9-]+)\*\*")


def sources():
    yield SKILL_DIR / "SKILL.md"
    yield from sorted((SKILL_DIR / "playbooks").glob("*.md"))
    yield from sorted((SKILL_DIR / "references").glob("*.md"))


def refs(text):
    text = FENCE.sub("", text)
    for token in BACKTICK.findall(text):
        word = token.split()[0]
        if word.startswith(PATH_PREFIXES) and "<" not in word and "*" not in word:
            yield word
    for bare, prefixed in SKILL_NAME.findall(text):
        yield f"../{bare or prefixed}/SKILL.md"


def main():
    adapter = ADAPTER.read_text()
    misses = []
    for src in sources():
        for ref in refs(src.read_text()):
            name = ref.removeprefix("../").removesuffix("/SKILL.md")
            if f"`{name}`" in adapter:
                continue
            if not (SKILL_DIR / ref).exists():
                misses.append(f"{src.relative_to(SKILL_DIR)}: {ref}")
    for miss in sorted(set(misses)):
        print(f"MISSING {miss}")
    sys.exit(1 if misses else 0)


if __name__ == "__main__":
    main()
