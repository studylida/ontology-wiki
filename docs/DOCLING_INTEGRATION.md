# Docling PDF and JATS ingestion

The API calls `knowledge.integrations.public_fetch.parse_download` with `parser="docling"` for PDFs and publisher JATS XML. HTML/text retain the lightweight extractor. XML requires Docling; OCR is an explicit PDF-only option. Docling is an isolated optional Python runtime; the API environment does not import its ML packages. A configured Docling failure is returned explicitly and never silently replaced with the legacy extraction.

## Windows runtime

The verified installation is `var/runtimes/docling/Scripts/python.exe`, with models in `var/models/docling`. Install from the official PyPI index using `backend/requirements-docling.txt`. The tested versions are Docling 2.143.0, Docling Core 2.104.0, IBM models 4.0.4, PDFium 5.14.0, RapidOCR 3.10.0 and tiktoken 0.12.0. The private verification directory retains a full `runtime-lock.txt` snapshot.

```powershell
python -m venv var/runtimes/docling
var/runtimes/docling/Scripts/python.exe -m pip install --index-url https://pypi.org/simple -r backend/requirements-docling.txt
$env:HF_HUB_DISABLE_IMPLICIT_TOKEN = '1'
var/runtimes/docling/Scripts/docling-tools.exe models download layout tableformer rapidocr --rapidocr-backend-lang torch:en --output-dir var/models/docling --quiet
var/runtimes/docling/Scripts/python.exe -c "import os,tiktoken; os.environ['TIKTOKEN_CACHE_DIR']='var/models/docling/tokenizer'; tiktoken.get_encoding('cl100k_base')"
```

Model downloads are an explicit setup step. Parsing sets the Hugging Face offline flags, disables implicit tokens, uses a fresh temporary profile/home, and receives only allowlisted OS variables. The tokenizer cache must have its published SHA-256 before it is loaded. Models and tokenizer files are content-hashed into the conversion key. The parser does not receive API keys or database credentials. This is resource isolation, not a filesystem/network security sandbox.

Windows workers start behind a stdin gate with `-S`. A Job Object is assigned before imports execute; it limits aggregate committed memory/CPU and kills descendants on close. Wall timeout, output cap, cancellation and errors also close the job. The lightweight worker has 12 seconds/512 MiB; Docling has 480 seconds/8 GiB, 600 CPU seconds and 32 MiB output. Limits are distinct because importing PyTorch alone exceeds a lightweight parser's practical budget. Input is capped at 20 MiB for local Docling conversion. Public URL downloads still have the existing 5 MiB bound.

## Output and preservation contract

`parse_download` returns `title`, `content`, `readScope`, `metadata`, `limitations`, plus `structuredDocument`, `sourceMap` and `preparedPassages` for Docling. `content` is the canonical text extraction, not an edited summary or a claim of byte-identical PDF text.

- `structuredDocument`: full Docling JSON, including table cells, source item references, page coordinates and document order.
- `sourceMap`: canonical `startOffset`/`endOffset`, original Docling item references, page numbers, bounding boxes and a readable locator.
- `preparedPassages`: `text`, `locator`, `start_offset`, `end_offset`, `embedding_text`, `input_hash`. Each `content[start_offset:end_offset] == text`. Index these passages directly; do not run them through the old character splitter.
- Native `HybridChunker` uses 768 cl100k tokens, Markdown table serialization, repeated table headers and peer merging. Its contextualized headings/captions stay in the cited passage as well as embedding input, so experimental conditions do not disappear at a chunk boundary. Document title is added to embedding input.

With `storage_path`, original bytes and all derived artifacts are saved using the existing content-addressed `save_raw`. Metadata references are relative paths: `rawPath`, `structuredDocumentPath`, `sourceMapPath`, `extractedTextPath`, and `preparedPassagesArtifact`. `conversionKey` fingerprints original bytes, parser/model/tokenizer profile and explicit limits. The result cache at `derived/docling/<key>.json` refers to a hash-checked result blob. Every artifact is verified on reuse. No document/version row is modified by this integration; the document service owns creation of a new extraction revision and source lineage. Unchanged inputs and profiles reuse the conversion without another worker invocation.

`metadata.processing.elapsedMs` is the current conversion/cache-read duration; `cacheHit` distinguishes them, and a cache hit retains `originalElapsedMs`. No provider API call is made during conversion. Pages beyond `max_pages`, text beyond `max_characters`, conversion failures, and pages with no extracted text mark `readScope=partial` and remain explicit in limitations. The text cap stops at a complete chunk. All supplied original bytes remain preserved regardless of extraction scope.

## Verified PDF-specific correction

The Cu film thickness paper (DOI `10.3390/ma17092150`, source SHA-256 `169e0ee61c0d0d5497b3dce67d9903f2e505fe61cf58fa7a7a10135c66c58caa`) contains clipped Form XObjects with a complete earlier manuscript page inside figure resources. Native pypdf, PDFium and Docling extraction exposed hidden paragraphs and tables, including `FOR PEER REVIEW`. Repeated-string deletion would corrupt provenance and would not reliably distinguish the revisions.

The verified correction is `ocr=True`: PDFium rendering, RapidOCR torch English `FULL_PAGE`, `force_backend_text=False`, and the default TableFormer with `do_cell_matching=True`. PDFium renders the visible clipped page; full-page OCR replaces native text cells, and cell matching keeps the table based on those OCR cells. The default Docling renderer plus full-page OCR still produced overlapping text in this file, so that combination was rejected. The official project also tracks [missing clipping information in text cells](https://github.com/docling-project/docling/issues/4762).

The corrected page 4 table preserves 31.24/61.14/93.06% with specimen columns, BF/VF/VH units and its 250°C caption. Page 2 contains 0.8/2.0/2.7 µm specimen thicknesses, and page 3 contains the 0.5 h bonding condition. The separate Stanford TSV source preserves page 21's 32 nm row and TSV 0.35 pJ/b versus wire bond 3.45 pJ/b as a structured table. These are extraction checks, not independent validation of the papers' scientific conclusions.

OCR is selected per source, not silently applied to every native PDF. It can misread text, formula symbols and units; the English profile is not a multilingual guarantee. Figures retain source metadata/captions, but chart points are not inferred. `full` describes pages processed within configured limits, not universal recognition accuracy. Original bytes, prior derived revisions and failed-profile verification artifacts remain available for review. Curated summaries are not replaced or mislabelled as originals by this parser.

## Verification

Run `python -m pytest backend/tests/test_bounded_process.py backend/tests/test_document_parsers.py -q` in the API environment. The tests exercise actual Windows limits, descendant termination, cancellation, credential exclusion, legacy HTML extraction, exact block offsets, original/artifact preservation, cache integrity and incremental keys. Representative real conversion results and provenance maps are recorded under `var/verification/docling-20261027/`; they are not checked into Git.

Final v3 conversion completed for both representative PDFs. Cu: 10 pages, 18 passages, 2 tables, 83.750 seconds; a later verified cache reuse took 0.813 seconds. Stanford TSV: 51 pages, 44 passages, 4 tables, 75.234 seconds. The TSV result is explicitly partial because 12 pages did not contribute extracted text (many contain figures). The key Cu pages 2–4 and TSV page 21 were rendered independently with Poppler and visually checked against the extracted numbers, units, table columns and conditions. Cu formulas remain undecoded and a sentence near the end of page 8 has OCR noise; targeted checks do not constitute a full-document transcription review. These limitations accompany the registration manifest, while every original and prior extraction remains preserved.

Official interfaces: [Docling advanced options](https://docling-project.github.io/docling/usage/advanced_options/), [DocumentConverter API](https://docling-project.github.io/docling/reference/document_converter/), [hybrid chunking](https://docling-project.github.io/docling/examples/hybrid_chunking/), [PyPI release](https://pypi.org/project/docling/2.143.0/).

## Publisher XML conversion

`knowledge.integrations.docling_jats` preserves the pinned SDK's native `JatsDocumentBackend` / `SimplePipeline` path for publisher JATS XML. The public fetch path accepts XML and JATS media types when Docling is configured and runs the existing bounded isolated worker. Input remains capped at 5 MiB.

The utility removes an OAI-PMH transport wrapper and the JATS element namespace, while retaining the original bytes unchanged. Publisher `floats-group` tables and figures move intact into a separately labelled extraction section so they are neither lost nor incorrectly attached to the conclusions. Numeric subscripts/superscripts become equivalent Unicode notation. Supported MathML includes single-child parentheses/brackets, selected overmarks, summation limits and left-aligned single-column math rows. Unsupported layouts remain literal MathML in normalized XML with formula ID and reason, and hold the source for review. Native figure-caption formula extraction can still be incomplete. No equation is evaluated and no unusual source value is silently corrected.

XML parsing disables entity resolution, DTD loading and network access, and rejects entity declarations (including UTF-16 input). Native backend local-file and remote-image fetching are disabled. `normalizedXml` is returned separately and must be saved with `save_raw`; `metadata.normalizedXmlArtifact` references it after preservation. `sourceSha256` identifies untouched source bytes, while `parserInputSha256` identifies normalization. The batch conversion key includes both hashes, the parser profile and model fingerprint. The API does not gain an `lxml` or Docling dependency.

Canonical offsets and prepared passages follow the PDF contract. Locators identify JATS sections; `sourceMap.documentRefs` addresses Docling JSON items, and the separately preserved original/normalized XML retains publisher element IDs. These are not PDF page numbers or original XML byte offsets. `readScope=partial` reflects unfetched figure files, supplements and formula limits even when the XML body was processed completely.

The 2026-10-27 batch inventory covers all 30 files in the nine prepared `raw/new-*` folders. Nine publisher XML and two author PDF extractions produced 327 prepared passages linked to the existing studies, in addition to the previously verified Cu-thickness extraction. The six other PDFs retain explicit holds for unresolved relevance, independent verification or permitted use. Every prior PDF extraction and editorial summary remains preserved. The inventory, targeted QA, registration manifests and unsuccessful conversion profiles live under `var/verification/docling-20261027/batch/`; registration and approval remain document-service operations.

Run `python -m pytest backend/tests/test_bounded_process.py backend/tests/test_document_parsers.py backend/tests/test_docling_jats.py -q`. The optional JATS test uses the installed isolated runtime to check original and normalized hashes, relocated table conditions, MathML, canonical offsets, and UTF-8/UTF-16 entity rejection. It skips explicitly when that runtime is unavailable.

## Runtime quality holds

`documents.runtime_preprocessing` checks prepared Docling passages before preservation and registration. Repeated packed numeric table rows and missing table structure are held; table captions are repeated in their own table passages. Uniquely matched JATS captions may be repaired from the original XML, and unique paragraph evidence is linked by XPath. Unsupported MathML or unresolved captions retain the original XML and cause a conservative document-wide hold. Document registration persists held passages as excluded, so they are not indexed or retrieved; a reviewed edited revision has a separate explicit release. The source remains available, and old cache artifacts are preserved under their original keys.

Original paragraphs can also be linked through a source-unique and passage-unique long formula hash or a uniquely matched single-paragraph caption. Short or repeated unlinked paragraphs remain explicitly counted. The default legacy PDF parser has no comparable structured-table quality gate. Previously registered or indexed sources are not retroactively changed. The checks are targeted heuristics and cannot establish transcription correctness; see [the scoped runtime validation](PREPROCESSING_RUNTIME_VALIDATION_20261027.md) and [the ALD follow-up](ALD_MATH_REVIEW_20261028.md).
