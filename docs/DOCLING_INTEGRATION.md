# Docling PDF ingestion

The API calls `knowledge.integrations.public_fetch.parse_download` with `parser="docling"` for PDFs. HTML/text retain the lightweight extractor. Docling is an isolated optional Python runtime; the API environment does not import its ML packages. A configured Docling failure is returned explicitly and never silently replaced with the legacy extraction.

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

Official interfaces: [Docling advanced options](https://docling-project.github.io/docling/usage/advanced_options/), [DocumentConverter API](https://docling-project.github.io/docling/reference/document_converter/), [hybrid chunking](https://docling-project.github.io/docling/examples/hybrid_chunking/), [PyPI release](https://pypi.org/project/docling/2.143.0/).
