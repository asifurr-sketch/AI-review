"""AI-based reviewers for document validation"""

# Import all reviewer classes for easy access
from .code_quality import (
    StyleGuideReviewer,
    NamingConventionsReviewer,
    DocumentationReviewer,
)

from .content_quality import (
    ResponseRelevanceReviewer,
    ConstraintsConsistencyReviewer,
    MissingApproachesReviewer,
    CodeElementsExistenceReviewer,
    ExampleWalkthroughReviewer,
    ComplexityCorrectnessReviewer,
    ConclusionQualityReviewer,
    ProblemConsistencyReviewer,
    SolutionPassabilityReviewer,
    MetadataCorrectnessReviewer,
    UniqueSolutionReviewer,
    TimeComplexityAuthenticityReviewer,
    TestCaseValidationReviewer,
    SampleDryRunValidationReviewer,
    NoteSectionReviewer,
    InefficientLimitationsReviewer,
    FinalApproachDiscussionReviewer,
    NoCodeInReasoningReviewer,
    TimeLimitValidationReviewer,
    MemoryLimitValidationReviewer,
)

from .structure_quality import (
    SubtopicTaxonomyReviewer,
    TypoCheckReviewer,
    SubtopicRelevanceReviewer,
    MissingSubtopicsReviewer,
    PredictiveHeadingsReviewer,
    MathEquationsReviewer,
    MathFormattingReviewer,
)

from .limits_consistency import (
    LimitsConsistencyReviewer,
)

from .example_validation import (
    ExampleValidationReviewer,
)

__all__ = [
    # Code Quality
    "StyleGuideReviewer",
    "NamingConventionsReviewer",
    "DocumentationReviewer",
    # Content Quality
    "ResponseRelevanceReviewer",
    "ConstraintsConsistencyReviewer",
    "MissingApproachesReviewer",
    "CodeElementsExistenceReviewer",
    "ExampleWalkthroughReviewer",
    "ComplexityCorrectnessReviewer",
    "ConclusionQualityReviewer",
    "ProblemConsistencyReviewer",
    "SolutionPassabilityReviewer",
    "MetadataCorrectnessReviewer",
    "UniqueSolutionReviewer",
    "TimeComplexityAuthenticityReviewer",
    "TestCaseValidationReviewer",
    "SampleDryRunValidationReviewer",
    "NoteSectionReviewer",
    "InefficientLimitationsReviewer",
    "FinalApproachDiscussionReviewer",
    "NoCodeInReasoningReviewer",
    "TimeLimitValidationReviewer",
    "MemoryLimitValidationReviewer",
    # Structure Quality
    "SubtopicTaxonomyReviewer",
    "TypoCheckReviewer",
    "SubtopicRelevanceReviewer",
    "MissingSubtopicsReviewer",
    "PredictiveHeadingsReviewer",
    "MathEquationsReviewer",
    "MathFormattingReviewer",
    # Limits Consistency
    "LimitsConsistencyReviewer",
    # Example Validation
    "ExampleValidationReviewer",
]
