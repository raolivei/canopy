"""Pydantic models for Golden Questions regression suite."""

from typing import Optional

from pydantic import BaseModel, Field


class GoldenQuestionResult(BaseModel):
    """Result of a single golden question comparison."""

    question_number: int = Field(..., description="Question 1-10 identifier")
    question: str = Field(..., description="The golden question text")
    category: str = Field(..., description="Category: net_worth, spending, budget, subscriptions, savings, merchants, portfolio, goals, anomalies")
    canopy_answer: str = Field(..., description="Canopy API response")
    monarch_reference: str = Field(..., description="Monarch MCP reference oracle response")
    match_type: str = Field(..., description="Match result: exact, numerical_delta, categorical_match, partial, mismatch")
    numerical_delta: Optional[float] = Field(None, description="Absolute difference for numerical comparisons")
    delta_percent: Optional[float] = Field(None, description="Percentage difference for numerical comparisons")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0.0-1.0")
    passed: bool = Field(..., description="True if comparison passes threshold")
    notes: Optional[str] = Field(None, description="Additional details about comparison")


class GoldenQuestionsRunRequest(BaseModel):
    """Request to run golden questions regression suite."""

    verbose: bool = Field(False, description="Include detailed comparison logs")
    stop_on_failure: bool = Field(False, description="Stop on first failure")


class GoldenQuestionsRunResponse(BaseModel):
    """Response from golden questions regression run."""

    run_id: str = Field(..., description="Unique run identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp of run")
    total_questions: int = Field(..., description="Total questions executed")
    passed: int = Field(..., description="Number of questions passed")
    failed: int = Field(..., description="Number of questions failed")
    pass_rate: float = Field(..., ge=0, le=1, description="Pass rate 0.0-1.0")
    results: list[GoldenQuestionResult] = Field(..., description="Individual question results")
    execution_time_ms: int = Field(..., description="Total execution time in milliseconds")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered during run")
