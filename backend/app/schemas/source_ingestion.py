"""Pydantic Schemas for Admin Source Document Ingestion & Knowledge Extraction.

Strict Contract for:
- Document tracking list (with last_succeeded_at vs last_attempted_at separation)
- Extraction execution request (using safe server-issued doc_id)
- Wiki DTO conversion preview (showing purpose, principles, limitations, perspective_cases, relations)
- Idempotent apply request with version checks
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class SourceDocumentItemDTO(BaseModel):
    doc_id: str = Field(alias="docId")
    file_path: str = Field(alias="filePath")
    publisher: str
    title: str
    file_hash: str = Field(alias="fileHash")
    last_succeeded_hash: Optional[str] = Field(None, alias="lastSucceededHash")
    last_succeeded_at: Optional[str] = Field(None, alias="lastSucceededAt")
    last_attempted_at: Optional[str] = Field(None, alias="lastAttemptedAt")
    attempt_status: str = Field(alias="attemptStatus")
    is_modified: bool = Field(False, alias="isModified")
    is_applied: bool = Field(False, alias="isApplied")
    last_applied_at: Optional[str] = Field(None, alias="lastAppliedAt")
    extracted_concepts_count: int = Field(0, alias="extractedConceptsCount")
    extracted_relations_count: int = Field(0, alias="extractedRelationsCount")
    last_error_message: Optional[str] = Field(None, alias="lastErrorMessage")

    class Config:
        populate_by_name = True


class SourceDocumentListResponse(BaseModel):
    documents: List[SourceDocumentItemDTO]
    total_count: int = Field(alias="totalCount")
    succeeded_count: int = Field(alias="succeededCount")
    pending_count: int = Field(alias="pendingCount")
    modified_count: int = Field(alias="modifiedCount")

    class Config:
        populate_by_name = True


class ExtractionRequestDTO(BaseModel):
    doc_ids: List[str] = Field(..., alias="docIds")
    force_reextract: bool = Field(False, alias="forceReextract")
    resume_interrupted: bool = Field(False, alias="resumeInterrupted")

    class Config:
        populate_by_name = True


class ExtractionStateDTO(BaseModel):
    state: Literal["idle", "running", "finished", "error", "interrupted"]
    run_id: Optional[str] = Field(None, alias="runId")
    doc_ids: List[str] = Field(default_factory=list, alias="docIds")
    preserved_count: int = Field(0, alias="preservedCount")
    interrupted_doc_id: Optional[str] = Field(None, alias="interruptedDocId")

    class Config:
        populate_by_name = True


class ConceptClassificationDTO(BaseModel):
    domain_facet: Optional[Literal["device", "unit_process", "operations", "materials_infra"]] = Field(None, alias="domainFacet")
    category: str = Field("미분류", min_length=1, max_length=64)
    scale_level: Optional[int] = Field(None, alias="scaleLevel", ge=1, le=5)

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, value):
        if not value.strip():
            raise ValueError("분류는 비워둘 수 없습니다. 판단되지 않으면 미분류를 사용해주세요.")
        return value.strip()

    class Config:
        populate_by_name = True


class ExtractedSpecificationDTO(BaseModel):
    """Source-backed parameter fields; absent values stay absent."""
    model_config = {"coerce_numbers_to_str": True}
    parameter: str
    value: Optional[str] = None
    unit: Optional[str] = None
    safetyMargin: Optional[str] = None
    role: Optional[str] = None
    tradeoff: Optional[str] = None
    rationale: Optional[str] = None
    isConfidential: bool = False
    evidenceQuote: Optional[str] = None
    fieldEvidenceQuotes: Dict[str, Optional[str]] = Field(default_factory=dict)


class ExtractedConceptDiffDTO(ConceptClassificationDTO):
    """Wiki DTO formatted concept extraction result for Preview and Diff."""
    concept_id: str = Field(alias="conceptId")
    title: str
    eng_name: str = Field(alias="engName")
    classification_note: Optional[str] = Field(None, alias="classificationNote")
    existing_classification: Optional[ConceptClassificationDTO] = Field(None, alias="existingClassification")
    classification_proposals: List[Dict[str, Any]] = Field(default_factory=list, alias="classificationProposals")
    classification_conflict: bool = Field(False, alias="classificationConflict")
    relation_corrections: List[Dict[str, Any]] = Field(default_factory=list, alias="relationCorrections")
    validation_warnings: List[str] = Field(default_factory=list, alias="validationWarnings")
    is_new: bool = Field(False, alias="isNew")
    summary: str
    purpose: str
    principles: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[Dict[str, Any]] = Field(default_factory=list)
    perspective_cases: List[Dict[str, Any]] = Field(default_factory=list, alias="perspectiveCases")
    previous_steps: List[Dict[str, Any]] = Field(default_factory=list, alias="previousSteps")
    next_steps: List[Dict[str, Any]] = Field(default_factory=list, alias="nextSteps")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    part_of: List[Dict[str, Any]] = Field(default_factory=list, alias="partOf")
    is_a: List[Dict[str, Any]] = Field(default_factory=list, alias="isA")
    evidence_quote: Optional[str] = Field(None, alias="evidenceQuote")
    evidence_verified: bool = Field(False, alias="evidenceVerified")
    source_document_title: Optional[str] = Field(None, alias="sourceDocumentTitle")
    source_url: Optional[str] = Field(None, alias="sourceUrl")
    source_coverage: Optional[Dict[str, Any]] = Field(None, alias="sourceCoverage")
    summary_evidence_quote: Optional[str] = Field(None, alias="summaryEvidenceQuote")
    purpose_evidence_quote: Optional[str] = Field(None, alias="purposeEvidenceQuote")
    summary_evidence_quotes: List[str] = Field(default_factory=list, alias="summaryEvidenceQuotes")
    purpose_evidence_quotes: List[str] = Field(default_factory=list, alias="purposeEvidenceQuotes")
    merged_preview: Optional[Dict[str, Any]] = Field(None, alias="mergedPreview")
    missing_fields: List[str] = Field(default_factory=list, alias="missingFields")
    apply_blockers: List[str] = Field(default_factory=list, alias="applyBlockers")

    class Config:
        populate_by_name = True


class DocumentExtractionResultDTO(BaseModel):
    doc_id: str = Field(alias="docId")
    file_path: str = Field(alias="filePath")
    title: str
    status: str
    succeeded: bool
    error_message: Optional[str] = Field(None, alias="errorMessage")
    extracted_concepts: List[ExtractedConceptDiffDTO] = Field(default_factory=list, alias="extractedConcepts")

    class Config:
        populate_by_name = True


class ExtractionPreviewResponseDTO(BaseModel):
    job_id: str = Field(alias="jobId")
    total_requested: int = Field(alias="totalRequested")
    total_succeeded: int = Field(alias="totalSucceeded")
    total_failed: int = Field(alias="totalFailed")
    document_results: List[DocumentExtractionResultDTO] = Field(alias="documentResults")
    aggregated_concepts: List[ExtractedConceptDiffDTO] = Field(alias="aggregatedConcepts")

    class Config:
        populate_by_name = True


class ApplyExtractionRequestDTO(BaseModel):
    job_id: Optional[str] = Field(None, alias="jobId")
    doc_ids: List[str] = Field(..., alias="docIds")
    expected_versions: Optional[Dict[str, str]] = Field(None, alias="expectedVersions")
    concept_metadata: Dict[str, ConceptClassificationDTO] = Field(default_factory=dict, alias="conceptMetadata")

    class Config:
        populate_by_name = True


class ApplyExtractionResponseDTO(BaseModel):
    applied_count: int = Field(alias="appliedCount")
    updated_concepts: List[str] = Field(alias="updatedConcepts")
    message: str

    class Config:
        populate_by_name = True
