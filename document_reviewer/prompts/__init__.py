"""Prompts module for document review"""

from .code_quality_prompts import Prompts as CodeQualityPrompts
from .content_prompts import Prompts as ContentPrompts
from .structure_prompts import Prompts as StructurePrompts

__all__ = ["CodeQualityPrompts", "ContentPrompts", "StructurePrompts"]
