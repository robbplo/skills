#!/usr/bin/env python3
"""Resolve every file path and skill name in every skill from its skill folder and report misses."""
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
CLAUDE_CODE_SKILLS = {"loop", "schedule"}
SAMPLE_DIRS = ("create-verification-skill/references/feature-map-example",)
SKILL_FOLDER_PREFIXES = ("playbooks/", "references/", "scripts/", "assets/", "../", "./")
FENCE = re.compile(r"^[ \t]*`{3,}.*$", re.M)
BACKTICK = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\]\(([^)\s]+)\)")
BOLD = re.compile(r"\*\*([a-z0-9-]+)\*\*")
NAMED_SKILL = re.compile(r"\*\*([a-z0-9-]+)\*\*(?=(?: principle)? skills?\b)")
SLASH = re.compile(r"(?<!no )`/(?:pstack:)?([a-z][a-z0-9-]*)`")


def path_misses(skill_dir, src, target):
    if "<" in target or "*" in target or "://" in target or target.startswith(("#", "/", "mailto:")):
        return
    target = target.split("#")[0]
    if not target:
        return
    if target.startswith(SKILL_FOLDER_PREFIXES):
        if not (skill_dir / target).exists():
            yield f"{target} does not resolve from skills/{skill_dir.name}/"
    elif src.parent != skill_dir and (src.parent / target).exists() and not (skill_dir / target).exists():
        yield f"{target} resolves from {src.parent.relative_to(skill_dir)}/, not from skills/{skill_dir.name}/"


def name_misses(text):
    names = set(NAMED_SKILL.findall(text)) | set(SLASH.findall(text))
    names |= {n for n in BOLD.findall(text) if n.startswith("principle-") or (SKILLS / f"principle-{n}").is_dir()}
    for name in sorted(names):
        if (SKILLS / name / "SKILL.md").exists() or name in CLAUDE_CODE_SKILLS:
            continue
        if (SKILLS / f"principle-{name}").is_dir():
            yield f"**{name}** names no skill; write **principle-{name}**"
        else:
            yield f"{name} names no skill in skills/ and is not in CLAUDE_CODE_SKILLS"


def check(skill_dir, src):
    for lineno, line in enumerate(FENCE.sub("", src.read_text()).splitlines(), 1):
        for token in BACKTICK.findall(line):
            yield from ((lineno, m) for m in path_misses(skill_dir, src, token.split()[0]))
        for target in LINK.findall(line):
            yield from ((lineno, m) for m in path_misses(skill_dir, src, target))
        yield from ((lineno, m) for m in name_misses(line))


def main():
    misses = []
    for skill_dir in sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").exists()):
        for src in sorted(skill_dir.rglob("*.md")):
            if any(src.is_relative_to(SKILLS / d) for d in SAMPLE_DIRS):
                continue
            for lineno, miss in check(skill_dir, src):
                misses.append(f"{src.relative_to(ROOT)}:{lineno}: {miss}")
    misses = list(dict.fromkeys(misses))
    if misses:
        print("\n".join(misses))
    sys.exit(1 if misses else 0)


if __name__ == "__main__":
    main()
