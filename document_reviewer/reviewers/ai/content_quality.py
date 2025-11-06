"""
AI Reviewers for document validation
"""

from ...core.base_reviewer import BaseReviewer
from ...core.models import ReviewResponse
from ...prompts import ContentPrompts


class UniqueSolutionReviewer(BaseReviewer):
    """Validates if problem has unique solution for automated testing"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_unique_solution_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class TimeComplexityAuthenticityReviewer(BaseReviewer):
    """Reviews time complexity authenticity in metadata for all approaches"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_time_complexity_authenticity_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class ResponseRelevanceReviewer(BaseReviewer):
    """Reviews if response section is relevant to problem description"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_response_relevance_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class ConstraintsConsistencyReviewer(BaseReviewer):
    """Reviews if defined problem constraints match problem description"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_constraints_consistency_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class MissingApproachesReviewer(BaseReviewer):
    """Reviews if any approaches or data structures are not explained in approach steps (this check is only for the response section, where optimal algorithm is explained)"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_missing_approaches_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class CodeElementsExistenceReviewer(BaseReviewer):
    """Reviews if mentioned variables, functions, and classes exist in code"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_code_elements_existence_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class ExampleWalkthroughReviewer(BaseReviewer):
    """Reviews if response has example walkthrough with optimal algorithm"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_example_walkthrough_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class ComplexityCorrectnessReviewer(BaseReviewer):
    """Reviews time and space complexity correctness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_complexity_correctness_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class ConclusionQualityReviewer(BaseReviewer):
    """Reviews conclusion quality"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_conclusion_quality_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class ProblemConsistencyReviewer(BaseReviewer):
    """Reviews problem statement consistency"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_problem_consistency_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class SolutionPassabilityReviewer(BaseReviewer):
    """Reviews if solution is passable according to limits"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_solution_passability_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class MetadataCorrectnessReviewer(BaseReviewer):
    """Reviews metadata correctness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_metadata_correctness_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class TestCaseValidationReviewer(BaseReviewer):
    """Reviews test cases against code and problem statement"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_test_case_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class SampleDryRunValidationReviewer(BaseReviewer):
    """Reviews if dry runs or explanations of sample test cases match the given examples exactly"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_sample_dry_run_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class NoteSectionReviewer(BaseReviewer):
    """Reviews note section explanation approach - only applies to problem statement/prompt section"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_note_section_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class InefficientLimitationsReviewer(BaseReviewer):
    """Reviews if inefficient approaches mention limitations"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_inefficient_limitations_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class FinalApproachDiscussionReviewer(BaseReviewer):
    """Reviews final approach discussion completeness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_final_approach_discussion_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class NoCodeInReasoningReviewer(BaseReviewer):
    """Reviews if reasoning chains contain code"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_no_code_in_reasoning_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class TimeLimitValidationReviewer(BaseReviewer):
    """Validates that time limit is specified in the document"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_time_limit_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class MemoryLimitValidationReviewer(BaseReviewer):
    """Validates that memory limit is at least 32 MB"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ContentPrompts.get_memory_limit_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


