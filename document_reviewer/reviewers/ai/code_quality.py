"""
AI Reviewers for document validation
"""

from ...core.base_reviewer import BaseReviewer
from ...core.models import ReviewResponse
from ...prompts import CodeQualityPrompts


class StyleGuideReviewer(BaseReviewer):
    """Reviews code style guide compliance"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CodeQualityPrompts.get_style_guide_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class NamingConventionsReviewer(BaseReviewer):
    """Reviews naming conventions compliance"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CodeQualityPrompts.get_naming_conventions_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class DocumentationReviewer(BaseReviewer):
    """Reviews appropriate documentation style"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = CodeQualityPrompts.get_documentation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


