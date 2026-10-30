"""Helpers that edit SNBT strings without rebuilding their surrounding syntax."""

import re


_TOKENS = re.compile(
    r'''(?P<string>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')'''
    r'|(?P<comment>//[^\r\n]*|\#[^\r\n]*|/\*[\s\S]*?\*/)'
    r'|(?P<lore>\bLore\s*:\s*\[)'
    r'|(?P<bracket>[\[\]{}])'
)


def translate_lore_content(content, lang_to, translate):
    """Translate plain Lore entries, preserving JSON components and formatting.

    Tokenize quoted strings before looking for brackets or field names: both
    may occur inside JSON text components, and quotes may be escaped in SNBT.
    Only direct string entries in a Lore list are eligible for translation.
    """
    depth = 0
    replacements = []
    for token in _TOKENS.finditer(content):
        if token.lastgroup == 'comment':
            continue
        if token.lastgroup == 'lore':
            if depth:
                depth += 1
            else:
                depth = 1
        elif depth and token.lastgroup == 'bracket':
            depth += 1 if token.group() in '[{' else -1
        elif depth == 1 and token.lastgroup == 'string':
            literal = token.group()
            quote = literal[0]
            text = re.sub(r'\\([\\\'\"])', r'\1', literal[1:-1])
            stripped = text.strip()
            if (not stripped or stripped.startswith(('{', '[')) or
                    stripped.endswith('}') or '(Part of the' in text or
                    text.startswith((' 8', ' 7', ' e('))):
                continue
            translated = translate(text, lang_to)
            if translated != text:
                escaped = translated.replace('\\', '\\\\').replace(quote, '\\' + quote)
                replacements.append((token.start(), token.end(), quote + escaped + quote))

    # Keep every byte outside changed string literals, including separators.
    for start, end, replacement in reversed(replacements):
        content = content[:start] + replacement + content[end:]
    return content
