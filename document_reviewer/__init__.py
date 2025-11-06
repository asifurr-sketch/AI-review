"""
Document Reviewer - A scalable AI-powered document review system

This package provides comprehensive document review capabilities for competitive programming
problems, including code quality checks, content validation, and GitHub repository validation.
"""

__version__ = "2.0.0"
__author__ = "Md Asifur Rahman"

from .core.models import ReviewResult, ReviewResponse
from .system.review_system import DocumentReviewSystem

__all__ = [
    "ReviewResult",
    "ReviewResponse", 
    "DocumentReviewSystem",
]
