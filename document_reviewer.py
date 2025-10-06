#!/usr/bin/env python3
"""
Document Review Script using Anthropic Claude Opus 4.1 with Extended Thinking - Ultimate Point Analysis

This script reads a document from a specified text file and performs comprehensive review checks
using Claude Opus 4.1 with extended thinking enabled across multiple specialized review points. 
Each review point is performed by a specialized reviewer class with targeted prompts for maximum precision.

Features:
- Comprehensive review points covering all aspects of document quality
- Primary: Claude Opus 4.1 with 30k thinking budget for exceptional reasoning
- Secondary: Claude Sonnet 4 for cleanup operations  
- Code style guide and naming convention compliance for C++ and Python (Points 1-3)
- Response quality and mathematical correctness (Points 4-11) 
- Problem statement and solution validation (Points 12-17)
- Reasoning chain analysis and approach evaluation (Points 18-21)
- Subtopic taxonomy and completeness validation (Points 22-25)
- Chain 2 test case analysis validation (Point 26)
- Thought heading violations check (Point 27)
- Comprehensive reasoning thoughts review (Point 28)
- Extended thinking provides deep analysis with step-by-step reasoning

Author: AI Assistant
Date: September 29, 2025
"""

import os
import sys
import argparse
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
import time
from anthropic import Anthropic

class ReviewResult(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"

@dataclass
class ReviewResponse:
    result: ReviewResult
    reasoning: str
    score: Optional[float] = None
    details: Optional[str] = None

class BaseReviewer:
    """Base class for all document reviewers"""
    
    def __init__(self, client: Anthropic):
        self.client = client
        # Primary model: Claude Opus 4.1 with thinking enabled for main review calls
        self.primary_model = "claude-opus-4-1-20250805"  # Claude Opus 4.1 - Exceptional reasoning
        # Secondary model: Claude Sonnet 4 for cleanup calls (not fallback)
        self.secondary_model = "claude-sonnet-4-20250514"  # Claude Sonnet 4 - High performance model
    
    def review(self, document: str) -> ReviewResponse:
        """Perform the review and return structured results"""
        raise NotImplementedError("Subclasses must implement review method")
    
    def _clean_failure_response(self, failure_response: str) -> str:
        """Make a second AI call using Sonnet 4 to clean up failure response, keeping only failure-related content"""
        cleanup_prompt = """
You are an expert at extracting and cleaning failure information. 

TASK: Extract and present ONLY the failure-related information from the provided response. Remove all unnecessary text, explanations, and formatting while keeping every single instance of failure.

CRITICAL REQUIREMENTS:
1. Keep EVERY instance of failure, even if the same error appears multiple times
2. Keep ALL violation locations (CHAIN_XX, THOUGHT_XX_YY, section names) exactly as specified
3. Keep ALL specific quotes and examples that show violations
4. Remove all introductory text, long explanations, and verbose descriptions
5. Present failures in a clear, concise format with bullet points
6. Keep specific examples of violations and suggested fixes
7. Remove any "PASS" sections or successful parts
8. Keep the essential failure details but make them concise
9. If there are code examples, keep only the essential violation examples and fixes
10. Remove repetitive explanations but keep all distinct failure instances
11. DO NOT include "improved code examples", "alternative options", or multiple code variations
12. DO NOT include "Option 1", "Option 2" or similar alternative implementations
13. Focus only on what is wrong and the direct fix needed
14. PRESERVE ALL LOCATION INFORMATION - do not summarize or omit any CHAIN_XX or THOUGHT_XX_YY references
15. PRESERVE ALL SPECIFIC QUOTES that demonstrate violations

FORMAT: Present as a clean, bulleted list of failures with specific examples, quotes, and exact locations.

CRITICAL: Do NOT summarize multiple violations into general statements. Each violation must be listed separately with its exact location.

IMPORTANT: Focus on actionable failure information that helps the user understand what needs to be fixed. Avoid providing multiple code alternatives or improved examples.

Original Response:
"""
        
        try:
            # Use Sonnet 4 for cleanup to keep it simple and fast
            message = self.client.messages.create(
                model=self.secondary_model,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": f"{cleanup_prompt}\n\n{failure_response}"
                    }
                ]
            )
            cleaned_response = message.content[0].text.strip()
            
            # Add a small delay to respect API rate limits for the cleanup call
            import time
            time.sleep(0.5)
            
            return cleaned_response
        except Exception as e:
            # If cleanup fails, return original response
            return f"[Cleanup failed: {str(e)}]\n\n{failure_response}"

    def _make_api_call(self, prompt: str, document: str) -> str:
        """Make API call to Claude Opus 4.1 with thinking enabled and streaming"""
        thinking_budget = 30000  # Large thinking budget for complex analysis
        max_output = 32000  # Maximum output tokens for Opus 4.1
        
        # Use streaming for large requests as required by API
        response_text = ""
        thinking_words = 0
        
        with self.client.messages.stream(
            model=self.primary_model,
            max_tokens=max_output,
            temperature=1.0,  # Must be 1.0 when thinking is enabled
            thinking={
                "type": "enabled",
                "budget_tokens": thinking_budget
            },
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n=== DOCUMENT TO REVIEW ===\n{document}"
                }
            ]
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, 'text') and event.delta.text:
                        response_text += event.delta.text
                    elif hasattr(event.delta, 'thinking') and event.delta.thinking:
                        thinking_words += len(event.delta.thinking.split())
                        
        return response_text if response_text else "No text content in response"
    
    def _parse_response(self, response: str) -> ReviewResponse:
        """Parse the LLM response to extract pass/fail and reasoning"""
        response_lower = response.lower()
        
        # Look for clear pass/fail indicators
        if "final verdict: pass" in response_lower or "conclusion: pass" in response_lower:
            result = ReviewResult.PASS
            # For PASS, extract only the verdict line, not full details
            lines = response.split('\n')
            for line in lines:
                if 'final verdict: pass' in line.lower() or 'conclusion: pass' in line.lower():
                    reasoning = line.strip()
                    break
            else:
                reasoning = "PASS - Review completed successfully"
        elif "final verdict: fail" in response_lower or "conclusion: fail" in response_lower:
            result = ReviewResult.FAIL
            # For FAIL, clean up the response with a second AI call
            reasoning = self._clean_failure_response(response.strip())
        elif "✅" in response or "pass" in response_lower.split()[-20:]:  # Check last 20 words
            result = ReviewResult.PASS
            reasoning = "PASS - Review completed successfully"
        elif "❌" in response or "fail" in response_lower.split()[-20:]:
            result = ReviewResult.FAIL
            # For FAIL, clean up the response with a second AI call
            reasoning = self._clean_failure_response(response.strip())
        else:
            # Default to FAIL if unclear
            result = ReviewResult.FAIL
            # Clean up ambiguous responses too
            reasoning = self._clean_failure_response(response.strip() + "\n\n[NOTE: Response was ambiguous, defaulting to FAIL]")
        
        return ReviewResponse(
            result=result,
            reasoning=reasoning
        )

class ReviewPrompts:
    """Centralized prompts for different review processes - Ultimate comprehensive analysis"""
    
    # Point 0: Problem Originality Check
    @staticmethod
    def get_problem_originality_prompt():
        """Check if the problem is original or copied from competitive programming platforms"""
        return """
You are an expert competitive programming analyst with deep knowledge of problems from Codeforces, AtCoder, CodeChef, LeetCode, HackerRank, and other major competitive programming platforms.

**TASK:** Search the internet (especially Codeforces, AtCoder, CodeChef, LeetCode, HackerRank, TopCoder, SPOJ) for problems similar to this one. Check if it is original, inspired, or copied.

**ANALYSIS STEPS:**
1. **[THINK DEEPLY]** - Use extended thinking to carefully analyze the problem
2. **Comprehensive Search Strategy:** Perform extensive searches across:
   - **Google Search**: Use targeted Google queries with problem keywords, constraints, and concepts
   - **Competitive Programming Platforms**: Codeforces, AtCoder, CodeChef, LeetCode, HackerRank, TopCoder, SPOJ
   - **Academic Sources**: GitHub, research papers, educational sites
   - **Community Forums**: StackOverflow, Reddit, Discord communities
   - **Online Judges**: Various online judge platforms and contest archives

3. **Search Queries to Use:**
   - Exact title searches on Google
   - Key concept + constraint searches (e.g., "dynamic programming N<=10^5")
   - Algorithm-specific searches (e.g., "segment tree range query")
   - Sample input/output pattern searches
   - Mathematical formulation searches

4. **Comparison Points:**
   - Title similarity (exact or near-exact matches)
   - Problem statement similarity (core concept, story, setup)
   - Constraint ranges (N, M values, time limits, etc.)
   - Sample input/output format and values
   - Expected algorithm/approach and complexity
   - Mathematical formulations and edge cases

**CLASSIFICATION:**
- **ORIGINAL:** No similar problems found, or only very general algorithmic concepts shared
- **INSPIRED:** Similar core concept but different constraints, format, or twist
- **COPIED:** Nearly identical problem statement, constraints, and samples
- **VARIANT:** Modified version of existing problem with different parameters

**CRITICAL VIOLATION REPORTING:**
- If COPIED or direct VARIANT is found, provide:
  - Exact source URL and problem name
  - Platform name and contest/problem ID
  - Specific similarities (title, statement, constraints, samples)
  - Percentage similarity assessment
- Report ALL similar problems found, not just the closest match

Take your time to compare title, statement, constraints, and samples thoroughly.

RESPONSE FORMAT:
Provide detailed analysis with search results, then end with:
FINAL VERDICT: PASS (if ORIGINAL/INSPIRED) or FINAL VERDICT: FAIL (if COPIED/direct VARIANT)
"""

    # Point 1: Style Guide Compliance
    @staticmethod
    def get_style_guide_prompt():
        """Check if code follows style guide"""
        return """
You are an expert code reviewer. 

**STEP 1: LANGUAGE DETECTION**
First, carefully analyze the document to determine the programming language by:
1. Looking for code blocks in the response section (not reasoning chains)
2. Examining syntax patterns, keywords, and structure
3. Identifying language-specific elements like:
   - C++: #include, std::, namespace, class/struct with public/private, semicolons, curly braces, template<>, vector<int>, iostream, using namespace std
   - Python: def, class without access modifiers, indentation-based blocks, import statements, snake_case, if __name__ == "__main__"
4. State your conclusion: "DETECTED LANGUAGE: [C++ or Python]"

**STEP 2: STYLE GUIDE ANALYSIS**
Based on the detected language, analyze the code against the appropriate style guide:

**General Style Guide Requirements:**
* a. Variables and functions are expected to be named in an explicit and easy-to-understand way 
* b. Standard and natural coding style is expected, instead of multiple unnecessary inlines / typedefs / templates etc. If an unnatural structure is applied, an explanation is expected. 
* c. Avoid vague abbreviations 
* d. If an unnatural const is defined, an explanation is expected.

**C++ Style Guide:**

1. Naming Conventions:
  + Use lowerCamelCase for variables and functions, e.g., inventory, numberOfDays().
  + Class names should be in UpperCamelCase, e.g., InventoryManager.
  + Constants should be named in kCamelCase, e.g., kDefaultTimeout.

2. Quoting:
Use standard double quotes " for string literals and single quotes ' only for single characters.

3. Indentation:
Use 4 spaces per indentation level. Do not use tabs.

4. Comments:
Use // for single-line comments. For longer comments or explanatory notes, use /* ... */. Place a space after the comment delimiter and capitalize the first letter of the comment. For example:
  ``` c++
  // Comment about the following line of code.

  /*
  * Block Comment: Explanation of the upcoming code section.
  */
  ```

    Remember to keep comments concise and meaningful.

**Python Style Guide:**

1. Code Readability and Style:
- Follow the PEP 8 guidelines for Python code style.
- Use meaningful variable, function, and class names that reflect their purpose.
- Use snake_case for variable, function, and module names.
- Use PascalCase (also known as CamelCase) for class names.
- Limit each line to 79 characters to maintain readability.
- Use proper indentation (4 spaces, no tabs).

2. Documentation and Comments
- Write clear and concise docstrings for all modules, classes, and functions, and also add type hints without using the "typing" module.

```python
def compute_inventory_count(include_reserved: bool) -> int:
    '''
    Computes the total number of items in the inventory.
   
    Args:
        include_reserved: If True, includes reserved items in the total count.

    Returns:
        The total number of items.
    '''     
```
- Use comments to explain complex or non-obvious parts of your code.
- Avoid redundant comments; ensure comments add value to the reader's understanding.
- Don't use type hint from the Typing library.

3. Dependencies and Environment
- Avoid using external libraries or dependencies.
- Aim to write code that is compatible with default Python libraries.
- Ensure your code can run seamlessly in environments like Google Colab or CodeForces without requiring the installation of additional libraries.

CRITICAL VIOLATION REPORTING:
- Report ALL violations with exact locations (line numbers, function names, class names where applicable)
- Provide specific quotes of violating code
- Do NOT summarize or omit any violations
- Include the exact location where each violation occurs

Please answer pass or fail and provide specific areas where a rule/guide is violated and suggest how to fix it.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 2: Naming Conventions
    @staticmethod
    def get_naming_conventions_prompt():
        """Check naming conventions"""
        return """
You are an expert code reviewer.

**STEP 1: LANGUAGE DETECTION**
First, carefully analyze the document to determine the programming language by:
1. Looking for code blocks in the response section (not reasoning chains)
2. Examining syntax patterns, keywords, and structure
3. Identifying language-specific elements like:
   - C++: #include, std::, namespace, class/struct with public/private, semicolons, curly braces, template<>, vector<int>, iostream, using namespace std
   - Python: def, class without access modifiers, indentation-based blocks, import statements, snake_case, if __name__ == "__main__"
4. State your conclusion: "DETECTED LANGUAGE: [C++ or Python]"

**STEP 2: NAMING CONVENTIONS ANALYSIS**
Check if the provided code follows the appropriate Naming Conventions based on the detected programming language:

**C++ Naming Conventions:**
* 1. Use kCamelCase for constants (e.g., `kMaxN`, `kInfinity`).
* 2. Use UpperCamelCase for class and struct names (e.g., `InventoryManager`, `Solver`, `Node`). 
* 3. Use lowerCamelCase for variables and functions (e.g., `visited`, `inventory`, `numberOfDays`, `numberOfElements`, `totalNodes`).

**Python Naming Conventions:**
* 1. Use UPPER_CASE_WITH_UNDERSCORES for constants (e.g., `MAX_N`, `INFINITY`).
* 2. Use PascalCase for class names (e.g., `InventoryManager`, `Solver`, `Node`).
* 3. Use snake_case for variables, functions, and module names (e.g., `visited`, `inventory`, `number_of_days`, `number_of_elements`, `total_nodes`).
* 4. Use snake_case for method names and instance variables.
* 5. Use leading underscore for internal use (e.g., `_internal_method`).

CRITICAL VIOLATION REPORTING:
- Report ALL violations with exact locations (line numbers, function names, variable names)
- Provide specific quotes of violating names
- Do NOT summarize or omit any violations
- List each violating identifier separately

Please answer pass or fail and provide specific areas where a rule is violated and suggest how to fix it.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 3: Documentation
    @staticmethod
    def get_documentation_prompt():
        """Check appropriate documentation style"""
        return """
You are an expert code reviewer.

**STEP 1: LANGUAGE DETECTION**
First, carefully analyze the document to determine the programming language by:
1. Looking for code blocks in the response section (not reasoning chains)
2. Examining syntax patterns, keywords, and structure
3. Identifying language-specific elements like:
   - C++: #include, std::, namespace, class/struct with public/private, semicolons, curly braces, template<>, vector<int>, iostream, using namespace std
   - Python: def, class without access modifiers, indentation-based blocks, import statements, snake_case, if __name__ == "__main__"
4. State your conclusion: "DETECTED LANGUAGE: [C++ or Python]"

**STEP 2: DOCUMENTATION ANALYSIS**
Check if the provided code uses appropriate documentation style for all functions, classes, and public APIs to specify arguments, return values, and any relevant details.

**C++ Documentation Requirements:**
- Use doxygen-style comments for all functions, classes, and public APIs
- Specify arguments, return values, and relevant details

**Python Documentation Requirements:**
- Write clear and concise docstrings for all modules, classes, and functions
- Add type hints without using the "typing" module
- Follow the format:
```python
def function_name(parameter: type) -> return_type:
    '''
    Brief description of the function.
   
    Args:
        parameter: Description of the parameter.

    Returns:
        Description of what is returned.
    '''
```
- Use comments to explain complex or non-obvious parts of code
- Avoid redundant comments that don't add value

CRITICAL VIOLATION REPORTING:
- Report ALL violations with exact locations (function names, class names)
- Identify which functions/classes lack proper documentation
- Do NOT summarize or omit any violations

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""
    
    # Point 4: Response Relevance to Problem
    @staticmethod
    def get_response_relevance_prompt():
        """Check if response section is relevant to problem description"""
        return """
You are an expert response evaluator. Check if every thought and response section is relevant to the provided problem description.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 5: Mathematical Equations Correctness
    @staticmethod
    def get_math_equations_prompt():
        """Check mathematical equations correctness"""
        return """
You are an expert response evaluator. Check if the mathematical equations are correct if there are any.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 6: Problem Constraints Consistency
    @staticmethod
    def get_constraints_consistency_prompt():
        """Check if defined problem constraints match problem description"""
        return """
You are an expert response evaluator. Check if the defined problem constraints are identical to those in the problem description.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 7: Missing Approaches in Steps
    @staticmethod
    def get_missing_approaches_prompt():
        """Check if any approaches or data structures are not explained in approach steps"""
        return """
You are an expert response evaluator. Check if any missing approaches or data structures are not explained in the approach steps.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 8: Code Elements Existence
    @staticmethod
    def get_code_elements_existence_prompt():
        """Check if mentioned variables, functions, and classes exist in code"""
        return """
You are an expert response evaluator. Variables, functions, and classes mentioned in the response should exist in the provided code.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 9: Example Walkthrough with Optimal Algorithm
    @staticmethod
    def get_example_walkthrough_prompt():
        """Check if response has example walkthrough with optimal algorithm"""
        return """
You are an expert response evaluator. Response section should have an example walkthrough with the optimal algorithm.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 10: Time and Space Complexity Correctness
    @staticmethod
    def get_complexity_correctness_prompt():
        """Check time and space complexity correctness"""
        return """
You are an expert response evaluator. Ensure the time complexity and space complexity are mentioned correctly. Check if the time complexity and space complexity are correct according to the provided code.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 11: Conclusion Quality
    @staticmethod
    def get_conclusion_quality_prompt():
        """Check conclusion quality"""
        return """
You are an expert response evaluator. The conclusion should be a brief conclusion about the response section.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 12: Problem Statement Consistency
    @staticmethod
    def get_problem_consistency_prompt():
        """Check problem statement consistency"""
        return """
You are an expert response evaluator. Is the problem statement consistent?

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 13: Solution Passability According to Limits
    @staticmethod
    def get_solution_passability_prompt():
        """Check if solution is passable according to limits"""
        return """
You are an expert response evaluator. According to given limits, is this solution passable?

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 14: Metadata Correctness
    @staticmethod
    def get_metadata_correctness_prompt():
        """Check metadata correctness"""
        return """
You are an expert response evaluator. Is the metadata correct?

METADATA VALIDATION REQUIREMENTS:
The document MUST contain a metadata section at the beginning that follows this EXACT format:

# Metadata

**Category:** - [value]

**Topic:** - [value]

**Subtopic:** - [JSON array of subtopics]

**Difficulty:** - [difficulty level]

**Languages:** - [programming languages]

**Number of Approaches:** - [approach count and complexity progression]

**Number of Chains:** - [number]

REQUIRED FORMAT SPECIFICATIONS:
1. Must start with "# Metadata" header
2. Each field must use the pattern: **FieldName:** - value
3. There must be a space after the colon, then a dash, then a space before the value
4. All fields must be present in this exact order
5. The subtopic must be a valid JSON array format with proper quotes

CRITICAL VALIDATION FOR "Number of Chains":
- Count all reasoning chains in the document with format **[CHAIN_01]**, **[CHAIN_02]**, etc.
- The stated number must exactly match the actual count of CHAIN_XX sections in the document
- Do NOT count THOUGHT_XX_YY items - only count CHAIN_XX items
- Format must be exactly: **Number of Chains:** - [number]
- Example: If document has CHAIN_01 through CHAIN_10, metadata must show "**Number of Chains:** - 10"

WHAT TO CHECK:
1. Metadata section exists with "# Metadata" header
2. All required fields are present in correct order
3. Each field follows the exact format: **FieldName:** - value
4. Number of Chains matches actual CHAIN_XX sections count
5. Subtopic is a properly formatted JSON array
6. Values are appropriate for the content

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 15: Time Complexity Authenticity Check
    @staticmethod
    def get_time_complexity_authenticity_prompt():
        """Check if time complexity in metadata is authentic and properly formatted"""
        return """
You are an expert response evaluator. Check if the time complexity mentioned in the metadata section meets ALL of the following requirements:

**REQUIREMENTS:**
1. **Overall Complexity Only**: The metadata must mention ONLY the overall time complexity, not individual step complexities
2. **No Extra Text**: Must NOT contain any descriptive text, approach explanations, or space complexity mentions
3. **Variable-Based**: Time complexity must be expressed ONLY using variables mentioned in the problem statement (e.g., if problem mentions N, M, K, then use those exact variables)
4. **Correctness**: The stated time complexity must be mathematically correct for the provided solution

**ACCEPTABLE FORMATS:**
- O(N)
- O(N log N)
- O(N * M)
- O(N^2)
- O(K * log N)

**UNACCEPTABLE FORMATS:**
- "O(N) for the main loop and O(log N) for binary search" (individual step breakdown)
- "O(N) using dynamic programming approach" (contains approach description)
- "Time: O(N), Space: O(1)" (mentions space complexity)
- "O(n)" (wrong variable case if problem uses N)
- "O(size)" (using variable not mentioned in problem statement)

**VALIDATION STEPS:**
1. Locate the time complexity statement in metadata
2. Verify it contains ONLY the overall complexity expression
3. Confirm all variables used are from the problem statement
4. Check if the complexity is mathematically sound for the solution

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 16: Test Case Validation (Note: Point 15 in user's list but numbered as 16)
    @staticmethod
    def get_test_case_validation_prompt():
        """Validate test cases against code and problem statement"""
        return """
You are an expert response evaluator. Validate the examples of the test cases in chain 2 on the code and in the problem statement, and check if explanations are correct.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 17: Sample Test Case Dry Run Validation
    @staticmethod
    def get_sample_dry_run_validation_prompt():
        """Check if dry runs or explanations of sample test cases match the given examples exactly"""
        return """
You are an expert response evaluator. If the document contains any dry runs, step-by-step explanations, or walkthroughs of test cases that claim to be from the given samples or examples, verify that they exactly match the provided sample inputs and outputs.

WHAT TO CHECK:
- Any section that says "let's trace through the first example", "using the given sample", "from the provided test case", etc.
- Step-by-step walkthroughs of algorithm execution on sample data
- Dry runs that claim to demonstrate the solution on provided examples
- Manual calculations or traces using the sample inputs

VALIDATION REQUIREMENTS:
- Input values must exactly match the sample input
- Each step of the calculation/algorithm must be correct
- Final output must exactly match the expected sample output
- Intermediate values and steps must be mathematically sound
- No errors in arithmetic, logic, or algorithm execution

WHAT NOT TO CHECK:
- Custom examples created for illustration (not claiming to be from samples)
- General algorithm explanations without specific sample data
- Abstract walkthroughs that don't reference the given examples

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 18: Note Section Explanation (Point 18 in user's list)
    @staticmethod
    def get_note_section_prompt():
        """Check note section explanation approach - only applies to problem statement/prompt section"""
        return """
You are an expert response evaluator. 

IMPORTANT SCOPE CLARIFICATION:
This check ONLY applies to the **[Prompt]** section or problem statement section of the document. Other sections like **[Assistant]**, reasoning chains (CHAIN_XX), thoughts (THOUGHT_XX_YY), or solution sections are allowed to expose solutions and implementation details without restriction.

WHAT TO CHECK:
- Focus ONLY on the **[Prompt]** section or main problem statement
- The problem statement itself should not reveal the solution approach
- Any "Note" or "Explanation" subsections within the problem statement should explain the output in relation to the problem requirements, not by analyzing the solution methodology
- The problem statement should present the challenge without giving away algorithmic insights or implementation strategies

WHAT NOT TO CHECK:
- Do not evaluate **[Assistant]** sections
- Do not evaluate CHAIN_XX reasoning sections  
- Do not evaluate THOUGHT_XX_YY sections
- Do not evaluate solution code or explanations outside the problem statement
- Other sections are free to contain complete solutions, algorithms, and implementation details

Please answer pass or fail based only on whether the **[Prompt]** section appropriately presents the problem without solution exposure.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 19: Inefficient Approaches Limitations (Point 19 in user's list)
    @staticmethod
    def get_inefficient_limitations_prompt():
        """Check if inefficient approaches mention limitations"""
        return """
You are an expert response evaluator. For the inefficient approaches, ensure that the chain mentions the limitations/disadvantages/cons of the approach and why we need to shift to a new approach.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 20: Final Approach Discussion (Point 21 in user's list)
    @staticmethod
    def get_final_approach_discussion_prompt():
        """Check final approach discussion completeness"""
        return """
You are an expert response evaluator. For the chains discussing the final approach:
a. Ensure that the chains mention the improvements that are done over the previous approach or approaches.
b. Ensure all approaches/data structures used in the provided code are discussed and well-explained.
c. Ensure that there are no extra approaches/data structures/methods are explained but not used in the provided code

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 21: No Code in Reasoning Chains (Point 22 in user's list)
    @staticmethod
    def get_no_code_in_reasoning_prompt():
        """Check if reasoning chains contain code"""
        return """
You are an expert response evaluator. There should not be any code in reasoning chains.

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 22: Subtopic Taxonomy Validation
    @staticmethod
    def get_subtopic_taxonomy_prompt():
        """Check if subtopics are from taxonomy list and relevant to problem"""
        return """
You are an expert response evaluator. Check if ALL subtopics selected in the document are:
1. Present in the taxonomy list below
2. Relevant to the problem and solution

IMPORTANT CLARIFICATION:
- It is NOT a problem if some taxonomy items are not used in the document
- The ONLY requirement is that ALL tags used in the document must be from the taxonomy list AND relevant to the problem
- You should ONLY flag subtopics that are either:
  a) Not found in the taxonomy list, OR
  b) Not relevant to the problem/solution

Taxonomy list: ["Basic Data Structures","Control Structures and Loops","Functions and Recursion","Object-Oriented Programming","Error and Exception Handling","Sorting Algorithms","Searching Algorithms","Graph Algorithms","Dynamic Programming","Greedy Algorithms","Divide and Conquer","Backtracking Algorithms", "Memoization", "Concurrency and Parallelism", "Genetic Algorithms", "Simulated Annealing", "Machine Learning Algorithms", "Deep Learning Frameworks","Natural Language Processing", "Arrays and Lists","Stacks and Queues","Linked Lists","Trees and Tries","Heaps and Priority Queues","Hash Tables","Graphs and Networks", "Web Scraping and Data Collection","Data Visualization","Data Analysis and Statistics","Automated Testing and Debugging","Cryptography and Security","Network Programming","Game Development","Quantum Algorithms","Blockchain Algorithms","Edge Computing Techniques","AI and Neural Network Optimization","Federated Learning","Explainable AI", "Bioinformatics Algorithms","Financial Modeling and Algorithms","Image Processing and Computer Vision","Robotics and Control Algorithms","Natural Language Understanding","Internet of Things (IoT) Algorithms","Spatial Data Analysis","Reinforcement Learning", "Graph Neural Networks","Transformer Models","Zero-Shot Learning","Unsupervised Learning Techniques","AutoML and Hyperparameter Tuning","Recommendation Systems","Fraud Detection","Supply Chain Optimization","Healthcare Data Analysis", "Personalized Marketing", "Autonomous Vehicles","Climate Modeling and Simulation","Algorithm Complexity and Big O Notation","Computational Complexity Theory", "Approximation Algorithms", "Probabilistic Algorithms", "Game Theory"]

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 23: Typo Check (Point 9 from reasoning section)
    @staticmethod
    def get_typo_check_prompt():
        """Check for typos and spelling issues"""
        return """
You are an expert response evaluator. Do the reasoning chains or the response contain typo issues like misspelling?

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 24: Subtopic Relevance (Point 24 in user's list)
    @staticmethod
    def get_subtopic_relevance_prompt():
        """Check if selected subtopics are relevant"""
        return """
You are an expert response evaluator. Are the selected subtopics relevant to the problem/the solution/the inefficient approaches in the reasoning chains?

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 25: Missing Relevant Subtopics (Point 25 in user's list)
    @staticmethod
    def get_missing_subtopics_prompt():
        """Identify missing relevant subtopics"""
        return """
You are an expert response evaluator. Identify from the taxonomy subtopics list if any missing subtopics could be relevant to the problem but not selected and provide them in a list. If the list is non-empty, its a fail.

Use this taxonomy list: ["Basic Data Structures","Control Structures and Loops","Functions and Recursion","Object-Oriented Programming","Error and Exception Handling","Sorting Algorithms","Searching Algorithms","Graph Algorithms","Dynamic Programming","Greedy Algorithms","Divide and Conquer","Backtracking Algorithms", "Memoization", "Concurrency and Parallelism", "Genetic Algorithms", "Simulated Annealing", "Machine Learning Algorithms", "Deep Learning Frameworks","Natural Language Processing", "Arrays and Lists","Stacks and Queues","Linked Lists","Trees and Tries","Heaps and Priority Queues","Hash Tables","Graphs and Networks", "Web Scraping and Data Collection","Data Visualization","Data Analysis and Statistics","Automated Testing and Debugging","Cryptography and Security","Network Programming","Game Development","Quantum Algorithms","Blockchain Algorithms","Edge Computing Techniques","AI and Neural Network Optimization","Federated Learning","Explainable AI", "Bioinformatics Algorithms","Financial Modeling and Algorithms","Image Processing and Computer Vision","Robotics and Control Algorithms","Natural Language Understanding","Internet of Things (IoT) Algorithms","Spatial Data Analysis","Reinforcement Learning", "Graph Neural Networks","Transformer Models","Zero-Shot Learning","Unsupervised Learning Techniques","AutoML and Hyperparameter Tuning","Recommendation Systems","Fraud Detection","Supply Chain Optimization","Healthcare Data Analysis", "Personalized Marketing", "Autonomous Vehicles","Climate Modeling and Simulation","Algorithm Complexity and Big O Notation","Computational Complexity Theory", "Approximation Algorithms", "Probabilistic Algorithms", "Game Theory"]

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 26: Predictive Headings in Thoughts
    @staticmethod
    def get_predictive_headings_prompt():
        """Check for predictive headings in thoughts"""
        return """
You are an expert response evaluator. Check if there are predictive headings specifically in THOUGHTS (THOUGHT_XX_YY format) that reveal solutions or approaches.

IMPORTANT DISTINCTION:
- ✅ CHAIN_XX: Predictive headings are ALLOWED (e.g., "CHAIN_03: Implementing brute force approach")
- ❌ THOUGHT_XX_YY: Predictive headings are NOT ALLOWED (e.g., "THOUGHT_03_02: The efficient way is to use hash tables")

WHAT TO CHECK:
- Only examine THOUGHT_XX_YY headings for predictive content
- Ignore CHAIN_XX headings - they can be predictive
- Look for thoughts that reveal solutions, approaches, or outcomes before analysis
- Non-predictive thought headings are acceptable (e.g., "THOUGHT_01_01: List of things we need to check")

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 27: Chain 2 Test Case Analysis Validation
    @staticmethod
    def get_chain2_testcase_analysis_prompt():
        """Check if Chain 2 actually performs test case analysis"""
        return """
You are an expert response evaluator. Check if Chain 2 (CHAIN_02) actually performs detailed test case analysis with step-by-step execution, rather than just suggesting test cases that need to be analyzed.

REQUIREMENTS FOR CHAIN 2:
- Must contain actual step-by-step analysis of test cases
- Must show detailed execution traces or walkthroughs
- Must demonstrate how the algorithm works on specific examples
- Must NOT be just suggestions like "we should test case X" or "consider testing edge case Y"

WHAT TO LOOK FOR (PASS criteria):
- Actual step-by-step execution of test cases
- Detailed walkthroughs showing algorithm behavior
- Concrete examples with input/output analysis
- Manual tracing through algorithm steps

WHAT COUNTS AS FAIL:
- Only suggestions for test cases without actual analysis
- Vague statements like "we need to test edge cases"
- Lists of test cases without execution details
- General recommendations without concrete analysis

Please provide ALL violations with exact locations (CHAIN_XX, THOUGHT_XX_YY) and specific quotes.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 28: Thought Heading Violations
    @staticmethod
    def get_thought_heading_violations_prompt():
        """Check if thoughts have prohibited headings"""
        return """
You are an expert response evaluator. Check if any THOUGHT_XX_YY sections contain prohibited headings or titles.

CRITICAL REQUIREMENTS:
- THOUGHT_XX_YY sections must NOT have any headings or titles
- Thoughts should contain only analysis content, not descriptive headings
- Any heading-like text in thoughts is a violation

PROHIBITED EXAMPLES (these are VIOLATIONS):
- "Going for best approach: ..."
- "Optimizing approach: ..."
- "Analyzing complexity: ..."
- "Edge cases consideration: ..."
- "Algorithm selection: ..."
- Any colon-followed descriptions that act as headings

ACCEPTABLE CONTENT:
- Direct analysis without headings
- Plain explanatory text
- Questions and reasoning without title formatting

INSTRUCTIONS:
1. Examine EVERY THOUGHT_XX_YY section systematically
2. Identify ALL violations with exact THOUGHT_XX_YY numbers
3. Provide the exact heading text that violates the rule
4. List ALL violations - do not summarize or omit any

Please provide ALL violations with exact locations (THOUGHT_XX_YY) and the specific prohibited heading text.

RESPONSE FORMAT:
For each violation, use this format:
• **[THOUGHT_XX_YY]**: "[Exact prohibited heading text]"

If no violations found, state "No heading violations found in thoughts."

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Point 29: Reasoning Thoughts Review Process
    @staticmethod
    def get_reasoning_thoughts_review_prompt():
        """Comprehensive review of reasoning thought chains"""
        return """
You are an expert response evaluator specializing in reasoning chain analysis. You must conduct an extremely thorough review of the reasoning thought chains with maximum attention to detail.

TASK: Review the reasoning thought chains for comprehensive analysis of thought processes and development from simple to optimized solutions.

CRITICAL ANALYSIS REQUIREMENTS:

1. **Style and Structure Analysis** (Apply to ALL chains):
   a. Reasoning chains should follow manuscript style - conclusions come AFTER analysis
   b. Avoid "presentation-style" reasoning where conclusions are given first, followed by supporting arguments
   c. Avoid any predictive statements without prior analysis, EXCEPT for very obvious cases (e.g., "if L = R, then length = 1", "empty array has size 0", basic arithmetic like "2 + 2 = 4")
   d. **Special check for Chain 1 and Chain 2 ONLY**: Ensure they don't contain information about approaches or data structures that are efficient or inefficient in solving the problem

   **IMPORTANT EXCEPTION for criterion (a), (b), (c)**: Do NOT flag conclusions that are immediately obvious or trivial mathematical facts that require no analysis. Examples of acceptable obvious conclusions:
   - Basic arithmetic: "if we have 5 elements, the array size is 5"
   - Range calculations: "if L = R, the range contains exactly 1 element"
   - Simple conditionals: "if the array is empty, no operations are needed"
   - Direct definitions: "a palindrome reads the same forwards and backwards"
   - Immediate logical implications: "if all elements are equal, no changes are needed"
   
   Only flag conclusions that involve non-trivial insights, complex algorithms, or problem-specific discoveries that should be derived through analysis.

2. **Information Quality Assessment** (Apply to ALL thoughts):
   a. Each thought should provide sufficient information for analysis
   b. Information must be factually accurate according to the chain context
   c. No redundant, repeated, or similar data compared to previous thoughts
   d. Account for dependencies between chains or thoughts

CRITICAL VIOLATION REPORTING:
- Report ALL violations with exact locations (CHAIN_XX, THOUGHT_XX_YY)
- Provide specific quotes and context for each violation
- Do NOT summarize or omit any violations
- Include the exact section/thought number where each issue occurs

ANALYSIS METHODOLOGY:
- Review EVERY single thought in EVERY chain systematically
- Check each thought against ALL criteria
- Be extremely precise in identifying issues
- Do not miss any violations or create false positives
- Consider context and dependencies carefully

RESPONSE FORMAT:
For each discovered issue, use this exact format:

• **[THOUGHT_XX_YY]**:
  - [Exact context/quote] - [Issue explanation according to criteria]
  - [Exact context/quote] - [Issue explanation according to criteria]

If no issues found in a thought, do not mention it.
If no issues found overall, state "No issues found in reasoning chains."

CRITICAL: Use VERY EXTENDED THINKING to ensure comprehensive analysis. Miss no issues and create no false positives.

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

# Ultimate Individual Reviewer Classes - One for each review point

class ProblemOriginalityReviewer(BaseReviewer):
    """Point 0: Reviews problem originality against competitive programming platforms"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_problem_originality_prompt()
        response = self._make_api_call_with_web_search(prompt, document)
        return self._parse_response(response)
    
    def _make_api_call_with_web_search(self, prompt: str, document: str) -> str:
        """Make API call to Claude with web search enabled for originality checking"""
        thinking_budget = 30000  # Large thinking budget for complex analysis
        max_output = 32000  # Maximum output tokens
        
        # Web search tool configuration - comprehensive search including Google and major platforms
        web_search_tool = {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 20,  # Generous limit for thorough checking across multiple platforms
            # No domain restrictions to allow Google, GitHub, StackOverflow, and all CP platforms
        }
        
        response_text = ""
        
        with self.client.messages.stream(
            model=self.primary_model,
            max_tokens=max_output,
            temperature=1.0,  # Must be 1.0 when thinking is enabled
            thinking={
                "type": "enabled",
                "budget_tokens": thinking_budget
            },
            tools=[web_search_tool],
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n=== DOCUMENT TO REVIEW ===\n{document}"
                }
            ]
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, 'text') and event.delta.text:
                        response_text += event.delta.text
                        
        return response_text if response_text else "No text content in response"

class StyleGuideReviewer(BaseReviewer):
    """Point 1: Reviews code style guide compliance"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_style_guide_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class NamingConventionsReviewer(BaseReviewer):
    """Point 2: Reviews naming conventions compliance"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_naming_conventions_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class DocumentationReviewer(BaseReviewer):
    """Point 3: Reviews appropriate documentation style"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_documentation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ResponseRelevanceReviewer(BaseReviewer):
    """Point 4: Reviews if response section is relevant to problem description"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_response_relevance_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class MathEquationsReviewer(BaseReviewer):
    """Point 5: Reviews mathematical equations correctness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_math_equations_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ConstraintsConsistencyReviewer(BaseReviewer):
    """Point 6: Reviews if defined problem constraints match problem description"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_constraints_consistency_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class MissingApproachesReviewer(BaseReviewer):
    """Point 7: Reviews if any approaches or data structures are not explained in approach steps (this check is only for the response section, where optimal algorithm is explained)"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_missing_approaches_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class CodeElementsExistenceReviewer(BaseReviewer):
    """Point 8: Reviews if mentioned variables, functions, and classes exist in code"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_code_elements_existence_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ExampleWalkthroughReviewer(BaseReviewer):
    """Point 9: Reviews if response has example walkthrough with optimal algorithm"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_example_walkthrough_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ComplexityCorrectnessReviewer(BaseReviewer):
    """Point 10: Reviews time and space complexity correctness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_complexity_correctness_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ConclusionQualityReviewer(BaseReviewer):
    """Point 11: Reviews conclusion quality"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_conclusion_quality_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ProblemConsistencyReviewer(BaseReviewer):
    """Point 12: Reviews problem statement consistency"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_problem_consistency_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class SolutionPassabilityReviewer(BaseReviewer):
    """Point 13: Reviews if solution is passable according to limits"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_solution_passability_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class MetadataCorrectnessReviewer(BaseReviewer):
    """Point 14: Reviews metadata correctness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_metadata_correctness_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class TimeComplexityAuthenticityReviewer(BaseReviewer):
    """Point 15: Reviews time complexity authenticity in metadata"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_time_complexity_authenticity_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class TestCaseValidationReviewer(BaseReviewer):
    """Point 16: Reviews test cases against code and problem statement"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_test_case_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class SampleDryRunValidationReviewer(BaseReviewer):
    """Point 16: Reviews if dry runs or explanations of sample test cases match the given examples exactly"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_sample_dry_run_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class NoteSectionReviewer(BaseReviewer):
    """Point 17: Reviews note section explanation approach - only applies to problem statement/prompt section"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_note_section_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class InefficientLimitationsReviewer(BaseReviewer):
    """Point 18: Reviews if inefficient approaches mention limitations"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_inefficient_limitations_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class FinalApproachDiscussionReviewer(BaseReviewer):
    """Point 20: Reviews final approach discussion completeness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_final_approach_discussion_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class NoCodeInReasoningReviewer(BaseReviewer):
    """Point 21: Reviews if reasoning chains contain code"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_no_code_in_reasoning_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class SubtopicTaxonomyReviewer(BaseReviewer):
    """Point 22: Reviews if subtopics are from taxonomy list"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_subtopic_taxonomy_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class TypoCheckReviewer(BaseReviewer):
    """Point 23: Reviews for typos and spelling issues"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_typo_check_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class SubtopicRelevanceReviewer(BaseReviewer):
    """Point 24: Reviews if selected subtopics are relevant"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_subtopic_relevance_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class MissingSubtopicsReviewer(BaseReviewer):
    """Point 25: Reviews for missing relevant subtopics"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_missing_subtopics_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class PredictiveHeadingsReviewer(BaseReviewer):
    """Point 26: Reviews for predictive headings in thoughts"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_predictive_headings_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class Chain2TestCaseAnalysisReviewer(BaseReviewer):
    """Point 27: Reviews if Chain 2 performs actual test case analysis"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_chain2_testcase_analysis_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response_no_cleanup(response)

    def _parse_response_no_cleanup(self, response: str) -> ReviewResponse:
        """Parse response without cleanup to preserve detailed violation information"""
        response_lower = response.lower()
        
        if "final verdict: pass" in response_lower or "conclusion: pass" in response_lower:
            result = ReviewResult.PASS
            lines = response.split('\n')
            for line in lines:
                if 'final verdict: pass' in line.lower() or 'conclusion: pass' in line.lower():
                    reasoning = line.strip()
                    break
            else:
                reasoning = "PASS - Chain 2 contains actual test case analysis"
        elif "final verdict: fail" in response_lower or "conclusion: fail" in response_lower:
            result = ReviewResult.FAIL
            reasoning = response.strip()
        elif "✅" in response or "pass" in response_lower.split()[-20:]:
            result = ReviewResult.PASS
            reasoning = "PASS - Chain 2 contains actual test case analysis"
        elif "❌" in response or "fail" in response_lower.split()[-20:]:
            result = ReviewResult.FAIL
            reasoning = response.strip()
        else:
            result = ReviewResult.FAIL
            reasoning = response.strip() + "\n\n[NOTE: Response was ambiguous, defaulting to FAIL]"
        
        return ReviewResponse(result=result, reasoning=reasoning)

class ThoughtHeadingViolationsReviewer(BaseReviewer):
    """Point 28: Reviews for prohibited headings in thoughts"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_thought_heading_violations_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response_no_cleanup(response)

    def _parse_response_no_cleanup(self, response: str) -> ReviewResponse:
        """Parse response without cleanup to preserve detailed violation information"""
        response_lower = response.lower()
        
        if "final verdict: pass" in response_lower or "conclusion: pass" in response_lower:
            result = ReviewResult.PASS
            lines = response.split('\n')
            for line in lines:
                if 'final verdict: pass' in line.lower() or 'conclusion: pass' in line.lower():
                    reasoning = line.strip()
                    break
            else:
                reasoning = "PASS - No prohibited headings found in thoughts"
        elif "final verdict: fail" in response_lower or "conclusion: fail" in response_lower:
            result = ReviewResult.FAIL
            reasoning = response.strip()
        elif "✅" in response or "pass" in response_lower.split()[-20:]:
            result = ReviewResult.PASS
            reasoning = "PASS - No prohibited headings found in thoughts"
        elif "❌" in response or "fail" in response_lower.split()[-20:]:
            result = ReviewResult.FAIL
            reasoning = response.strip()
        else:
            result = ReviewResult.FAIL
            reasoning = response.strip() + "\n\n[NOTE: Response was ambiguous, defaulting to FAIL]"
        
        return ReviewResponse(result=result, reasoning=reasoning)

class ReasoningThoughtsReviewer(BaseReviewer):
    """Point 29: Comprehensive review of reasoning thought chains"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_reasoning_thoughts_review_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response_no_cleanup(response)
    
    def _parse_response_no_cleanup(self, response: str) -> ReviewResponse:
        """Parse response without cleanup for detailed reasoning analysis"""
        response_lower = response.lower()
        
        # Look for clear pass/fail indicators
        if "final verdict: pass" in response_lower or "conclusion: pass" in response_lower:
            result = ReviewResult.PASS
            # For PASS, extract only the verdict line
            lines = response.split('\n')
            for line in lines:
                if 'final verdict: pass' in line.lower() or 'conclusion: pass' in line.lower():
                    reasoning = line.strip()
                    break
            else:
                reasoning = "PASS - Review completed successfully"
        elif "final verdict: fail" in response_lower or "conclusion: fail" in response_lower:
            result = ReviewResult.FAIL
            # No cleanup - keep detailed reasoning as-is
            reasoning = response.strip()
        elif "✅" in response or "pass" in response_lower.split()[-20:]:  # Check last 20 words
            result = ReviewResult.PASS
            reasoning = "PASS - Review completed successfully"
        elif "❌" in response or "fail" in response_lower.split()[-20:]:
            result = ReviewResult.FAIL
            # No cleanup - keep detailed reasoning as-is
            reasoning = response.strip()
        else:
            # Default to FAIL if unclear
            result = ReviewResult.FAIL
            # No cleanup - keep original response
            reasoning = response.strip() + "\n\n[NOTE: Response was ambiguous, defaulting to FAIL]"
        
        return ReviewResponse(result=result, reasoning=reasoning)

class DocumentReviewSystem:
    """Main system orchestrating all reviews"""
    
    def __init__(self):
        # Initialize Anthropic client with API key from environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not found. Please set it in your .bashrc")
        
        self.client = Anthropic(api_key=api_key)
        self.detailed_output = []  # Capture all detailed output for the report
        
        # Initialize all Ultimate reviewers - each as individual API call
        self.reviewers = {
            # Point 0: Problem Originality
            "0. Problem Originality Check": ProblemOriginalityReviewer(self.client),
            
            # Points 1-3: Code Quality
            "1. Style Guide Compliance": StyleGuideReviewer(self.client),
            "2. Naming Conventions": NamingConventionsReviewer(self.client),
            "3. Documentation Standards": DocumentationReviewer(self.client),
            
            # Points 4-11: Response Quality  
            "4. Response Relevance to Problem": ResponseRelevanceReviewer(self.client),
            "5. Mathematical Equations Correctness": MathEquationsReviewer(self.client),
            "6. Problem Constraints Consistency": ConstraintsConsistencyReviewer(self.client),
            "7. Missing Approaches in Steps": MissingApproachesReviewer(self.client),
            "8. Code Elements Existence": CodeElementsExistenceReviewer(self.client),
            "9. Example Walkthrough with Optimal Algorithm": ExampleWalkthroughReviewer(self.client),
            "10. Time and Space Complexity Correctness": ComplexityCorrectnessReviewer(self.client),
            "11. Conclusion Quality": ConclusionQualityReviewer(self.client),
            
            # Points 12-17: Problem Statement and Solution Quality
            "12. Problem Statement Consistency": ProblemConsistencyReviewer(self.client),
            "13. Solution Passability According to Limits": SolutionPassabilityReviewer(self.client),
            "14. Metadata Correctness": MetadataCorrectnessReviewer(self.client),
            "15. Time Complexity Authenticity Check": TimeComplexityAuthenticityReviewer(self.client),
            "16. Test Case Validation": TestCaseValidationReviewer(self.client),
            "17. Sample Test Case Dry Run Validation": SampleDryRunValidationReviewer(self.client),
            "18. Note Section Explanation Approach": NoteSectionReviewer(self.client),
            
            # Points 19-21: Reasoning Chain Quality
            "19. Inefficient Approaches Limitations": InefficientLimitationsReviewer(self.client),
            "20. Final Approach Discussion": FinalApproachDiscussionReviewer(self.client),
            "21. No Code in Reasoning Chains": NoCodeInReasoningReviewer(self.client),
            
            # Points 22+: Subtopic, Taxonomy, and Reasoning Analysis
            "22. Subtopic Taxonomy Validation": SubtopicTaxonomyReviewer(self.client),
            "23. Typo and Spelling Check": TypoCheckReviewer(self.client),
            "24. Subtopic Relevance": SubtopicRelevanceReviewer(self.client),
            "25. Missing Relevant Subtopics": MissingSubtopicsReviewer(self.client),
            "26. No Predictive Headings in Thoughts": PredictiveHeadingsReviewer(self.client),
            "27. Chain 2 Test Case Analysis Validation": Chain2TestCaseAnalysisReviewer(self.client),
            "28. Thought Heading Violations Check": ThoughtHeadingViolationsReviewer(self.client),
            "29. Comprehensive Reasoning Thoughts Review": ReasoningThoughtsReviewer(self.client)
        }
    
    def load_document(self, file_path: str) -> str:
        """Load document from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Document file '{file_path}' not found")
        except Exception as e:
            raise Exception(f"Error reading document: {str(e)}")
    
    def run_reviews(self, document: str, resume_from: int = 0) -> Dict[str, ReviewResponse]:
        """Run all reviews on the document, optionally resuming from a specific point"""
        results = {}
        self.detailed_output = []  # Reset for new run
        
        header_msg = f"🔍 Resuming Ultimate document review from point {resume_from}..." if resume_from > 0 else "🔍 Starting Ultimate document review process..."
        print(header_msg)
        self.detailed_output.append(header_msg)
        
        budget_msg = "💭 Extended thinking enabled with 30,000 token budget per review"
        print(budget_msg)
        self.detailed_output.append(budget_msg)
        
        separator = "=" * 70
        print(separator)
        self.detailed_output.append(separator)
        
        # Convert reviewers dict to list for indexing
        reviewer_items = list(self.reviewers.items())
        
        # Skip to resume point (resume_from is already 0-based)
        start_index = resume_from
        if start_index < 0:
            start_index = 0
        elif start_index >= len(reviewer_items):
            warning_msg = f"⚠️  Resume point {resume_from} is beyond available reviews ({len(reviewer_items)}). Starting from beginning."
            print(warning_msg)
            self.detailed_output.append(warning_msg)
            start_index = 0
        
        # Add skipped reviews as "SKIPPED"
        for i in range(start_index):
            review_name, _ = reviewer_items[i]
            results[review_name] = ReviewResponse(
                result=ReviewResult.PASS,
                reasoning="SKIPPED - Resumed from later point"
            )
        
        for i in range(start_index, len(reviewer_items)):
            review_name, reviewer = reviewer_items[i]
            running_msg = f"\n🔄 Running: {review_name}"
            print(running_msg)
            self.detailed_output.append(running_msg)
            
            # Start timing the review
            start_time = time.time()
            
            try:
                # Add small delay to respect API rate limits
                time.sleep(1)
                
                result = reviewer.review(document)
                
                # Special rule for last point (Comprehensive Reasoning Thoughts Review): Run twice if first attempt passes
                if isinstance(reviewer, ReasoningThoughtsReviewer) and result.result == ReviewResult.PASS:
                    # Calculate and display first run time
                    end_time = time.time()
                    duration_seconds = end_time - start_time
                    duration_minutes = duration_seconds / 60.0
                    
                    first_run_msg = f"⏱️ First run completed in {duration_minutes:.2f} minutes"
                    print(first_run_msg)
                    self.detailed_output.append(first_run_msg)
                    
                    first_result_msg = f"Result: {result.result.value} (First run)"
                    print(first_result_msg)
                    self.detailed_output.append(first_result_msg)
                    
                    second_run_msg = "🔄 Running Point 28 again for confirmation..."
                    print(second_run_msg)
                    self.detailed_output.append(second_run_msg)
                    
                    # Second run
                    second_start_time = time.time()
                    time.sleep(1)  # Rate limit delay
                    second_result = reviewer.review(document)
                    second_end_time = time.time()
                    second_duration_seconds = second_end_time - second_start_time
                    second_duration_minutes = second_duration_seconds / 60.0
                    
                    total_duration_minutes = duration_minutes + second_duration_minutes
                    second_time_msg = f"⏱️ Second run completed in {second_duration_minutes:.2f} minutes"
                    print(second_time_msg)
                    self.detailed_output.append(second_time_msg)
                    
                    total_time_msg = f"⏱️ Total time: {total_duration_minutes:.2f} minutes"
                    print(total_time_msg)
                    self.detailed_output.append(total_time_msg)
                    
                    separator_msg = "-" * 40
                    print(separator_msg)
                    self.detailed_output.append(separator_msg)
                    
                    # Final result based on both runs
                    if second_result.result == ReviewResult.PASS:
                        final_pass_msg = f"Result: ✅ PASS (Both runs passed)"
                        print(final_pass_msg)
                        self.detailed_output.append(final_pass_msg)
                        results[review_name] = ReviewResponse(
                            result=ReviewResult.PASS,
                            reasoning="PASS - Both comprehensive analysis runs completed successfully"
                        )
                    else:
                        final_fail_msg = f"Result: ❌ FAIL (Second run failed)"
                        print(final_fail_msg)
                        self.detailed_output.append(final_fail_msg)
                        
                        second_issues_header = "\nSecond run issues:"
                        print(second_issues_header)
                        self.detailed_output.append(second_issues_header)
                        
                        print(second_result.reasoning)
                        self.detailed_output.append(second_result.reasoning)
                        
                        results[review_name] = ReviewResponse(
                            result=ReviewResult.FAIL,
                            reasoning=f"First run: PASS\nSecond run: FAIL\n\nSecond run issues:\n{second_result.reasoning}"
                        )
                        
                        end_separator = "\n" + "-" * 40
                        print(end_separator)
                        self.detailed_output.append(end_separator)
                else:
                    # Normal handling for all other cases
                    results[review_name] = result
                    
                    # Calculate and display execution time
                    end_time = time.time()
                    duration_seconds = end_time - start_time
                    duration_minutes = duration_seconds / 60.0
                    
                    time_msg = f"⏱️ Completed in {duration_minutes:.2f} minutes"
                    print(time_msg)
                    self.detailed_output.append(time_msg)
                    
                    sep_msg = "-" * 40
                    print(sep_msg)
                    self.detailed_output.append(sep_msg)
                    
                    # Print immediate result with details for failures
                    if result.result == ReviewResult.PASS:
                        result_msg = f"Result: {result.result.value}"
                        print(result_msg)
                        self.detailed_output.append(result_msg)
                    else:
                        fail_result_msg = f"Result: {result.result.value}"
                        print(fail_result_msg)
                        self.detailed_output.append(fail_result_msg)
                        
                        # Only show cleanup message for points that actually do cleanup
                        if not isinstance(reviewer, (ReasoningThoughtsReviewer, Chain2TestCaseAnalysisReviewer, ThoughtHeadingViolationsReviewer)):
                            cleanup_msg = "🧹 Cleaning up failure details..."
                            print(cleanup_msg)
                            self.detailed_output.append(cleanup_msg)
                        
                        issues_header = "\nIssues Found:"
                        print(issues_header)
                        self.detailed_output.append(issues_header)
                        
                        print(result.reasoning)
                        self.detailed_output.append(result.reasoning)
                        
                        issues_separator = "\n" + "-" * 40
                        print(issues_separator)
                        self.detailed_output.append(issues_separator)
                
            except Exception as e:
                error_result = ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Review failed due to error: {str(e)}"
                )
                results[review_name] = error_result
                
                error_msg = f"Result: ❌ ERROR - {str(e)}"
                print(error_msg)
                self.detailed_output.append(error_msg)
        
        return results
    
    def generate_report(self, results: Dict[str, ReviewResponse]) -> str:
        """Generate comprehensive review report for all 27 review points"""
        report = []
        
        # Add the complete detailed execution log first
        report.append("📋 COMPLETE EXECUTION LOG")
        report.append("=" * 70)
        report.append("")
        
        # Add all the detailed output that was captured during execution
        for line in self.detailed_output:
            report.append(line)
        
        report.append("")
        report.append("")
        report.append("📋 FINAL SUMMARY REPORT - ULTIMATE POINT ANALYSIS")
        report.append("=" * 70)
        report.append("")
        
        # Summary
        passed = sum(1 for r in results.values() if r.result == ReviewResult.PASS and r.reasoning != "SKIPPED - Resumed from later point")
        skipped = sum(1 for r in results.values() if r.reasoning == "SKIPPED - Resumed from later point")
        total = len(results)
        failed = total - passed - skipped
        
        if skipped > 0:
            report.append(f"📊 SUMMARY: {passed}/{total - skipped} reviews passed ({skipped} skipped)")
        else:
            report.append(f"📊 SUMMARY: {passed}/{total} reviews passed")
        
        if failed > 0:
            report.append(f"⚠️  {failed} review(s) failed")
        if skipped > 0:
            report.append(f"⏭️  {skipped} review(s) skipped")
        report.append("")
        
        # Overall status
        if failed == 0 and skipped == 0:
            report.append("🎉 OVERALL STATUS: ALL REVIEWS PASSED")
        elif failed == 0:
            report.append("🎉 OVERALL STATUS: ALL EXECUTED REVIEWS PASSED")
        else:
            report.append("⚠️  OVERALL STATUS: SOME REVIEWS FAILED")
        
        report.append("")
        report.append("=" * 70)
        
        # Results - show all details since we now have the complete log above
        for review_name, result in results.items():
            report.append("")
            report.append(f"📝 {review_name.upper()}")
            report.append("-" * 50)
            
            if result.reasoning == "SKIPPED - Resumed from later point":
                report.append("Status: ⏭️ SKIPPED")
            else:
                report.append(f"Status: {result.result.value}")
                
                if result.result == ReviewResult.FAIL:
                    report.append("")
                    report.append("Issues Found:")
                    report.append(result.reasoning)
                elif result.result == ReviewResult.PASS:
                    report.append("Review passed successfully")
            
            report.append("")
            report.append("-" * 50)
        
        return "\n".join(report)
    
    def save_report(self, report: str, original_filename: str):
        """Save report to file in reports folder with filename_report.txt format"""
        try:
            # Create reports directory if it doesn't exist
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Extract base filename without extension
            base_name = os.path.splitext(os.path.basename(original_filename))[0]
            
            # Create report filename
            report_filename = f"{base_name}_report.txt"
            report_path = os.path.join(reports_dir, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n💾 Report saved to: {report_path}")
        except Exception as e:
            print(f"\n❌ Error saving report: {str(e)}")

def main():
    """Main execution function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Document Review Script - Ultimate Point Analysis',
        epilog='Examples:\n'
               '  python3 document_reviewer.py doc.txt           # Run all Ultimate reviews on doc.txt\n'
               '  python3 document_reviewer.py doc.txt --resume 16   # Resume from review point 16\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('file', help='Path to the text file to review')
    parser.add_argument('--resume', type=int, default=0, metavar='X',
                       help='Resume from review point X (0-N, default: 0)')
    
    args = parser.parse_args()
    
    # Validate resume point
    # Initialize review system first for dynamic validation
    review_system = DocumentReviewSystem()
    max_points = len(review_system.reviewers) - 1
    if args.resume < 0 or args.resume > max_points:
        print(f"❌ Invalid resume point: {args.resume}. Must be between 0 and {max_points}.")
        sys.exit(1)
        sys.exit(1)
    
    try:
        # Review system already initialized for validation above
        
        # Load document
        print(f"📖 Loading document from {args.file}...")
        document = review_system.load_document(args.file)
        print(f"✅ Document loaded ({len(document)} characters)")
        
        # Model information
        print("\n🤖 Model Configuration:")
        print("   Primary: Claude Opus 4.1 (claude-opus-4-1-20250805) with 30k thinking budget")
        print("   Secondary: Claude Sonnet 4 (claude-sonnet-4-20250514) for cleanup operations")
        print("   Max tokens: 32,000 (Opus 4.1) / 2,000 (Sonnet 4 cleanup)")
        print()
        
        # Run reviews with resume option
        results = review_system.run_reviews(document, resume_from=args.resume)
        
        # Generate and display report
        print("\n" + "=" * 70)
        print("📋 GENERATING FINAL REPORT - ULTIMATE POINT ANALYSIS")
        print("=" * 70)
        
        report = review_system.generate_report(results)
        print("\n" + report)
        
        # Save report
        review_system.save_report(report, args.file)
        
        # Exit code based on results (excluding skipped ones)
        failed_reviews = [name for name, result in results.items() 
                         if result.result == ReviewResult.FAIL]
        
        if failed_reviews:
            print(f"\n❌ Review completed with {len(failed_reviews)} failures")
            sys.exit(1)
        else:
            print("\n✅ All reviews passed successfully!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()