"""Normalize only supplied evidence aliases; numbering has one owner per answer."""
import re
from knowledge.rag.context import citation


class CitationNormalizer:
    def __init__(self, evidence):
        self.allowed = {h['alias']: h for h in evidence}
        self.pending = ''
        self.citations = []
        self.warnings = []
        self._used = set()

    def feed(self, text, *, final=False):
        self.pending += text
        output, added = [], []
        while self.pending:
            index = self.pending.find('[[')
            if index < 0:
                if self.pending.endswith('[') and not final:
                    output.append(self.pending[:-1])
                    self.pending = '['
                else:
                    output.append(self.pending)
                    self.pending = ''
                break
            output.append(self.pending[:index])
            self.pending = self.pending[index:]
            end = self.pending.find(']]', 2)
            if end < 0 and len(self.pending) <= 160 and not final:
                break
            if end < 0:
                # A malformed citation cannot become a clickable pseudo-source.
                self.warnings.append('완성되지 않은 인용 표식을 제거했습니다.')
                self.pending = self.pending[2:]
                continue
            key = self.pending[2:end].strip()
            self.pending = self.pending[end + 2:]
            hit = self.allowed.get(key)
            if hit is None:
                output.append('(출처 확인 불가)')
                self.warnings.append('제공되지 않은 근거의 인용 표식을 제거했습니다.')
                continue
            pid = hit['passageId']
            output.append('[[' + pid + ']]')
            if pid not in self._used:
                value = {**citation(hit), 'number': len(self.citations) + 1}
                self.citations.append(value)
                added.append(value)
                self._used.add(pid)
        self.warnings = list(dict.fromkeys(self.warnings))
        return ''.join(output), added
