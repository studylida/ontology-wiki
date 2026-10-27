"""Offline, loss-aware preparation of preserved Markdown and Docling extractions."""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET

from knowledge.documents.parsing import prepared_passages


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def normalized(text: str) -> str:
    return re.sub(r"\s", "", text)


def markdown_blocks(text: str) -> tuple[list[dict], list[dict]]:
    """Keep paragraphs, fenced code and tables whole; classify only explicit notes."""
    front = re.match(r"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", text, re.S)
    lines = list(re.finditer(r"[^\n]*(?:\n|$)", text))
    blocks, notes, stack = [], [], []
    position, note_level = front.end() if front else 0, None
    i = next((i for i, line in enumerate(lines) if line.start() >= position), len(lines))
    while i < len(lines):
        line = lines[i].group().rstrip("\r\n")
        if not line.strip():
            i += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)", line)
        if heading:
            level, name = len(heading[1]), heading[2].strip()
            stack = [(n, h) for n, h in stack if n < level] + [(level, name)]
            if note_level is not None and level <= note_level:
                note_level = None
            if name in {"원문·편집 계보", "편집 기록", "검토 메모", "전처리 검수 기록"}:
                note_level = level
        begin, j = lines[i].start(), i + 1
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            while j < len(lines):
                if re.match(r"^\s*" + re.escape(fence[1][0]) + "{" + str(len(fence[1])) + r",}\s*$", lines[j].group().strip()):
                    j += 1
                    break
                j += 1
        elif not heading:
            while j < len(lines):
                following = lines[j].group().strip()
                if not following or re.match(r"^#{1,6}\s|^(`{3,}|~{3,})", following):
                    break
                j += 1
        end = lines[j - 1].end()
        raw = text[begin:end]
        value = raw.strip()
        offset = begin + len(raw) - len(raw.lstrip())
        block = {"text": value, "locator": " > ".join(h for _, h in stack) or "본문",
                 "inputStart": offset, "inputEnd": offset + len(value),
                 "kind": "heading" if heading else "table" if re.search(r"^\s*\|?\s*:?-{3,}", value, re.M) else "paragraph"}
        if note_level is not None:
            notes.append({**block, "reason": "explicit_editorial_section"})
        elif value in {"공유하기", "인쇄하기", "URL 복사", "페이스북 공유", "트위터 공유"}:
            notes.append({**block, "reason": "standalone_navigation_control"})
        else:
            blocks.append(block)
        i = j
    return blocks, notes


def group_markdown(blocks: list[dict], maximum: int = 1400) -> list[dict]:
    chunks, pending = [], []
    for block in blocks:
        if pending and (block["kind"] == "heading" or block["locator"] != pending[-1]["locator"]
                        or sum(len(b["text"]) + 2 for b in pending) + len(block["text"]) > maximum):
            chunks.append(pending)
            pending = []
        pending.append(block)
    if pending:
        chunks.append(pending)
    return [{"text": "\n\n".join(b["text"] for b in chunk), "locator": chunk[0]["locator"],
             "sourceSpans": [{"start": b["inputStart"], "end": b["inputEnd"]} for b in chunk],
             "kinds": list(dict.fromkeys(b["kind"] for b in chunk))} for chunk in chunks]


def xml_nodes(raw: bytes):
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("XML input exceeds 5 MiB")
    # Decode first so UTF-16 declarations cannot evade the entity check.
    decoded = raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    if re.search(r"<!ENTITY\s", decoded, re.I):
        raise ValueError("XML entities are not accepted")
    root = ET.fromstring(raw)
    nodes = []

    def visit(node, path):
        nodes.append((node, path))
        counts = {}
        for child in node:
            tag = child.tag.rsplit("}", 1)[-1]
            counts[tag] = counts.get(tag, 0) + 1
            visit(child, path + f"/*[local-name()='{tag}'][{counts[tag]}]")

    visit(root, f"/*[local-name()='{root.tag.rsplit('}', 1)[-1]}'][1]")
    return nodes


SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
SUB.update(str.maketrans("aehijklmnoprstuvx", "ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"))
SUP = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")


def script_text(value: str, superscript: bool = False) -> str:
    alphabet = SUP if superscript else SUB
    if all(ord(char) in alphabet for char in value):
        return value.translate(alphabet)
    return ("^{" if superscript else "_{") + value + "}"


def xml_text(node, *, omit_math=False, in_math=False):
    tag = node.tag.rsplit("}", 1)[-1]
    if omit_math and tag in {"math", "tex-math"}:
        return ""
    in_math = in_math or tag == "math" or node.tag.startswith("{http://www.w3.org/1998/Math/MathML}")
    if in_math and tag not in {"math", "mrow", "mi", "mn", "mo", "mtext", "msub", "msup"}:
        raise ValueError("Caption math requires manual review")
    children = [xml_text(c, omit_math=omit_math, in_math=in_math) for c in node]
    if tag in {"msub", "msup"}:
        if len(children) != 2 or (node.text or "").strip() or any((child.tail or "").strip() for child in node):
            raise ValueError("Caption math requires manual review")
        return children[0] + script_text(children[1], superscript=tag == "msup")
    if tag in {"math", "mrow", "mi", "mn", "mo", "mtext", "msub", "msup"}:
        return (node.text or "") + "".join(value + (child.tail or "") for value, child in zip(children, node))
    if tag in {"semantics", "mfrac", "msqrt", "msubsup", "mtable", "mover", "munder"}:
        raise ValueError("Caption math requires manual review")
    value = (node.text or "") + "".join(value + (child.tail or "") for value, child in zip(children, node))
    return script_text(value, superscript=tag == "sup") if tag in {"sub", "sup"} else value


def table_reprocessing_candidates(result: dict) -> list[dict]:
    """Flag numeric rows packed into one cell; conversion success is not approval."""
    number = re.compile(r"(?<![\w.])[−+-]?\d+(?:\.\d+)?(?:\s*±\s*[−+-]?\d+(?:\.\d+)?)?(?![\w.])")
    candidates = []
    for table in result["structuredDocument"].get("tables", []):
        if not isinstance(table.get("data", {}).get("table_cells"), list) or not table["data"]["table_cells"]:
            candidates.append({"documentRef": table.get("self_ref", ""),
                "pageNumbers": sorted({p["page_no"] for p in table.get("prov", [])}),
                "reason": "table_structure_missing", "status": "needs_targeted_reextraction_and_source_comparison"})
            continue
        suspicious_rows = set()
        for cell in table.get("data", {}).get("table_cells", []):
            text = cell["text"]
            if cell.get("column_header") or cell.get("row_span", 1) != 1:
                continue
            # A real list/condition cell containing words is left for normal review.
            if len(number.findall(text)) >= 3 and not number.sub("", text).strip(" \n\r\t/%–−-+"):
                suspicious_rows.add(cell["start_row_offset_idx"])
        if len(suspicious_rows) >= 2:
            candidates.append({"documentRef": table["self_ref"],
                "pageNumbers": sorted({p["page_no"] for p in table.get("prov", [])}),
                "reason": "multiple_numeric_columns_packed_into_single_cell",
                "rows": sorted(suspicious_rows), "status": "needs_targeted_reextraction_and_source_comparison"})
    return candidates


def repair_jats(result: dict, raw: bytes) -> tuple[dict, list[dict], list[dict]]:
    """Repair only uniquely matched captions; link raw IDs/xrefs without guessing."""
    result = copy.deepcopy(result)
    nodes, edits, unresolved = xml_nodes(raw), [], []
    document = result["structuredDocument"]
    captions = [x for x in document["texts"] if x["label"] == "caption"]
    originals = []
    for node, path in nodes:
        if node.tag.rsplit("}", 1)[-1] not in {"fig", "table-wrap"}:
            continue
        caption = next((c for c in node if c.tag.rsplit("}", 1)[-1] == "caption"), None)
        label = next((c for c in node if c.tag.rsplit("}", 1)[-1] == "label"), None)
        if caption is None:
            continue
        try:
            prefix = "" if label is None else xml_text(label).strip() + " "
            full, without = prefix + xml_text(caption).strip(), prefix + xml_text(caption, omit_math=True).strip()
        except ValueError:
            unresolved.append({"xmlId": node.get("id"), "xpath": path, "reason": "complex_caption_math_preserved_in_original"})
            continue
        originals.append((node, path, full, without))
    for node, path, full, without in originals:
        matches = [c for c in captions if normalized(c["text"]) in {normalized(full), normalized(without)}]
        if len(matches) != 1 or sum(normalized(matches[0]["text"]) in {normalized(other_full), normalized(other_without)}
                                    for _, _, other_full, other_without in originals) != 1:
            unresolved.append({"xmlId": node.get("id"), "xpath": path, "reason": "caption_not_uniquely_matched"})
            continue
        item = matches[0]
        item["rawXmlLocation"] = {"xmlId": node.get("id"), "xpath": path}
        if normalized(item["text"]) != normalized(full):
            old = item["text"]
            targets = [passage for passage, source in zip(result["preparedPassages"], result["sourceMap"], strict=True)
                       if item["self_ref"] in source["documentRefs"] and old in passage["text"]]
            if targets and all(passage["text"].count(old) == 1 for passage in targets):
                for passage in targets:
                    passage["text"] = passage["text"].replace(old, full, 1)
                edits.append({"type": "extraction_caption_repair", "before": old, "after": full,
                              "xmlId": node.get("id"), "xpath": path, "documentRef": item["self_ref"]})
                item["text"] = full
            else:
                unresolved.append({"xmlId": node.get("id"), "xpath": path, "reason": "caption_not_found_in_passages"})
    return result, edits, unresolved


def apply_table_repairs(result: dict, repairs: list[dict]) -> tuple[dict, list[dict]]:
    result = copy.deepcopy(result)
    edits = []
    for repair in repairs:
        ref = repair["documentRef"]
        table = next(t for t in result["structuredDocument"]["tables"] if t["self_ref"] == ref)
        if sha(json.dumps(table, sort_keys=True, ensure_ascii=False).encode()) != repair["tableSha256"]:
            raise ValueError("Reviewed table changed")
        expected = repair["beforeRows"]
        rows, columns = repair["rows"], repair["columns"]
        if len(rows) != len(expected) or any(len(row) != len(columns) for row in rows):
            raise ValueError("Table dimensions differ from review")
        compact = lambda value: re.sub(r"\s", "", unicodedata.normalize("NFKC", value))
        if any(compact(" ".join(new)) != compact(old) for new, old in zip(rows, expected)):
            raise ValueError("Table repair changes cell values")
        found = []
        for passage, source in zip(result["preparedPassages"], result["sourceMap"]):
            if ref not in source["documentRefs"]:
                continue
            if any(r.startswith("#/tables/") and r != ref for r in source["documentRefs"]):
                raise ValueError("Multiple tables in one passage require review")
            selected = []
            for line in passage["text"].splitlines():
                if not line.strip().startswith("|"):
                    continue
                if re.fullmatch(r"[\s|:\-]+", line):
                    continue
                if line in repair.get("beforeHeaderLines", []):
                    continue
                cell_text = " ".join(cell.strip() for cell in line.strip().strip("|").split("|") if cell.strip())
                matches = [i for i, old in enumerate(expected) if compact(cell_text) == compact(old)]
                if len(matches) != 1:
                    raise ValueError("Unreviewed or ambiguous table row")
                selected.append(rows[matches[0]])
            if not selected:
                raise ValueError("Reviewed table rows are not in extraction")
            found.extend(selected)
            lines = passage["text"].splitlines()
            table_lines = [i for i, line in enumerate(lines) if line.strip().startswith("|")]
            if any(lines[i].strip() and not lines[i].strip().startswith("|") for i in range(min(table_lines), max(table_lines))):
                raise ValueError("Noncontiguous table requires review")
            before, after = "\n".join(lines[:min(table_lines)]), "\n".join(lines[max(table_lines) + 1:])
            if repair["caption"] not in before:
                before += "\n\n" + repair["caption"]
            passage["text"] = before.rstrip() + "\n\n" + "\n".join([
                "| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |",
                *("| " + " | ".join(row) + " |" for row in selected)]) + ("\n\n" + after if after else "")
        if found != rows:
            raise ValueError("Table repair would omit or reorder rows")
        edits.append({"type": "extraction_table_columns_and_repeated_caption", **repair})
    return result, edits


def docling_blocks(result: dict) -> list[dict]:
    blocks = []
    for passage, source in zip(result["preparedPassages"], result["sourceMap"], strict=True):
        blocks.append({"text": passage["text"], "locator": source["locator"],
                       "sourceSpans": [{"start": source["startOffset"], "end": source["endOffset"]}],
                       "documentRefs": source["documentRefs"], "pageNumbers": source["pageNumbers"],
                       "provenance": source["provenance"], "kinds": source["label"].split(",")})
    return blocks


def link_xml(blocks: list[dict], result: dict, raw: bytes) -> dict:
    nodes = xml_nodes(raw)
    # Location matching must retain numeric signs, decimal points and units.
    location_text = lambda text: re.sub(r"\s", "", text)
    searchable = [location_text(b["text"]) for b in blocks]
    paragraphs = [n for n, _ in nodes if n.tag.rsplit("}", 1)[-1] == "p"]
    paragraph_texts = [location_text("".join(n.itertext())) for n in paragraphs]
    formulas = result.get("metadata", {}).get("mathmlNotationHashes", [])
    formula_hash_counts = Counter(item["sha256"] for item in formulas)
    formula_ids = Counter(n.get("id") for n, _ in nodes if n.tag.rsplit("}", 1)[-1] == "math" and n.get("id"))
    formula_by_id = {item["xmlId"]: item for item in formulas if item.get("xmlId") and
                     item.get("length", 0) >= 40 and formula_ids[item["xmlId"]] == 1 and formula_hash_counts[item["sha256"]] == 1}
    formula_blocks = {}
    for i, block in enumerate(blocks):
        for notation in re.findall(r"\$\$(.*?)\$\$", block["text"], re.S):
            formula_blocks.setdefault(sha(notation.strip().encode()), set()).add(i)
    paths = {id(node): path for node, path in nodes}
    caption_refs = {}
    for node, path in nodes:
        if node.tag.rsplit("}", 1)[-1] not in {"fig", "table-wrap"}:
            continue
        caption = next((c for c in node if c.tag.rsplit("}", 1)[-1] == "caption"), None)
        if caption is None:
            continue
        caption_paragraphs = [c for c in caption.iter() if c.tag.rsplit("}", 1)[-1] == "p"]
        if len(caption_paragraphs) == 1:
            location = {"xmlId": node.get("id"), "xpath": path}
            refs = {item["self_ref"] for item in result["structuredDocument"]["texts"]
                    if item.get("rawXmlLocation") == location}
            if refs:
                caption_refs[paths[id(caption_paragraphs[0])]] = refs

    def plain_fragments(node):
        parts = [""]
        def walk(current):
            parts[-1] += current.text or ""
            for child in current:
                if child.tag.rsplit("}", 1)[-1] in {"math", "tex-math", "inline-formula", "disp-formula", "sub", "sup", "italic", "bold", "xref"}:
                    parts.append("")
                else:
                    walk(child)
                parts[-1] += child.tail or ""
        walk(node)
        return [location_text(part) for part in parts if len(location_text(part)) >= 40]

    ids, misses = {}, []
    for node, path in nodes:
        tag = node.tag.rsplit("}", 1)[-1]
        if tag not in {"p", "fig", "table-wrap"}:
            continue
        location = {"xmlId": node.get("id"), "xpath": path}
        matches = []
        if tag == "p":
            if path in caption_refs:
                matches = [i for i, block in enumerate(blocks) if caption_refs[path].intersection(block.get("documentRefs", []))]
                if matches:
                    location["matchMethod"] = "unique_caption_reference"
            # Only complete paragraph matches are accepted, never fuzzy anchors.
            value = location_text("".join(node.itertext()))
            if not matches and len(value) >= 25:
                matches = [i for i, text in enumerate(searchable) if value in text]
                if len(matches) > 1 or sum(value in text for text in paragraph_texts) != 1:
                    matches = []
            if not matches:
                for fragment in plain_fragments(node):
                    anchor = fragment[:100]
                    candidates = [i for i, text in enumerate(searchable) if anchor in text]
                    if len(candidates) == 1 and sum(anchor in text for text in paragraph_texts) == 1:
                        matches = candidates
                        location.update(matchMethod="unique_literal_fragment", matchedText=anchor)
                        break
            if not matches:
                for math in node.iter():
                    if math.tag.rsplit("}", 1)[-1] != "math":
                        continue
                    item = formula_by_id.get(math.get("id"))
                    candidates = formula_blocks.get(item["sha256"], set()) if item else set()
                    if len(candidates) == 1:
                        matches = list(candidates)
                        location.update(matchMethod="unique_formula_hash", formulaXmlId=math.get("id"), notationSha256=item["sha256"])
                        break
        else:
            refs = {item["self_ref"] for item in result["structuredDocument"]["texts"]
                    if item.get("rawXmlLocation") == location}
            matches = [i for i, b in enumerate(blocks) if refs.intersection(b.get("documentRefs", []))]
        for i in matches:
            blocks[i].setdefault("rawXmlLocations", []).append(location)
        if node.get("id"):
            ids[node.get("id")] = matches
        if tag == "p" and location_text("".join(node.itertext())) and not matches:
            misses.append(location)
        if matches:
            for xref in node.iter():
                if xref.tag.rsplit("}", 1)[-1] == "xref":
                    for i in matches:
                        blocks[i].setdefault("xmlReferenceTargets", []).extend(xref.get("rid", "").split())
    for block in blocks:
        block["relatedOrdinals"] = sorted({i for target in block.get("xmlReferenceTargets", []) for i in ids.get(target, [])})
    for i, block in enumerate(blocks):
        for target in list(block["relatedOrdinals"]):
            if i not in blocks[target]["relatedOrdinals"]:
                blocks[target]["relatedOrdinals"].append(i)
    return {"unmatchedParagraphs": misses, "xmlIds": ids,
            "limitation": "Only exact normalized complete paragraphs and unique captions mapped; unmatched nodes require review."}


def assemble(blocks: list[dict], title: str, lineage: dict) -> tuple[str, list[dict]]:
    pieces, passages, length = [], [], 0
    for ordinal, block in enumerate(blocks):
        value = block["text"].strip()
        if not value:
            raise ValueError("Empty preprocessing block")
        prefix = "\n\n" if pieces else ""
        start = length + len(prefix)
        pieces.extend([prefix, value])
        length = start + len(value)
        identity = sha((lineage["inputSha256"] + str(ordinal) + value).encode())[:24]
        embedded = f"문헌: {title}\n절: {block['locator']}\n{value}"
        passages.append({**block, **lineage, "id": identity, "ordinal": ordinal, "text": value,
                         "start_offset": start, "end_offset": length,
                         "embedding_text": embedded, "input_hash": sha(embedded.encode())})
    content = "".join(pieces)
    prepared_passages(content, passages)
    for i, passage in enumerate(passages):
        passage["previousId"] = passages[i - 1]["id"] if i else None
        passage["nextId"] = passages[i + 1]["id"] if i + 1 < len(passages) else None
        passage["relatedPassageIds"] = [passages[n]["id"] for n in passage.pop("relatedOrdinals", []) if n != i]
    return content, passages
