"""Deterministic names are navigation hints, never a claim of semantic identity."""
import re
import unicodedata


def name_key(value: str) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value).strip()).casefold()


def name_keys(title: str, aliases: list[str]) -> list[str]:
    return list(dict.fromkeys(name_key(v) for v in [title, *aliases] if name_key(v)))
