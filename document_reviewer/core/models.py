"""
Core data models for the document review system
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class ReviewResult(Enum):
    """Enumeration of possible review results"""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"


@dataclass
class ReviewResponse:
    """Response from a review operation"""
    result: ReviewResult
    reasoning: str
    score: Optional[float] = None
    details: Optional[str] = None
