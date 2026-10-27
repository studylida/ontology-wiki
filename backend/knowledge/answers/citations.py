"""Short prompt-only source keys, restored before answer text is persisted."""
from copy import deepcopy
from dataclasses import replace
import re

from ..integrations.providers import ProviderDelta


def citation_aliases(retrieval: dict) -> dict[str, str]:
    identifiers = dict.fromkeys(p.get("id") or p.get("passageId")
                              for p in retrieval.get("grounding", {}).get("passages", []))
    return {f"E{index}": identifier for index, identifier in enumerate(
        (value for value in identifiers if isinstance(value, str) and value), 1)}


def alias_grounding(retrieval: dict) -> dict:
    grounding = deepcopy(retrieval.get("grounding", {}))
    aliases = {identifier: alias for alias, identifier in citation_aliases(retrieval).items()}
    for passage in grounding.get("passages", []):
        alias = aliases.get(passage.get("id") or passage.get("passageId"))
        if alias and passage.get("passageId"):
            aliases.setdefault(passage["passageId"], alias)
    for passage in grounding.get("passages", []):
        identifier = passage.get("id") or passage.get("passageId")
        if identifier in aliases:
            passage["id"] = aliases[identifier]
        passage.pop("passageId", None)
        passage.pop("sourceRevisionId", None)
    for field in ("relations", "sourceViews"):
        for card in grounding.get(field, []):
            card.pop("sourceRevisionId", None)
            for reference in card.get("evidenceRefs", []):
                identifier = reference.get("id") or reference.get("passageId")
                if identifier not in aliases:
                    raise ValueError("Relation evidence is outside the prompt source set")
                reference["id"] = aliases[identifier]
                reference.pop("passageId", None)
                reference.pop("sourceRevisionId", None)
    return grounding


class CitationTextDecoder:
    MAX_BUFFER_BYTES = 2048
    _START = re.compile(r"\[출처\s*:")
    _PARTIAL_START = re.compile(r"\[(?:출(?:처\s*)?)?$")

    def __init__(self, mapping: dict[str, str]):
        self.mapping = dict(mapping)
        self.unknown_references: set[str] = set()
        self._known_ids = set(mapping.values())
        self._pending = ""

    def _restore(self, bracket: str, prefix_length: int) -> str:
        pieces = re.split("([,;])", bracket[prefix_length:-1])
        for index in range(0, len(pieces), 2):
            token = pieces[index]
            identifier = token.strip()
            if identifier in self.mapping:
                leading = len(token) - len(token.lstrip())
                trailing = len(token) - len(token.rstrip())
                pieces[index] = token[:leading] + self.mapping[identifier] + (token[-trailing:] if trailing else "")
            elif identifier and identifier not in self._known_ids:
                self.unknown_references.add(identifier)
        return bracket[:prefix_length] + "".join(pieces) + "]"

    def feed(self, text: str) -> str:
        text, self._pending = self._pending + text, ""
        output, cursor = [], 0
        while match := self._START.search(text, cursor):
            output.append(text[cursor:match.start()])
            end = text.find("]", match.end())
            if end < 0:
                candidate = text[match.start():]
                if len(candidate.encode("utf-8")) <= self.MAX_BUFFER_BYTES:
                    self._pending = candidate
                else:
                    output.append(candidate)
                return "".join(output)
            bracket = text[match.start():end + 1]
            if len(bracket.encode("utf-8")) <= self.MAX_BUFFER_BYTES:
                output.append(self._restore(bracket, match.end() - match.start()))
            else:
                output.append(bracket)
            cursor = end + 1
        tail = text[cursor:]
        partial = self._PARTIAL_START.search(tail)
        if partial and len(partial.group().encode("utf-8")) <= self.MAX_BUFFER_BYTES:
            output.append(tail[:partial.start()])
            self._pending = partial.group()
        else:
            output.append(tail)
        return "".join(output)

    def finish(self) -> str:
        pending, self._pending = self._pending, ""
        return pending


async def decode_citation_deltas(stream, retrieval: dict, *, decoder: CitationTextDecoder | None = None,
                                 cancel_event=None):
    decoder = decoder if decoder is not None else CitationTextDecoder(citation_aliases(retrieval))
    async for delta in stream:
        # Keep observed usage after cancellation without buffering late answer text.
        yield replace(delta, text="" if cancel_event is not None and cancel_event.is_set() else decoder.feed(delta.text))
    pending = decoder.finish()
    if pending:
        yield ProviderDelta(text=pending)
