"""
Chain of Thought (CoT) Quality Reviewers
"""

from ...core.base_reviewer import BaseReviewer
from ...core.models import ReviewResponse
from ...prompts.cot_prompts import CoTPrompts


class CoTStructureReviewer(BaseReviewer):
    """Reviews if CoT follows the required structural format"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_structure_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTThoughtQualityReviewer(BaseReviewer):
    """Reviews if thoughts contain proper reasoning and justification"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_thought_quality_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTApproachProgressionReviewer(BaseReviewer):
    """Reviews if approaches progress from inefficient to optimal"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_approach_progression_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTVariableConsistencyReviewer(BaseReviewer):
    """Reviews variable name consistency between prompt and CoT"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_variable_consistency_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTLineReferenceReviewer(BaseReviewer):
    """Reviews that chains don't reference line numbers when no code is present"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_line_reference_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTLogicalContinuityReviewer(BaseReviewer):
    """Reviews that each chain logically follows from the previous one"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_logical_continuity_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTMarkdownFormattingReviewer(BaseReviewer):
    """Reviews that code blocks use proper markdown formatting"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_markdown_formatting_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTMetadataAlignmentReviewer(BaseReviewer):
    """Reviews that metadata complexity matches CoT discussions"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_metadata_alignment_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTLanguageConsistencyReviewer(BaseReviewer):
    """Reviews that chains don't mention wrong programming language"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_language_consistency_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTConstraintValidationReviewer(BaseReviewer):
    """Reviews if time and space constraints are present and correct"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_constraint_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class ResponseStructureReviewer(BaseReviewer):
    """Reviews if response section follows the required structure"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_response_structure_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTPlagiarismCheckReviewer(BaseReviewer):
    """Performs heuristic check for code plagiarism indicators"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_plagiarism_check_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CoTAccuracyCheckReviewer(BaseReviewer):
    """Reviews if thoughts and chains are technically accurate"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CoTPrompts.get_cot_accuracy_check_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)
