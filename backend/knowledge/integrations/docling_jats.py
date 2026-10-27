"""Offline publisher JATS conversion; original bytes remain separate from normalization.

Run only in the isolated Docling runtime behind the bounded-process launcher.
The public service uses the same bounded conversion for JATS input.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from importlib.metadata import version
from pathlib import Path

MAX_INPUT_BYTES = 5 * 1024 * 1024


def normalize_jats(raw: bytes) -> tuple[bytes, dict]:
    """Remove transport wrappers without resolving entities or fetching external files."""
    from lxml import etree

    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("JATS input limit")
    # PMC exports omit the DTD (or wrap namespace-qualified JATS in OAI-PMH).
    # Normalize only the transport wrapper/namespace for the pinned SDK's format detector.
    # Original bytes stay the preserved source; no content is summarized or rewritten.
    tree=etree.fromstring(raw,parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True))
    # Check the parsed DTD too: a byte-pattern guard alone misses UTF-16 declarations.
    dtd=tree.getroottree().docinfo.internalDTD
    if dtd is not None and list(dtd.iterentities()):
        raise ValueError('Entity declarations are not accepted')
    if any(isinstance(node, etree._Entity) for node in tree.iter()):
        raise ValueError('Entity references are not accepted')
    articles=[node for node in tree.iter() if isinstance(node.tag,str) and etree.QName(node).localname=='article']
    if len(articles)!=1: raise ValueError('Expected one JATS article')
    article=articles[0]
    if article.getparent() is not None:
        article.getparent().remove(article)
    titles=article.xpath('.//*[local-name()="article-title"]')
    if not titles: raise ValueError('JATS article title is missing')
    original_title=''.join(titles[0].itertext())
    for node in article.iter():
        if isinstance(node.tag,str) and str(etree.QName(node).namespace or '').startswith('https://jats.nlm.nih.gov/ns/'):
            node.tag=etree.QName(node).localname
    etree.cleanup_namespaces(article)
    # The SDK walks body/back but not floats-group. Relocate intact publisher nodes;
    # each original id and the original raw XML remain available for provenance.
    body_node=article.find('body')
    if body_node is None: raise ValueError('JATS article body is missing')
    float_count=0
    float_section=etree.Element('sec',id='extraction-floating-elements')
    etree.SubElement(float_section,'title').text='원문에 별도 배치된 표와 그림'
    for floating in list(article.findall('floats-group')):
        for item in list(floating):
            float_section.append(item);float_count+=1
        article.remove(floating)
    if float_count: body_node.append(float_section)
    # Avoid native chunking splitting chemical subscripts and squared units into new lines.
    for node in list(article.iter()):
        if node.tag in {'sub','sup'}:
            value=''.join(node.itertext())
            alphabet='0123456789+-=()'
            mapped='₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎' if node.tag=='sub' else '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾'
            text=value.translate(str.maketrans(alphabet,mapped)) if all(c in alphabet for c in value) else (('_' if node.tag=='sub' else '^')+'{'+value+'}')
            replacement=etree.Element('named-content');replacement.text=text;replacement.tail=node.tail
            node.getparent().replace(node,replacement)
    def math_notation(node):
        tag=etree.QName(node).localname
        if tag in {'mi','mn','mo','mtext'}:
            if len(node): raise ValueError('Nested MathML token requires review')
            return node.text or ''
        children=list(node)
        if tag=='semantics':
            if len(children)!=1: raise ValueError('MathML semantics annotations require review')
            return (node.text or '')+math_notation(children[0])+(children[0].tail or '')
        if tag in {'math','mrow','mstyle'}:
            return (node.text or '')+''.join(math_notation(c)+(c.tail or '') for c in children)
        if (node.text or '').strip() or any((child.tail or '').strip() for child in children):
            raise ValueError('MathML direct text requires review')
        if tag in {'msup','msub','mfrac'} and len(children)!=2 or tag=='msubsup' and len(children)!=3:
            raise ValueError('MathML operand count requires review')
        if tag=='msup': return '{'+math_notation(children[0])+'}^{'+math_notation(children[1])+'}'
        if tag=='msub': return '{'+math_notation(children[0])+'}_{'+math_notation(children[1])+'}'
        if tag=='msubsup': return '{'+math_notation(children[0])+'}_{'+math_notation(children[1])+'}^{'+math_notation(children[2])+'}'
        if tag=='mfrac': return '\\frac{'+math_notation(children[0])+'}{'+math_notation(children[1])+'}'
        if tag=='msqrt': return '\\sqrt{'+''.join(math_notation(c) for c in children)+'}'
        if (tag=='mfenced' and len(children)==1 and set(node.attrib) <= {'open','close','separators'}
                and (node.get('open','('),node.get('close',')')) in {('(',')'),('[',']')}):
            return node.get('open','(')+math_notation(children[0])+node.get('close',')')
        if tag=='mover' and len(children)==2 and set(node.attrib) <= {'accent'} and node.get('accent') in {None,'true','false'}:
            mark=math_notation(children[1])
            if mark in {'−','-'}: return '\\overset{'+mark+'}{'+math_notation(children[0])+'}'
            if mark=='^' and node.get('accent')=='true': return '\\hat{'+math_notation(children[0])+'}'
        if (tag=='munderover' and len(children)==3 and not node.attrib
                and etree.QName(children[0]).localname=='mo' and math_notation(children[0])=='∑'):
            return '\\sum\\limits_{'+math_notation(children[1])+'}^{'+math_notation(children[2])+'}'
        if tag=='mtable' and set(node.attrib) <= {'columnalign'} and node.get('columnalign','left')=='left' and children:
            rows=[]
            for row in children:
                if etree.QName(row).localname!='mtr' or row.attrib or (row.text or '').strip() or len(row)!=1:
                    raise ValueError('MathML table layout requires review')
                cell=row[0]
                if (etree.QName(cell).localname!='mtd' or cell.attrib or (cell.tail or '').strip()
                        or (cell.text or '').strip() or any((c.tail or '').strip() for c in cell)):
                    raise ValueError('MathML table layout requires review')
                rows.append((cell.text or '')+''.join(math_notation(c)+(c.tail or '') for c in cell))
            return '\\begin{aligned}'+r'\\'.join('&'+row for row in rows)+'\\end{aligned}'
        raise ValueError('Unsupported MathML layout')
    math_count=math_fallback=0
    fallback_details=[]
    notation_hashes=[]
    for math_node in list(article.xpath('.//*[local-name()="math"]')):
        try:
            notation=math_notation(math_node);replacement=etree.Element('tex-math');replacement.text=notation;math_count+=1
            notation_hashes.append({'xmlId':math_node.get('id'),'sha256':hashlib.sha256(notation.strip().encode('utf8')).hexdigest(), 'length':len(notation.strip())})
        except (ValueError,IndexError) as exc:
            replacement=etree.Element('named-content');replacement.text='[MathML 원문: '+etree.tostring(math_node,encoding='unicode',with_tail=False)+']';math_fallback+=1
            fallback_details.append({'xmlId':math_node.get('id'),'reason':str(exc) or 'MathML operand count requires review'})
        replacement.tail=math_node.tail;math_node.getparent().replace(math_node,replacement)
    normalized=etree.tostring(article,encoding='UTF-8',xml_declaration=True,
        doctype='<!DOCTYPE article SYSTEM "https://jats.nlm.nih.gov/archiving/1.4/JATS-archivearticle1-4.dtd">')
    return normalized, {"title": original_title, "floatCount": float_count, "mathCount": math_count, "mathFallback": math_fallback, "mathFallbackDetails": fallback_details, "mathNotationHashes": notation_hashes}


def parse_jats(raw: bytes, *, artifacts_path: str, max_characters: int = 500000) -> dict:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.backend_options import JatsBackendOptions
    from docling.datamodel.document import InputDocument
    from docling.datamodel.pipeline_options import ConvertPipelineOptions
    from docling.backend.xml.jats_backend import JatsDocumentBackend
    from docling.pipeline.simple_pipeline import SimplePipeline
    from knowledge.integrations.docling_parser import document_blocks, assemble_blocks

    if max_characters < 1:
        raise ValueError("max_characters must be positive")
    normalized, info = normalize_jats(raw)
    original_title = info["title"]
    float_count, math_count, math_fallback = info["floatCount"], info["mathCount"], info["mathFallback"]
    input_doc=InputDocument(path_or_stream=io.BytesIO(normalized),format=InputFormat.XML_JATS,
        backend=JatsDocumentBackend,backend_options=JatsBackendOptions(enable_remote_fetch=False,enable_local_fetch=False),
        filename=hashlib.sha256(raw).hexdigest()+'.nxml')
    if not input_doc.valid: raise ValueError('Invalid JATS article')
    converted=SimplePipeline(ConvertPipelineOptions()).execute(input_doc,raises_on_error=True)
    doc=converted.document
    title=original_title
    for text_item in doc.texts:
        if text_item.label.value=='title':
            text_item.text=original_title
            break
    blocks=document_blocks(doc,Path(artifacts_path),title)
    for block in blocks:
        # JATS contains section/item IDs rather than PDF pages. Do not manufacture page numbers.
        first=(block.get('headings') or [block['text'].split('\n',1)[0]])[-1]
        block['locator']='JATS 절: '+first[:180]+(' · 표' if 'table' in block['label'] else '')
    content,source_map,truncated=assemble_blocks(blocks,max_characters)
    prepared=[]
    for block,source in zip(blocks,source_map):
        text=content[source['startOffset']:source['endOffset']]
        embed=title+'\n\n'+text
        prepared.append(dict(text=text,locator=source['locator'],start_offset=source['startOffset'],end_offset=source['endOffset'],
                             embedding_text=embed,input_hash=hashlib.sha256(embed.encode()).hexdigest()))
    result=dict(title=title,content=content,readScope='partial',metadata={
        'documentForm':'text_extraction','sourceSha256':hashlib.sha256(raw).hexdigest(),
        'parserInputSha256':hashlib.sha256(normalized).hexdigest(),
        'sourceXmlNormalization':'unwrap OAI-PMH, remove JATS namespace, declare DTD, move floats-group nodes intact into body, preserve sub/sup as Unicode notation; entity and external fetch disabled',
        'relocatedFloatElements':float_count,
        'mathmlNotationConverted':math_count,'mathmlPreservedAsXml':math_fallback,'mathmlFallbackDetails':info['mathFallbackDetails'],
        'mathmlNotationHashes':info['mathNotationHashes'],
        'parserProfile':{'engine':'docling','version':version('docling'),'coreVersion':version('docling-core'),
                         'sourceFormat':'xml_jats','backend':'JatsDocumentBackend','serialization':'hybrid-markdown-v3',
                         'inputNormalization':'jats-transport-v3',
                         'maxCharacters':max_characters,
                         'chunker':'HybridChunker','maxTokens':768,'tokenizer':'cl100k_base','ocr':False,
                         'remoteFetch':False,'localFetch':False},
        'conversionStatus':str(converted.status.value),'tableCount':len(doc.tables),'pictureCount':len(doc.pictures)},
        limitations=['JATS XML의 본문·표·캡션을 구조적으로 추출했습니다. 별도 그림 파일·외부 링크·부록은 가져오지 않았습니다.',
                     'XML 절·문서 요소 ID를 보존하며 PDF 페이지 번호로 바꾸지 않았습니다.'],
        structuredDocument=doc.export_to_dict(),sourceMap=source_map,preparedPassages=prepared,normalizedXml=normalized.decode('utf8'))
    if truncated: result['limitations'].append(f'{max_characters}자 한도에서 완전한 청크까지만 보존했습니다.')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts_path")
    parser.add_argument("--max-characters", type=int, default=500000)
    args = parser.parse_args()
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    print(json.dumps(parse_jats(raw, artifacts_path=args.artifacts_path,
                               max_characters=args.max_characters), ensure_ascii=False))


if __name__ == "__main__":
    main()
