"""Source-grounded companions and a single whole-passage context budget."""
import json
import re

_EXPERIMENT = re.compile(r'(?i)experiment|result|measure|specimen|sample|bonding process|실험|시편|측정|결과')
_CONDITIONS = re.compile(r'(?im)materials?\s+(?:and|&)\s+methods|experimental\s+(?:details|methods|setup|procedure)|sample\s+(?:preparation|fabrication)|specimen\s+(?:preparation|fabrication)|시편.{0,12}(?:제작|준비|조건)|실험\s*(?:방법|조건)|^\s*2\.\d+\.\s+.{2,80}')
_CONFLICT_NOTE = re.compile(r'(?i)원문\s*내부.{0,15}차이|불일치|상충|모순|inconsisten(?:t|cy)|contradict(?:ion|ory)|discrepanc(?:y|ies)')
_MEASURED_UNIT = re.compile(r'(?i)(?:sccm|mTorr|°\s*[CF]|[µμ]m|Å\s*/\s*cycle|pJ\s*/\s*bit|\d\s*%|\b(?:nm|MPa|kPa|Pa|mW|W|mV|V)\b)')


def numeric_conflict_note(hit):
    text = hit.get('locator', '') + '\n' + hit.get('text', '')[:1200]
    return bool(_CONFLICT_NOTE.search(text) and _MEASURED_UNIT.search(text))


def experiment_companions(ranked, selected):
    seen_ids = {h['passageId'] for h in selected}
    seen_sources, companions = set(), []
    for hit in selected:
        source = hit.get('lineageKey') or hit.get('sourceRevisionId')
        if not source or source in seen_sources or not _EXPERIMENT.search(hit.get('locator', '') + '\n' + hit.get('text', '')[:1200]):
            continue
        seen_sources.add(source)
        matches = [h for h in ranked if h['passageId'] not in seen_ids
                   and (h.get('lineageKey') or h.get('sourceRevisionId')) == source
                   and _CONDITIONS.search(h.get('locator', '') + '\n' + h.get('text', '')[:1200])]
        if matches:
            item = min(matches, key=lambda h: h.get('documentForm') not in ('original', 'text_extraction'))
            companions.append({**item, 'methods': list(dict.fromkeys([*item.get('methods', []), 'experiment_companion']))})
            seen_ids.add(item['passageId'])
    return companions


def prioritize_conflict_notes(hits):
    return sorted(hits, key=lambda h: not numeric_conflict_note(h))


def conflict_companions(ranked, selected):
    sources = {h.get('lineageKey') or h.get('sourceRevisionId') for h in selected}
    seen, used, result = {h['passageId'] for h in selected}, set(), []
    for hit in ranked:
        source = hit.get('lineageKey') or hit.get('sourceRevisionId')
        if source in sources and source not in used and hit['passageId'] not in seen and numeric_conflict_note(hit):
            result.append({**hit, 'methods': list(dict.fromkeys([*hit.get('methods', []), 'source_discrepancy_note']))})
            used.add(source)
    return result


def prompt_evidence(evidence):
    fields = ('alias', 'passageId', 'sourceRevisionId', 'title', 'locator', 'text',
              'author', 'publisher', 'publishedAt', 'sourceType', 'documentForm', 'readScope', 'sourceKind', 'pageId', 'revisionNumber', 'sourceNote', 'editorId')
    return [{key: hit[key] for key in fields if key in hit} for hit in evidence]


def serialized_evidence(evidence):
    return json.dumps(prompt_evidence(evidence), ensure_ascii=False, separators=(',', ':'))


def select_context(hits, max_characters):
    selected, seen = [], set()
    for hit in hits:
        pid = hit['passageId']
        if pid in seen or not hit.get('text', '').strip():
            continue
        item = {**hit, 'alias': f'C{len(selected) + 1}', 'excerpt': hit['text']}
        # Include metadata/serialization overhead. Never split a condition or table mid-passage.
        if len(serialized_evidence([*selected, item])) > max_characters:
            continue
        selected.append(item)
        seen.add(pid)
    return selected


def citation(hit):
    fields = ('passageId', 'sourceRevisionId', 'documentId', 'title', 'locator', 'excerpt',
              'author', 'publisher', 'publishedAt', 'sourceType', 'documentForm', 'readScope', 'sourceKind', 'pageId', 'revisionNumber', 'sourceNote', 'editorId')
    return {'id': hit['passageId'], **{key: hit[key] for key in fields if key in hit}}
