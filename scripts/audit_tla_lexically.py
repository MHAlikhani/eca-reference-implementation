#!/usr/bin/env python3
"""Small lexical sanity check; it is NOT a TLA+ parser or model checker."""
from __future__ import annotations
import sys
from pathlib import Path

pairs = {')': '(', ']': '[', '}': '{'}

def strip_comments(text: str) -> str:
    out = []
    i = 0
    depth = 0
    while i < len(text):
        if text.startswith('(*', i):
            depth += 1
            i += 2
        elif depth and text.startswith('*)', i):
            depth -= 1
            i += 2
        elif depth:
            i += 1
        else:
            out.append(text[i])
            i += 1
    if depth:
        raise ValueError('unterminated nested comment')
    return ''.join(out)

def audit(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    plain = strip_comments(text)
    stack = []
    in_string = False
    escaped = False
    for pos, ch in enumerate(plain):
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in '([{':
            stack.append((ch, pos))
        elif ch in ')]}':
            if not stack or stack[-1][0] != pairs[ch]:
                raise ValueError(f'unbalanced delimiter {ch!r} at offset {pos}')
            stack.pop()
    if in_string:
        raise ValueError('unterminated string literal')
    if stack:
        raise ValueError(f'unclosed delimiter(s): {stack[-3:]}')
    header = f'MODULE {path.stem}'
    if header not in plain:
        raise ValueError(f'module header does not match filename: expected {header}')
    if not plain.rstrip().endswith('=') and not plain.rstrip().endswith('====='):
        raise ValueError('module terminator is missing')
    for token in ('Init ==', 'Next ==', 'Spec ==', 'TypeOK =='):
        if token not in plain:
            raise ValueError(f'missing required definition: {token}')
    import re
    header_match = re.search(r'VARIABLES\s+([\s\S]*?)\n\nvars', plain)
    if not header_match:
        raise ValueError('could not identify VARIABLE declarations')
    variables = [line.strip().rstrip(',') for line in header_match.group(1).splitlines() if line.strip()]
    action_text = plain[plain.index('Reserve =='):plain.index('Next ==')]
    action_parts = re.split(r'\n(?=[A-Z][A-Za-z0-9]* ==\n)', action_text)
    variable_pattern = r'(?:' + '|'.join(re.escape(name) for name in variables) + r')'
    for action in action_parts:
        action_name = action.split(' ==', 1)[0].splitlines()[0]
        changed = set(re.findall(r'/\\\s*(' + variable_pattern + r")'\s*=", action))
        unchanged = set()
        for tuple_text in re.findall(r'UNCHANGED\s*<<([\s\S]*?)>>', action):
            unchanged.update(re.findall(r'\b' + variable_pattern + r'\b', tuple_text))
        missing = set(variables) - changed - unchanged
        if missing:
            raise ValueError(f'action {action_name} has missing frame conditions for: {sorted(missing)}')
    print(f'PASS lexical and action-frame sanity: {path}')
    print('LIMIT: this check does not establish TLA+ grammar validity, semantic correctness, or model-checking results.')

if __name__ == '__main__':
    try:
        audit(Path(sys.argv[1]))
    except Exception as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
