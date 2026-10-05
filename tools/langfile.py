"""Read and write exact and reference-wildcard Yakumo translation files."""

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

MAX_BYTES = 16 * 1024 * 1024
MAX_LINE = 64 * 1024
Key = tuple[int, int, int | str]
CODE = re.compile(r'[A-Za-z0-9_-]{1,64}')
TOKENS = re.compile(r'~[A-Za-z]\d{1,2}|%(?:%|(?:\d+\$)?[-+ #0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|ll|[hljztL])?[diuoxXfFeEgGaAcspn])|[\n\r\t]')
ESCAPES = {'n': '\n', 'r': '\r', 't': '\t', '\\': '\\', '#': '#', ';': ';'}


@dataclass
class Language:
    code: str
    name: str
    rows: dict[Key, str]


def identity(text: str) -> Key:
    """Parse an entry:table:index identity; only the index may be a wildcard."""
    if not re.fullmatch(r'\d+:\d+:(?:\d+|\*)', text):
        raise ValueError('Only exact numeric keys and reference wildcards are supported')
    entry_text, table_text, index_text = text.split(':')
    entry, table = int(entry_text), int(table_text)
    index = '*' if index_text == '*' else int(index_text)
    if entry > 0xFFFFFFFF or table > 65535 or (index != '*' and index > 0xFFFFFFFF):
        raise ValueError('Translation key exceeds the format limits')
    return entry, table, index


def row_order(key: Key) -> tuple[int, int, int]:
    return key[0], key[1], -1 if key[2] == '*' else key[2]


def unescape(value: str) -> str:
    result = []
    index = 0
    while index < len(value):
        if value[index] == '\\' and index + 1 < len(value) and value[index + 1] in ESCAPES:
            result.append(ESCAPES[value[index + 1]])
            index += 2
        else:
            result.append(value[index])
            index += 1
    return ''.join(result)


def escape(value: str) -> str:
    for old, new in [('\\', '\\\\'), ('\n', '\\n'), ('\r', '\\r'), ('\t', '\\t'), ('#', '\\#'), (';', '\\;')]:
        value = value.replace(old, new)
    return value


def loads(text: str) -> Language:
    if '\0' in text or len(text.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Invalid translation size or NUL character')
    code, name, entry = '', '', 16
    rows = {}
    for number, line in enumerate(text.lstrip('\ufeff').split('\n'), 1):
        line = line.rstrip('\r')
        if len(line.encode('utf-8')) > MAX_LINE:
            raise ValueError(f'Line {number} exceeds the input limit')
        body = line.lstrip(' \t')
        if not body or body.startswith(('#', ';')):
            continue
        if re.fullmatch(r'\[\d+\]', body):
            entry = int(body[1:-1])
            if entry > 0xFFFFFFFF:
                raise ValueError(f'Invalid section at line {number}')
            continue
        key, equal, value = body.partition('=')
        if not equal:
            raise ValueError(f'Invalid line {number}')
        key = key.strip()
        if value.startswith((' ', '\t')):
            value = value[1:]
        value = unescape(value)
        if key in ('language', 'name'):
            if key == 'language':
                code = value
            else:
                name = value
            continue
        row = identity(f'{entry}:{key}')
        if row in rows:
            raise ValueError(f'Invalid or duplicate key at line {number}')
        rows[row] = value
    if not CODE.fullmatch(code) or not name:
        raise ValueError('A valid language code and name are required')
    return Language(code, name, rows)


def read(path: Path) -> Language:
    with path.open('rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Translation exceeds 16 MiB')
    return loads(raw.decode('utf-8-sig'))


def write(path: Path, language: Language) -> None:
    lines = ['# Work in progress. Missing keys fall back to the installed game text.',
             f'language = {escape(language.code)}', f'name = {escape(language.name)}']
    previous = None
    for (entry, table, index), value in sorted(language.rows.items(), key=lambda item: row_order(item[0])):
        if entry != previous:
            lines.extend(['', f'[{entry}]'])
            previous = entry
        lines.append(f'{table}:{index} = {escape(value)}')
    text = '\n'.join(lines) + '\n'
    parsed = loads(text)
    if parsed != language:
        raise ValueError('Translation serialization did not round-trip')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.lang-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate(source: Language, target: Language, code: str = 'ru') -> list[str]:
    errors = []
    if target.code != code:
        errors.append(f'Target language must be {code}')
    for key, value in target.rows.items():
        if key not in source.rows:
            errors.append(f'Unknown source key {key}')
        elif not value or '\0' in value:
            errors.append(f'Empty or invalid translation {key}')
        elif TOKENS.findall(source.rows[key]) != TOKENS.findall(value):
            errors.append(f'Formatting tokens or line breaks changed at {key}')
    return errors
