"""
AI Reviewers for document validation
"""

from ...core.base_reviewer import BaseReviewer
from ...core.models import ReviewResponse
from ...prompts import StructurePrompts


class MathEquationsReviewer(BaseReviewer):
    """Reviews mathematical equations correctness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = StructurePrompts.get_math_equations_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class SubtopicTaxonomyReviewer(BaseReviewer):
    """Reviews if subtopics are from taxonomy list"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = StructurePrompts.get_subtopic_taxonomy_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class SubtopicRelevanceReviewer(BaseReviewer):
    """Reviews if selected subtopics are relevant"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = StructurePrompts.get_subtopic_relevance_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class MissingSubtopicsReviewer(BaseReviewer):
    """Reviews for missing relevant subtopics"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = StructurePrompts.get_missing_subtopics_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class PredictiveHeadingsReviewer(BaseReviewer):
    """Reviews for natural thinking flow in thoughts - allows somewhat predictive titles if they don't break thinking flow"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = StructurePrompts.get_predictive_headings_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class MathFormattingReviewer(BaseReviewer):
    """Reviews mathematical variables and expressions formatting"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = StructurePrompts.get_math_formatting_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


