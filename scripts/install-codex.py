#!/usr/bin/env python3
"""Install an adapted local copy without modifying upstream skills or host config."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

SOURCE = Path(__file__).resolve().parents[1]
MARKER = '.pstack-local-install'


def skill_frontmatter(path: Path):
    text = path.read_text()
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise ValueError(f'Invalid skill frontmatter: {path}')
    front, body = text[4:].split('\n---\n', 1)
    lines = front.splitlines()
    for key in ('name', 'description'):
        fields = [(i, line[len(key) + 1:].strip()) for i, line in enumerate(lines) if line.startswith(f'{key}:')]
        if len(fields) != 1:
            raise ValueError(f'Skill requires one {key}: {path}')
        index, value = fields[0]
        if value in ('>', '>-', '>+', '|', '|-', '|+'):
            continuation = []
            for line in lines[index + 1:]:
                if line and not line.startswith(' '):
                    break
                continuation.append(line.strip())
            value = '\n'.join(continuation).strip()
        elif value.startswith('"'):
            value = json.loads(value)
        elif value.startswith("'"):
            if not re.fullmatch(r"'(?:[^']|'')*'", value):
                raise ValueError(f'Invalid {key} string: {path}')
            value = value[1:-1].replace("''", "'")
        elif re.search(r':\s|^[\[\]{},&*!#%@`]|^(?:null|true|false|~|[-+]?\d+(?:\.\d+)?)$', value, re.I):
            raise ValueError(f'Skill {key} must be a string: {path}')
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'Skill requires a nonempty {key}: {path}')
        if key == 'name' and (value != path.parent.name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value)):
            raise ValueError(f'Skill name must match its directory: {path}')
    return front, body


def render_pack(stage: Path, pack: Path):
    skills = sorted((SOURCE / 'skills').glob('*/SKILL.md'))
    if not skills:
        raise ValueError(f'No skills found in {SOURCE}')
    parsed = {skill.parent.name: skill_frontmatter(skill) for skill in skills}
    for folder in ('skills', 'agents', 'docs', 'assets'):
        shutil.copytree(SOURCE / folder, stage / folder)
    shutil.copy2(SOURCE / 'README.md', stage / 'README.md')
    for adapter_name in ('README.md', 'codex.md', 'pi.md', 'claude-code.md'):
        if not (stage / 'docs/harness' / adapter_name).is_file():
            raise ValueError(f'Missing host contract or adapter: {adapter_name}')
    if (pack / 'models.md').is_file():
        shutil.copy2(pack / 'models.md', stage / 'models.md')
    (stage / MARKER).write_text(f'Source: {SOURCE}\n')
    adapter = pack / 'docs/harness/codex.md'
    prelude = (f'## Host instructions\n\nBefore doing any work, read `{pack / "docs/harness/README.md"}` '
               'and select the active host adapter. This shared catalog may be loaded by Codex or Pi. '
               f'Only in Codex, read `{adapter}` and `{pack / "models.md"}` if present. '
               'Pass the contract and selected adapter paths to every delegate.\n\n')
    for name, (front, body) in parsed.items():
        explicit_only = 'disable-model-invocation: true' in front
        front = '\n'.join(line for line in front.splitlines() if not line.startswith(
            ('user-invocable:', 'icon:', 'color:')))
        dest = stage / 'skills' / name / 'SKILL.md'
        dest.write_text('---\n' + front + '\n---\n\n' + prelude + body.lstrip())
        if explicit_only:
            metadata = dest.parent / 'agents' / 'openai.yaml'
            metadata.parent.mkdir(exist_ok=True)
            metadata.write_text('policy:\n  allow_implicit_invocation: false\n')
    return set(parsed)


def owned_link(link: Path, pack: Path):
    return link.is_symlink() and Path(os.path.abspath(link.parent / os.readlink(link))) == pack / 'skills' / link.name


def restore_links(catalog: Path, pack: Path, previous):
    catalog.mkdir(parents=True, exist_ok=True)
    for name in previous:
        link = catalog / name
        if os.path.lexists(link) and not owned_link(link, pack):
            raise ValueError(f'Refusing to overwrite existing skill during recovery: {link}')
    for link in catalog.iterdir():
        if owned_link(link, pack) and link.name not in previous:
            link.unlink()
    for name, target in previous.items():
        link = catalog / name
        if not os.path.lexists(link):
            link.symlink_to(target, target_is_directory=True)


def retire_transaction(transaction: Path):
    with tempfile.TemporaryDirectory(prefix='.pstack-local-discard-', dir=transaction.parent) as directory:
        transaction.rename(Path(directory) / 'transaction')


def recover(transaction: Path, pack: Path, catalog: Path):
    if not os.path.lexists(transaction):
        return
    if transaction.is_symlink() or not (transaction / MARKER).is_file():
        raise ValueError(f'Refusing unrelated transaction path: {transaction}')
    if not (transaction / 'committed').exists():
        state = json.loads((transaction / 'state.json').read_text())
        previous = transaction / 'previous'
        if previous.exists() or not state['had_pack']:
            if os.path.lexists(pack):
                if pack.is_symlink() or not (pack / MARKER).is_file():
                    raise ValueError(f'Refusing unrelated pack during recovery: {pack}')
                pack.rename(transaction / 'discarded')
            if previous.exists():
                previous.rename(pack)
        restore_links(catalog, pack, state['links'])
    retire_transaction(transaction)


def install(home: Path):
    pack = home / '.codex' / 'pstack-local'
    catalog = home / '.agents' / 'skills'
    transaction = pack.parent / '.pstack-local-transaction'
    pack.parent.mkdir(parents=True, exist_ok=True)
    with (pack.parent / '.pstack-local-install.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        recover(transaction, pack, catalog)
        if pack.is_symlink() or (pack.exists() and not (pack / MARKER).is_file()):
            raise ValueError(f'Refusing to overwrite unrelated path: {pack}')
        with tempfile.TemporaryDirectory(prefix='.pstack-local-stage-', dir=pack.parent) as directory:
            stage = Path(directory)
            names = render_pack(stage / 'pack', pack)
            for name in names:
                link = catalog / name
                if os.path.lexists(link) and not owned_link(link, pack):
                    raise ValueError(f'Refusing to overwrite existing skill: {link}')
            links = {link.name: os.readlink(link) for link in catalog.iterdir() if owned_link(link, pack)} if catalog.exists() else {}
            (stage / 'state.json').write_text(json.dumps({'had_pack': pack.exists(), 'links': links}))
            (stage / MARKER).write_text(f'Transaction source: {SOURCE}\n')
            stage.rename(transaction)
        try:
            if pack.exists():
                pack.rename(transaction / 'previous')
            (transaction / 'pack').rename(pack)
            catalog.mkdir(parents=True, exist_ok=True)
            for name in links.keys() - names:
                (catalog / name).unlink()
            for name in sorted(names):
                link = catalog / name
                if not os.path.lexists(link):
                    link.symlink_to(pack / 'skills' / name, target_is_directory=True)
            (transaction / 'committed').touch()
        except BaseException:
            recover(transaction, pack, catalog)
            raise
        retire_transaction(transaction)
    print(f'Installed {len(names)} skills in {pack}; linked from {catalog}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home(), help='Override home for testing')
    try:
        install(parser.parse_args().home.expanduser().resolve())
    except (OSError, ValueError) as error:
        parser.exit(1, f'Install failed: {error}\n')
