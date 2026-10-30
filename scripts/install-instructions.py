#!/usr/bin/env python3
"""Install pstack's shared and host rules in always-loaded global instructions."""
import argparse
import os
from pathlib import Path
import re
import stat
import tempfile

SOURCE = Path(__file__).resolve().parents[1]
HOSTS = {
    'codex': {'global': '.codex/AGENTS.md', 'pack': '.codex/pstack-local',
              'adapter': 'codex.md', 'project_skills': '.agents/skills/'},
    'pi': {'global': '.pi/agent/AGENTS.md', 'pack': '.pi/agent/skills/pstack',
           'adapter': 'pi.md', 'project_skills': '.pi/skills/'},
    'claude-code': {'global': '.claude/CLAUDE.md', 'pack': SOURCE, 'pack_env': 'CLAUDE_PLUGIN_ROOT',
                    'adapter': 'claude-code.md', 'project_skills': '.claude/skills/'},
}
BEGIN = '<!-- BEGIN pstack-managed instructions -->'
END = '<!-- END pstack-managed instructions -->'


def render_section(existing: str, content: str):
    """Replace exactly one bounded section, leaving all outside text untouched."""
    markers = list(re.finditer(r'^<!-- (?:BEGIN|END) pstack-managed instructions -->$', existing, re.M))
    if existing.count('pstack-managed') != len(markers):
        raise ValueError('Malformed pstack-managed boundary')
    section = BEGIN + '\n' + content.rstrip() + '\n' + END
    if not markers:
        separator = '' if not existing or existing.endswith('\n\n') else ('\n' if existing.endswith('\n') else '\n\n')
        return existing + separator + section + '\n'
    if len(markers) != 2 or markers[0].group() != BEGIN or markers[1].group() != END:
        raise ValueError('Expected one ordered pstack-managed section')
    return existing[:markers[0].start()] + section + existing[markers[1].end():]


def render_instructions(home: Path, host: str, pack: Path, source=SOURCE):
    config = HOSTS[host]
    parts = []
    for name in ('README.md', config['adapter']):
        _, boundary, text = (source / 'docs/harness' / name).read_text().partition('<!-- pstack:runtime -->')
        if not boundary or not text.strip():
            raise ValueError(f'Missing runtime rules in {name}')
        text = text.strip().replace('<pstack>', str(pack)).replace('<project-skills>', config['project_skills'])
        text = re.sub(r'\]\((?![a-z]+://|#)([^)]+)\)',
                      lambda match: '](' + str(pack / 'docs/harness' / match[1]) + ')', text)
        text = text.replace('$HOME/', str(home) + '/').replace('~/', str(home) + '/')
        parts.append(text.rstrip())
    header = (f'# pstack compatibility rules ({host})\n\nThe installed pack is `{pack}`. '
              'These rules are already loaded. Do not reread adapters for each skill. '
              'Give delegates these rules or the absolute path to this global instruction file. '
              'Include absolute paths to their briefs. Do not assume delegates inherit these rules.\n\n')
    return header + '\n\n'.join(parts)


def validate_target(home: Path, target: Path):
    for path in (home, *(home / Path(*target.relative_to(home).parts[:i])
                          for i in range(1, len(target.relative_to(home).parts) + 1))):
        if path.is_symlink():
            raise ValueError(f'Refusing symlink instruction path: {path}')
        if path.exists() and path != target and not path.is_dir():
            raise ValueError(f'Instruction parent is not a directory: {path}')
    if target.exists() and (not target.is_file() or target.stat().st_nlink != 1):
        raise ValueError(f'Refusing non-regular or hard-linked instruction file: {target}')


def prepare(home: Path, host: str, pack=None, source=SOURCE):
    target = home / HOSTS[host]['global']
    validate_target(home, target)
    existing = target.read_bytes().decode('utf-8') if target.exists() else ''
    config = HOSTS[host]
    installed = pack or Path(os.environ.get(config.get('pack_env', ''), '') or home / config['pack'])
    content = render_instructions(home, host, installed.expanduser().absolute(), source)
    return target, existing, render_section(existing, content)


def publish(prepared, home: Path):
    target, previous, rendered = prepared
    validate_target(home, target)
    current = target.read_bytes().decode('utf-8') if target.exists() else ''
    if current != previous:
        raise ValueError(f'Instruction file changed during install: {target}')
    if current == rendered:
        return
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o600
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.pstack-instructions-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(rendered.encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def install(home: Path, hosts, pack=None):
    prepared = [prepare(home, host, pack) for host in dict.fromkeys(hosts)]
    for item in prepared:
        publish(item, home)
        print(f'Installed instructions in {item[0]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home(), help='Override home for testing')
    parser.add_argument('--host', choices=HOSTS, action='append', required=True, help='Repeat to select multiple hosts')
    parser.add_argument('--pack', type=Path, help='Actual installed pack path (one host only)')
    args = parser.parse_args()
    if args.pack and len(set(args.host)) != 1:
        parser.error('--pack requires exactly one host')
    try:
        install(args.home.expanduser().absolute(), args.host,
                args.pack.expanduser().absolute() if args.pack else None)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Instruction install failed: {error}\n')
