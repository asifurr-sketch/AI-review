#!/usr/bin/env python3
"""
Document Review Script using Anthropic Claude Opus 4.1 with Extended Thinking - Ultimate Point Analysis

This script reads a document from a specified text file and performs comprehensive review checks
using Claude Opus 4.1 with extended thinking enabled across multiple specialized review points. 
Each review point is performed by a specialized reviewer class with targeted prompts for maximum precision.

Features:
- Comprehensive review points covering all aspects of document quality
- GitHub Requirements Validation (Non-AI): Validates GitHub URL and overall.md file existence
- Primary: Claude Opus 4.1 with 20k thinking budget for exceptional reasoning
- Secondary: Claude Sonnet 4 for cleanup operations with 64k output tokens
- Code style guide and naming convention compliance for C++ and Python (Points 1-3)
- Response quality and mathematical correctness (Points 4-11) 
- Problem statement and solution validation (Points 12-17)
- Reasoning chain analysis and approach evaluation (Points 18-21)
- Subtopic taxonomy and completeness validation (Points 22-25)
- Chain 2 test case analysis validation (Point 26)
- Thought heading violations check (Point 27)
- Comprehensive reasoning thoughts review (Point 28)
- Extended thinking provides deep analysis with step-by-step reasoning

GitHub Requirements:
- Document must contain a GitHub URL in metadata: **GitHub URL:** https://github.com/owner/repo
- Repository cloning uses SSH by default with HTTPS fallback for better security
- Repository must be accessible and cloneable (SSH key setup recommended)
- Repository must contain exactly one overall.md file (case-insensitive)
- SSH Setup (Recommended):
  1. Generate SSH key: ssh-keygen -t ed25519 -C 'your_email@example.com'
  2. Add to SSH agent: ssh-add ~/.ssh/id_ed25519
  3. Add public key to GitHub: Copy content of ~/.ssh/id_ed25519.pub to GitHub settings
  4. Test SSH access: ssh -T git@github.com
- GitHub API key should be configured in .env file as: git_api = your_token_here (optional for public repos)

Author: AI Assistant
Date: October 9, 2025
"""

import os
import sys
import argparse
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
import time
import re
import subprocess
import tempfile
import shutil
from urllib.parse import urlparse
from anthropic import Anthropic
import concurrent.futures
import threading

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

FORMATTING REQUIREMENTS:
- DO NOT use **bold** formatting or any markdown-style formatting
- DO NOT use ChatGPT-style brackets like **[SECTION]** or **bold text**
- Use plain text with simple bullet points (•) or dashes (-)
- Keep formatting minimal and clean
- Avoid any special formatting characters

IMPORTANT: Focus on actionable failure information that helps the user understand what needs to be fixed. Avoid providing multiple code alternatives or improved examples.

Original Response:
"""
        
        try:
            # Use Sonnet 4 for cleanup with streaming for comprehensive failure analysis
            cleaned_response = ""
            
            with self.client.messages.stream(
                model=self.secondary_model,
                max_tokens=64000,  # Maximum output tokens for Claude Sonnet 4
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": f"{cleanup_prompt}\n\n{failure_response}"
                    }
                ]
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text') and event.delta.text:
                            cleaned_response += event.delta.text
            
            if not cleaned_response:
                cleaned_response = "No text content in cleanup response"
            
            cleaned_response = cleaned_response.strip()
            
            # Remove **bold** and *italic* formatting while preserving all structure
            import re
            # Remove **bold** formatting
            cleaned_response = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_response)
            # Remove *italic* formatting  
            cleaned_response = re.sub(r'\*(.*?)\*', r'\1', cleaned_response)
            
            # Add a small delay to respect API rate limits for the cleanup call
            import time
            time.sleep(0.5)
            
            return cleaned_response.strip()
        except Exception as e:
            # If cleanup fails, return original response
            return f"[Cleanup failed: {str(e)}]\n\n{failure_response}"

    def _make_api_call(self, prompt: str, document: str) -> str:
        """Make API call to Claude Opus 4.1 with thinking enabled and streaming"""
        thinking_budget = 20000  # Thinking budget for comprehensive analysis
        max_output = 32000  # Maximum output tokens for Claude Opus 4.1
        
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
    
    # Style Guide Compliance
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

    # Naming Conventions
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

    # Documentation
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
    
    # Response Relevance to Problem
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

    # Mathematical Equations Correctness
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

    # Problem Constraints Consistency
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

    # Missing Approaches in Steps
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

    # Code Elements Existence
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

    # Example Walkthrough with Optimal Algorithm
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

    # Time and Space Complexity Correctness
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

    # Conclusion Quality
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

    # Problem Statement Consistency
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

    # Solution Passability According to Limits
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

    # Metadata Correctness
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

CRITICAL VALIDATION FOR "Number of Approaches":
- Must contain both the count and the time complexity progression
- Acceptable formats:
  * "4, (O(n²+qn²) → O(qn²) → O(qn) → O(q))" 
  * "3, ($O(2^n)$ → $O(n \\log n)$ → $O((n + s) \\log n)$)"
  * "4, (O(n^4) → O(n^3) → O(n^2) → O(n log n))"
- The number must match the count of approaches in the complexity progression
- Can use either "->" or "→" arrows consistently
- Can use LaTeX formatting with $ symbols or plain text
- Must show progression from inefficient to efficient approaches
- Variables must match those used in the problem statement

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
4. Number of Approaches contains both count and valid time complexity progression
5. Number of Chains matches actual CHAIN_XX sections count
6. Subtopic is a properly formatted JSON array
7. Values are appropriate for the content

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Unique Solution Validation
    @staticmethod
    def get_unique_solution_prompt():
        """Check if problem has unique valid solution for automated testing"""
        return """
You are an expert problem analysis specialist. 

TASK: Determine if this problem can have multiple valid solutions for the same input, which would make it unsuitable for direct file matching validation.

CRITICAL ANALYSIS REQUIREMENTS:
1. **Single Valid Output**: For ANY given valid input, there must be exactly ONE correct output
2. **Deterministic Result**: The problem should not allow different valid answers for the same test case
3. **No Multiple Correct Formats**: Output format should be strictly defined with no acceptable variations

EXAMPLES OF PROBLEMS THAT FAIL THIS CHECK:
- "Print any valid permutation" (multiple correct answers exist)
- "Output any path from A to B" (multiple valid paths possible)
- "Print elements in any order" (different orderings are valid)
- "Find any solution that satisfies the constraints" (multiple solutions exist)
- Problems with floating-point outputs where precision tolerance matters
- Problems asking for "one possible arrangement" or "any valid configuration"

EXAMPLES OF PROBLEMS THAT PASS THIS CHECK:
- "Find the minimum number of operations" (single numerical answer)
- "Calculate the maximum profit" (single numerical answer)
- "Determine if it's possible (YES/NO)" (binary answer)
- "Print the lexicographically smallest sequence" (deterministic ordering)
- "Output the unique solution" (explicitly states uniqueness)
- "Find the shortest path length" (single numerical value)

WHAT TO EXAMINE:
1. **Problem Statement**: Look for words like "any", "one possible", "find a solution", "print any valid"
2. **Output Requirements**: Check if output format allows variations
3. **Constraints**: Determine if constraints guarantee uniqueness
4. **Examples**: Verify if given examples have only one possible correct output
5. **Problem Type**: Identify if it's optimization (usually unique) vs. construction (often multiple solutions)

VALIDATION CRITERIA:
- If the problem asks for "any valid solution" → FAIL
- If multiple correct outputs exist for the same input → FAIL  
- If output ordering is flexible ("in any order") → FAIL
- If the problem guarantees unique solution → PASS
- If it's asking for optimal value (min/max) → Usually PASS
- If it's asking for count/existence (YES/NO) → Usually PASS

RESPONSE FORMAT:
Provide detailed analysis of why the problem does/doesn't have unique solutions, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Time Complexity Authenticity Check
    @staticmethod
    def get_time_complexity_authenticity_prompt():
        """Check if time complexity in metadata covers all approaches discussed"""
        return """
You are an expert response evaluator. Check if the time complexity mentioned in the metadata section meets ALL of the following requirements:

**REQUIREMENTS:**
1. **All Approaches Covered**: The metadata must list time complexity for EVERY approach discussed in the document (brute force, optimized, final solution, etc.)
2. **Sequential Format**: Must follow the format showing progression from inefficient to efficient approaches using either "->" or "→" arrows
3. **Count Consistency**: The number of complexity expressions must match the count specified in "Number of Approaches" field
4. **No Extra Text**: Must NOT contain any descriptive text, approach explanations, or space complexity mentions
5. **Variable-Based**: Time complexity must be expressed ONLY using variables mentioned in the problem statement (e.g., if problem mentions N, M, K, Q, then use those exact variables)
6. **Correctness**: Each stated time complexity must be mathematically correct for its corresponding approach
7. **Complex Expressions**: Support complex mathematical expressions with multiple terms (e.g., "O(n²+qn²)", "O(n*m + k*log(n))")

**ACCEPTABLE FORMATS:**
- Single approach: "O(N)"
- Two approaches: "O(N^2) -> O(N log N)" or "O(N²) → O(N log N)"
- Three approaches: "O(N^3) -> O(N^2) -> O(N log N)" or "O(N³) → O(N²) → O(N log N)"
- Multiple approaches: "O(N^2) -> O(N log N) -> O(N) -> O(log N)"
- Complex expressions: "O(n²+qn²) → O(qn²) → O(qn) → O(q)"
- Mixed variables: "O(n*m + k) → O(n*m) → O(n+m)"
- Logarithmic terms: "O(n²log(n)) → O(n log n) → O(n)"

**ACCEPTABLE COMPLEXITY NOTATIONS:**
- Superscripts: N², n², m³, etc.
- Caret notation: N^2, n^2, m^3, etc.
- Multiplication: n*m, q*n, k*log(n), etc.
- Addition: n²+qn², n*m+k, etc.
- Logarithms: log(n), log(m), logN, etc.
- Mixed: n²+m*log(k), qn²+n*m, etc.

**UNACCEPTABLE FORMATS:**
- Missing approaches: "O(N)" when document discusses brute force O(N^2) and optimized O(N)
- Extra text: "O(N^2) brute force -> O(N) optimized approach"
- Space complexity: "Time: O(N^2) -> O(N), Space: O(1)"
- Wrong variables: "O(n)" when problem uses N, or "O(size)" when problem uses variables n, q
- Individual steps: "O(N) for loop + O(log N) for search = O(N log N)"
- Inconsistent arrow types: mixing "->" and "→" in same sequence
- Wrong case: "O(n)" when problem statement uses uppercase "N"

**VALIDATION STEPS:**
1. Count all approaches discussed in the document (brute force, intermediate, final, etc.)
2. Check the "Number of Approaches" field to get the expected count and complexity progression
3. Verify metadata lists time complexity for each approach in progression order
4. Confirm the count of complexity expressions matches the stated number of approaches
5. Confirm all variables used exactly match those in the problem statement (including case)
6. Check if each complexity is mathematically correct for its corresponding approach
7. Ensure no extra descriptive text or space complexity mentions
8. Validate complex mathematical expressions are properly formatted
9. Ensure consistent arrow notation throughout the sequence

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Test Case Validation
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

    # Sample Test Case Dry Run Validation
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

    # Note Section Explanation
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

    # Inefficient Approaches Limitations
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

    # Final Approach Discussion
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

    # No Code in Reasoning Chains
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

    # Subtopic Taxonomy Validation
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

    # Typo Check
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

    # Subtopic Relevance
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

    # Missing Relevant Subtopics
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

    # Predictive Headings in Thoughts
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

    # Chain Test Case Analysis Validation
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

    # Thought Heading Violations
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

    # Mathematical Variables and Expressions Formatting
    @staticmethod
    def get_math_formatting_prompt():
        """Check if all mathematical variables and expressions are properly enclosed in LaTeX format"""
        return """
You are an expert document reviewer specializing in mathematical notation and LaTeX formatting.

TASK: Check if ALL variables and mathematical expressions throughout the document are properly enclosed in LaTeX format ($...$ for inline or $$...$$ for display).

WHAT TO CHECK:
1. **Single variables**: Letters used as mathematical variables (e.g., n, i, j, k, x, y, N, M, etc.)
2. **Mathematical expressions**: Any mathematical operations, equations, or formulas
3. **Mathematical notation**: Subscripts, superscripts, fractions, summations, etc.
4. **Algorithm complexity**: Big O notation (e.g., O(n), O(log n), O(n²))
5. **Mathematical relationships**: Comparisons, inequalities, ranges (e.g., i < n, x ≥ 0)

WHAT NOT TO FLAG:
- Variables in code blocks (inside ``` code blocks)
- Programming language keywords and syntax
- Regular English words that happen to be single letters
- Variables that are clearly part of programming context (not mathematical)
- File extensions, version numbers, or technical abbreviations

FORMATTING REQUIREMENTS:
- Inline math should use single dollar signs: $variable$ or $expression$
- Display math should use double dollar signs: $$expression$$
- All mathematical content must be enclosed, no exceptions

SECTION-BY-SECTION ANALYSIS:
You must examine ALL sections of the document including:
- Metadata section
- Problem statement/Prompt section
- All CHAIN_XX sections
- All THOUGHT_XX_YY sections
- Response/Assistant sections
- Any other text content

VIOLATION REPORTING:
For each violation found, provide:
1. The exact section name where it occurs (e.g., "Metadata", "CHAIN_01", "THOUGHT_02_03", etc.)
2. The exact unformatted text that should be in LaTeX
3. The suggested correction with proper LaTeX formatting

RESPONSE FORMAT:
List ALL violations in this format:

**VIOLATIONS FOUND:**

**Section: [Section Name]**
- Violation: "[exact unformatted text]"
- Should be: "$[corrected LaTeX format]$"

**Section: [Section Name]**
- Violation: "[exact unformatted text]" 
- Should be: "$[corrected LaTeX format]$"

If no violations are found, state: "No mathematical formatting violations found."

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    # Reasoning Thoughts Review Process
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

    @staticmethod
    def get_time_limit_validation_prompt():
        """Check if time limit is properly specified in document"""
        return """
You are a document validator. Check if the document contains a properly specified time limit for the problem.

REQUIREMENTS:
1. The document must contain a time limit specification
2. The time limit should be in a clear, recognizable format (e.g., "Time Limit: 1 second", "Time: 2 seconds", "1s", etc.)
3. The time limit must be a positive value

ANALYSIS:
- Look through the entire document for any mention of time limits
- Check common locations: problem statement, constraints section, metadata
- Verify the format is clear and the value is reasonable (typically 0.1s to 10s for competitive programming)

PASS if: Time limit is clearly specified with a positive value
FAIL if: No time limit found or time limit is unclear/invalid

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_memory_limit_validation_prompt():
        """Check if memory limit is at least 32 MB"""
        return """
You are a document validator. Check if the document contains a memory limit specification that is at least 32 MB.

REQUIREMENTS:
1. The document must contain a memory limit specification
2. The memory limit must be at least 32 MB (32 megabytes)
3. The format should be clear and recognizable (e.g., "Memory Limit: 64 MB", "Memory: 128 MB", etc.)

ANALYSIS:
- Look through the entire document for any mention of memory limits
- Check common locations: problem statement, constraints section, metadata
- Convert the value to MB if needed (e.g., 32768 KB = 32 MB, 0.032 GB = 32 MB)
- Verify the value is at least 32 MB

PASS if: Memory limit is specified and is at least 32 MB
FAIL if: No memory limit found, memory limit is less than 32 MB, or format is unclear

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

# Ultimate Individual Reviewer Classes - One for each review point

class UniqueSolutionReviewer(BaseReviewer):
    """Validates if problem has unique solution for automated testing"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_unique_solution_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class TimeComplexityAuthenticityReviewer(BaseReviewer):
    """Reviews time complexity authenticity in metadata for all approaches"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_time_complexity_authenticity_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class StyleGuideReviewer(BaseReviewer):
    """Reviews code style guide compliance"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_style_guide_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class NamingConventionsReviewer(BaseReviewer):
    """Reviews naming conventions compliance"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_naming_conventions_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class DocumentationReviewer(BaseReviewer):
    """Reviews appropriate documentation style"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_documentation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ResponseRelevanceReviewer(BaseReviewer):
    """Reviews if response section is relevant to problem description"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_response_relevance_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class MathEquationsReviewer(BaseReviewer):
    """Reviews mathematical equations correctness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_math_equations_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ConstraintsConsistencyReviewer(BaseReviewer):
    """Reviews if defined problem constraints match problem description"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_constraints_consistency_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class MissingApproachesReviewer(BaseReviewer):
    """Reviews if any approaches or data structures are not explained in approach steps (this check is only for the response section, where optimal algorithm is explained)"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_missing_approaches_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class CodeElementsExistenceReviewer(BaseReviewer):
    """Reviews if mentioned variables, functions, and classes exist in code"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_code_elements_existence_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ExampleWalkthroughReviewer(BaseReviewer):
    """Reviews if response has example walkthrough with optimal algorithm"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_example_walkthrough_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ComplexityCorrectnessReviewer(BaseReviewer):
    """Reviews time and space complexity correctness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_complexity_correctness_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ConclusionQualityReviewer(BaseReviewer):
    """Reviews conclusion quality"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_conclusion_quality_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class ProblemConsistencyReviewer(BaseReviewer):
    """Reviews problem statement consistency"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_problem_consistency_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class SolutionPassabilityReviewer(BaseReviewer):
    """Reviews if solution is passable according to limits"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_solution_passability_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class MetadataCorrectnessReviewer(BaseReviewer):
    """Reviews metadata correctness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_metadata_correctness_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class TestCaseValidationReviewer(BaseReviewer):
    """Reviews test cases against code and problem statement"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_test_case_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class SampleDryRunValidationReviewer(BaseReviewer):
    """Reviews if dry runs or explanations of sample test cases match the given examples exactly"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_sample_dry_run_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class NoteSectionReviewer(BaseReviewer):
    """Reviews note section explanation approach - only applies to problem statement/prompt section"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_note_section_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class InefficientLimitationsReviewer(BaseReviewer):
    """Reviews if inefficient approaches mention limitations"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_inefficient_limitations_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class FinalApproachDiscussionReviewer(BaseReviewer):
    """Reviews final approach discussion completeness"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_final_approach_discussion_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class NoCodeInReasoningReviewer(BaseReviewer):
    """Reviews if reasoning chains contain code"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_no_code_in_reasoning_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class SubtopicTaxonomyReviewer(BaseReviewer):
    """Reviews if subtopics are from taxonomy list"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_subtopic_taxonomy_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class TimeLimitValidationReviewer(BaseReviewer):
    """Validates that time limit is specified in the document"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_time_limit_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class MemoryLimitValidationReviewer(BaseReviewer):
    """Validates that memory limit is at least 32 MB"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_memory_limit_validation_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class TypoCheckReviewer(BaseReviewer):
    """Reviews for typos and spelling issues"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_typo_check_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class SubtopicRelevanceReviewer(BaseReviewer):
    """Reviews if selected subtopics are relevant"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_subtopic_relevance_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class MissingSubtopicsReviewer(BaseReviewer):
    """Reviews for missing relevant subtopics"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_missing_subtopics_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class PredictiveHeadingsReviewer(BaseReviewer):
    """Reviews for predictive headings in thoughts"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_predictive_headings_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)

class Chain2TestCaseAnalysisReviewer(BaseReviewer):
    """Reviews if Chain 2 performs actual test case analysis"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_chain2_testcase_analysis_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)



class ThoughtHeadingViolationsReviewer(BaseReviewer):
    """Reviews for prohibited headings in thoughts"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_thought_heading_violations_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)



class MathFormattingReviewer(BaseReviewer):
    """Reviews mathematical variables and expressions formatting"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_math_formatting_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)
    

class ReasoningThoughtsReviewer(BaseReviewer):
    """Comprehensive review of reasoning thought chains"""
    
    def review(self, document: str) -> ReviewResponse:
        prompt = ReviewPrompts.get_reasoning_thoughts_review_prompt()
        response = self._make_api_call(prompt, document)
        return self._parse_response(response)


class GitHubReviewValidator:
    """Non-AI review: Validates GitHub post links and overall.md file existence"""
    
    def __init__(self, quiet_mode=False):
        # Load GitHub API key from .env file
        self.github_api_key = None
        self.quiet_mode = quiet_mode
        self._load_env_variables()
    
    def _load_env_variables(self):
        """Load environment variables from .env file"""
        env_path = '.env'
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key == 'git_api':
                            self.github_api_key = value
                            break
    
    def _extract_github_url(self, document: str) -> Optional[str]:
        """Extract GitHub URL from document metadata"""
        # Try the exact format first
        github_url_pattern = r'\*\*GitHub URL:\*\*\s+(https://github\.com/[^\s\n]+)'
        match = re.search(github_url_pattern, document)
        if match:
            return match.group(1)
        
        # Try alternative formats with different spacing or formatting
        alternative_patterns = [
            r'\*\*GitHub URL\*\*\s*:\s+(https://github\.com/[^\s\n]+)',
            r'\*\*GitHub URL:\*\*[^\n]*?(https://github\.com/[^\s\n]+)',
            r'GitHub URL[^:]*:\s*(https://github\.com/[^\s\n]+)',
        ]
        
        for pattern in alternative_patterns:
            match = re.search(pattern, document, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_github_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse GitHub URL to extract owner and repo name"""
        try:
            parsed = urlparse(url)
            if parsed.netloc == 'github.com':
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    owner = path_parts[0]
                    repo = path_parts[1]
                    return owner, repo
        except Exception:
            pass
        return None, None
    
    def _convert_to_ssh_url(self, https_url: str) -> str:
        """Convert HTTPS GitHub URL to SSH format"""
        # https://github.com/owner/repo -> git@github.com:owner/repo.git
        if https_url.startswith('https://github.com/'):
            # Remove https://github.com/ prefix
            repo_path = https_url.replace('https://github.com/', '')
            # Remove .git suffix if present
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
            # Convert to SSH format
            ssh_url = f"git@github.com:{repo_path}.git"
            return ssh_url
        else:
            # If it's already in SSH format or different format, return as-is
            return https_url
    
    def _clone_repository(self, url: str, temp_dir: str) -> bool:
        """Clone GitHub repository to temporary directory using SSH with HTTPS fallback"""
        try:
            # Convert HTTPS URL to SSH format
            ssh_url = self._convert_to_ssh_url(url)
            
            # Ensure temp_dir doesn't exist (git clone creates it)
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
            
            # First try SSH
            if not self.quiet_mode:
                print(f"🔑 Attempting to clone using SSH: {ssh_url}")
            result = subprocess.run([
                'git', 'clone', '--depth=1', ssh_url, temp_dir
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                if not self.quiet_mode:
                    print(f"✅ Successfully cloned via SSH")
                return True
            else:
                if not self.quiet_mode:
                    print(f"⚠️  SSH clone failed, trying HTTPS fallback...")
                    print(f"   SSH Error: {result.stderr}")
                
                # Clean up failed attempt
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
                
                # Fallback to HTTPS if SSH fails
                if not self.quiet_mode:
                    print(f"🌐 Attempting to clone using HTTPS: {url}")
                https_result = subprocess.run([
                    'git', 'clone', '--depth=1', url, temp_dir
                ], capture_output=True, text=True, timeout=120)
                
                if https_result.returncode == 0:
                    if not self.quiet_mode:
                        print(f"✅ Successfully cloned via HTTPS fallback")
                    return True
                else:
                    if not self.quiet_mode:
                        print(f"❌ Both SSH and HTTPS clone failed")
                        print(f"   SSH Error: {result.stderr}")
                        print(f"   HTTPS Error: {https_result.stderr}")
                        print(f"   ")
                        print(f"   💡 SSH Setup Help:")
                        print(f"   1. Generate SSH key: ssh-keygen -t ed25519 -C 'your_email@example.com'")
                        print(f"   2. Add to SSH agent: ssh-add ~/.ssh/id_ed25519")
                        print(f"   3. Add public key to GitHub: cat ~/.ssh/id_ed25519.pub")
                        print(f"   4. Test SSH access: ssh -T git@github.com")
                    return False
                
        except subprocess.TimeoutExpired:
            if not self.quiet_mode:
                print("❌ Git clone timed out after 120 seconds")
            return False
        except Exception as e:
            if not self.quiet_mode:
                print(f"Git clone exception: {e}")
            return False
    
    def _find_overall_md_files(self, repo_dir: str) -> List[str]:
        """Find all overall.md files in the repository (case-insensitive)"""
        overall_files = []
        
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                if file.lower() == 'overall.md':
                    overall_files.append(os.path.join(root, file))
        
        return overall_files
    
    def _check_hunyuan_cpp_files(self, repo_dir: str) -> Tuple[bool, str]:
        """Check if runs/hunyuan-t1-dev-20250822/*.cpp files exist"""
        hunyuan_dir = os.path.join(repo_dir, 'runs', 'hunyuan-t1-dev-20250822')
        
        if not os.path.exists(hunyuan_dir):
            return False, f"Directory 'runs/hunyuan-t1-dev-20250822' does not exist"
        
        cpp_files = []
        for file in os.listdir(hunyuan_dir):
            if file.endswith('.cpp'):
                cpp_files.append(file)
        
        if not cpp_files:
            return False, f"No .cpp files found in 'runs/hunyuan-t1-dev-20250822' directory"
        
        return True, f"Found {len(cpp_files)} .cpp files: {', '.join(cpp_files)}"
    
    def _validate_overall_md_format(self, overall_md_path: str) -> Tuple[bool, str]:
        """Validate the format of overall.md file"""
        try:
            with open(overall_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "# Overall Test Report for",
                "**Error Code Legend:**",
                "## Detailed Model Performance",
                "### Model: `hunyuan-t1-dev-20250822`",
                "### Model: `standard.cpp`",
                "## Overall Model Comparison"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                return False, f"Missing required sections: {', '.join(missing_sections)}"
            
            # Check for hunyuan model failure requirement
            if "hunyuan-t1-dev-20250822" in content:
                # Look for failure indicators in hunyuan section
                hunyuan_section_start = content.find("### Model: `hunyuan-t1-dev-20250822`")
                if hunyuan_section_start != -1:
                    # Find the next model section or end of content
                    next_model = content.find("### Model:", hunyuan_section_start + 1)
                    if next_model == -1:
                        hunyuan_section = content[hunyuan_section_start:]
                    else:
                        hunyuan_section = content[hunyuan_section_start:next_model]
                    
                    if "❌ FAIL" not in hunyuan_section and "✅ PASS" in hunyuan_section:
                        return False, "hunyuan-t1-dev-20250822 model should show FAIL status (❌ FAIL), not PASS"
            
            # Check for standard.cpp pass requirement
            if "standard.cpp" in content:
                standard_section_start = content.find("### Model: `standard.cpp`")
                if standard_section_start != -1:
                    # Find the next section or end of content - look for ### or ## or \n---\n (real section separators, not table borders)
                    next_section_positions = []
                    
                    # Look for next model section
                    next_model = content.find("### Model:", standard_section_start + 1)
                    if next_model != -1:
                        next_section_positions.append(next_model)
                    
                    # Look for overall comparison section
                    next_overall = content.find("## Overall", standard_section_start + 1)
                    if next_overall != -1:
                        next_section_positions.append(next_overall)
                        
                    # Look for separator - but only standalone separators (not table borders)
                    # Look for \n---\n pattern to avoid table borders like |---|---|
                    search_start = standard_section_start + 1
                    while True:
                        next_separator = content.find("\n---\n", search_start)
                        if next_separator == -1:
                            break
                        # Make sure this isn't part of a table
                        line_start = content.rfind('\n', 0, next_separator)
                        line_before = content[line_start+1:next_separator].strip()
                        if not line_before.startswith('|') and not line_before.endswith('|'):
                            next_section_positions.append(next_separator)
                            break
                        search_start = next_separator + 1
                    
                    # If no markers found, use end of content
                    if not next_section_positions:
                        next_section = len(content)
                    else:
                        next_section = min(next_section_positions)
                    
                    standard_section = content[standard_section_start:next_section]
                    
                    if "✅ PASS" not in standard_section:
                        return False, "standard.cpp model should show PASS status (✅ PASS)"
            
            # Check for solution_bf.cpp constraints if present
            if "solution_bf.cpp" in content:
                bf_section_start = content.find("### Model: `solution_bf.cpp`")
                if bf_section_start != -1:
                    next_model = content.find("### Model:", bf_section_start + 1)
                    if next_model == -1:
                        bf_section = content[bf_section_start:]
                    else:
                        bf_section = content[bf_section_start:next_model]
                    
                    # Check for WA or CE errors (should not have these)
                    if "|" in bf_section:  # Look for table rows
                        table_lines = [line.strip() for line in bf_section.split('\n') if '|' in line and 'Run File' not in line and 'Model' not in line]
                        for line in table_lines:
                            if 'solution_bf.cpp' in line:
                                parts = [p.strip() for p in line.split('|')]
                                if len(parts) >= 8:  # Ensure we have enough columns
                                    errors_column = parts[7]  # Last column with errors
                                    
                                    # Parse errors format: WA/TLE/RTE/CE
                                    if '/' in errors_column:
                                        error_counts = errors_column.split('/')
                                        if len(error_counts) >= 4:
                                            wa_count = error_counts[0]
                                            ce_count = error_counts[3]
                                            if wa_count != '0':
                                                return False, "solution_bf.cpp should not have Wrong Answer (WA) errors"
                                            if ce_count != '0':
                                                return False, "solution_bf.cpp should not have Compilation Error (CE) errors"
            
            return True, "overall.md format validation passed"
            
        except Exception as e:
            return False, f"Error reading overall.md file: {str(e)}"
    
    def _normalize_content(self, content: str) -> str:
        """Normalize content by removing extra whitespace but preserving structure"""
        lines = content.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Strip trailing whitespace but preserve leading whitespace structure
            stripped = line.rstrip()
            normalized_lines.append(stripped)
        
        # Join and normalize multiple consecutive empty lines to single empty lines
        result = '\n'.join(normalized_lines)
        # Remove trailing newlines/whitespace
        result = result.rstrip()
        
        return result
    
    def _extract_content_until_chain01(self, document: str) -> str:
        """Extract content from start until and including **[CHAIN_01]** line"""
        lines = document.split('\n')
        result_lines = []
        
        for line in lines:
            result_lines.append(line)
            if line.strip() == "**[CHAIN_01]**":
                break
        
        return '\n'.join(result_lines)
    
    def _extract_content_from_chain01(self, document: str) -> str:
        """Extract content from **[CHAIN_01]** line to the end"""
        lines = document.split('\n')
        result_lines = []
        found_chain01 = False
        
        for line in lines:
            if line.strip() == "**[CHAIN_01]**":
                found_chain01 = True
            if found_chain01:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _extract_prompt_section(self, document: str) -> str:
        """Extract content between **[Prompt]** and **[Assistant]** (exclusive)"""
        lines = document.split('\n')
        result_lines = []
        in_prompt_section = False
        
        for line in lines:
            if line.strip() == "**[Prompt]**":
                in_prompt_section = True
                continue  # Skip the **[Prompt]** line itself
            elif line.strip() == "**[Assistant]**":
                break  # Stop before **[Assistant]** line
            elif in_prompt_section:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _compare_content_with_diff_rules(self, content1: str, content2: str, allowed_diffs: List[str]) -> Tuple[bool, str]:
        """Compare two contents and check if differences are only in allowed list"""
        # Normalize both contents
        norm1 = self._normalize_content(content1)
        norm2 = self._normalize_content(content2)
        
        # If they're identical after normalization, pass
        if norm1 == norm2:
            return True, "Contents are identical"
        
        # Split into lines for detailed comparison
        lines1 = norm1.split('\n')
        lines2 = norm2.split('\n')
        
        # Simple line-by-line diff approach
        import difflib
        
        differ = difflib.unified_diff(lines1, lines2, lineterm='', n=0)
        diff_lines = list(differ)
        
        # Skip the header lines (first 3 lines: ---, +++, @@)
        actual_diffs = diff_lines[3:] if len(diff_lines) > 3 else []
        
        violations = []
        for diff_line in actual_diffs:
            if diff_line.startswith('+') or diff_line.startswith('-'):
                # Extract the actual content (remove +/- prefix)
                content = diff_line[1:]
                
                # Check if this difference is allowed
                is_allowed = False
                for allowed in allowed_diffs:
                    if allowed == "newlines" and content.strip() == "":
                        is_allowed = True
                        break
                    elif allowed == "spaces" and content != "" and content.strip() == "":
                        is_allowed = True
                        break
                    elif allowed == "---" and content.strip() == "---":
                        is_allowed = True
                        break
                    elif allowed in content:
                        is_allowed = True
                        break
                
                if not is_allowed:
                    violations.append(f"Disallowed diff: '{content}'")
        
        if violations:
            # Create a detailed diff output showing the full context
            full_diff = '\n'.join(diff_lines)
            violation_summary = '; '.join(violations[:5])  # Limit to first 5 violations
            return False, f"Content diff violations found: {violation_summary}\n\nFull diff output:\n{full_diff}"
        
        return True, "All differences are in allowed categories"
    
    def _validate_solution_md_consistency(self, repo_dir: str, document: str) -> Tuple[bool, str]:
        """Validate that solution.md matches document content from CHAIN_01 onward"""
        solution_md_path = os.path.join(repo_dir, 'solution.md')
        
        if not os.path.exists(solution_md_path):
            return False, "solution.md file not found in repository"
        
        try:
            # Read solution.md
            with open(solution_md_path, 'r', encoding='utf-8') as f:
                solution_content = f.read()
            
            # Extract document content from CHAIN_01 onward
            doc_content = self._extract_content_from_chain01(document)
            
            # Compare with allowed differences: newlines, spaces, "---", "**[COT]**"
            is_valid, message = self._compare_content_with_diff_rules(
                doc_content, solution_content, ["newlines", "spaces", "---", "**[COT]**"]
            )
            
            if not is_valid:
                return False, f"solution.md content mismatch: {message}"
            
            return True, "solution.md content validation passed"
            
        except Exception as e:
            return False, f"Error validating solution.md: {str(e)}"
    
    def _validate_problem_statement_md_consistency(self, repo_dir: str, document: str) -> Tuple[bool, str]:
        """Validate that problem_statement.md matches document prompt section"""
        problem_md_path = os.path.join(repo_dir, 'problem_statement.md')
        
        if not os.path.exists(problem_md_path):
            return False, "problem_statement.md file not found in repository"
        
        try:
            # Read problem_statement.md
            with open(problem_md_path, 'r', encoding='utf-8') as f:
                problem_content = f.read()
            
            # Extract prompt section from document
            prompt_content = self._extract_prompt_section(document)
            
            # Compare with allowed differences: newlines, spaces, "---"
            is_valid, message = self._compare_content_with_diff_rules(
                prompt_content, problem_content, ["newlines", "spaces", "---"]
            )
            
            if not is_valid:
                return False, f"problem_statement.md content mismatch: {message}"
            
            return True, "problem_statement.md content validation passed"
            
        except Exception as e:
            return False, f"Error validating problem_statement.md: {str(e)}"
    
    def validate_github_requirements(self, document: str) -> ReviewResponse:
        """Main validation method for GitHub requirements"""
        # Step 1: Check for GitHub URL in document
        github_url = self._extract_github_url(document)
        if not github_url:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning="No GitHub URL found in document metadata. Expected format: **GitHub URL:** https://github.com/owner/repo"
            )
        
        # Step 2: Parse GitHub URL
        owner, repo = self._parse_github_url(github_url)
        if not owner or not repo:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Invalid GitHub URL format: {github_url}. Expected format: https://github.com/owner/repo"
            )
        
        # Step 3: Clone repository
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="github_review_")
            
            if not self._clone_repository(github_url, temp_dir):
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Failed to clone repository: {github_url}. Repository may not exist or be inaccessible."
                )
            
            # Step 4: Find overall.md files
            overall_files = self._find_overall_md_files(temp_dir)
            
            if len(overall_files) == 0:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"No overall.md file found in repository {github_url}"
                )
            elif len(overall_files) > 1:
                # Select the overall.md file with the largest alphabetical path
                overall_files.sort()
                selected_file = overall_files[-1]
                relative_paths = [os.path.relpath(f, temp_dir) for f in overall_files]
                selected_relative = os.path.relpath(selected_file, temp_dir)
                # Update overall_files to contain only the selected file
                overall_files = [selected_file]
            
            # Step 5: Check for hunyuan cpp files
            hunyuan_exists, hunyuan_msg = self._check_hunyuan_cpp_files(temp_dir)
            if not hunyuan_exists:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Repository validation failed: {hunyuan_msg}"
                )
            
            # Step 6: Validate overall.md format
            overall_md_path = overall_files[0]
            format_valid, format_msg = self._validate_overall_md_format(overall_md_path)
            if not format_valid:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"overall.md format validation failed: {format_msg}"
                )
            
            # Step 7: Validate solution.md content consistency
            solution_valid, solution_msg = self._validate_solution_md_consistency(temp_dir, document)
            if not solution_valid:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"solution.md validation failed: {solution_msg}"
                )
            
            # Step 8: Validate problem_statement.md content consistency
            problem_valid, problem_msg = self._validate_problem_statement_md_consistency(temp_dir, document)
            if not problem_valid:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"problem_statement.md validation failed: {problem_msg}"
                )
            
            # All validations passed
            relative_path = os.path.relpath(overall_md_path, temp_dir)
            return ReviewResponse(
                result=ReviewResult.PASS,
                reasoning=f"✅ PASS - All GitHub requirements validated:\n" +
                         f"• Repository: {github_url}\n" +
                         f"• overall.md file: {relative_path}\n" +
                         f"• Hunyuan cpp files: {hunyuan_msg}\n" +
                         f"• Format validation: {format_msg}\n" +
                         f"• solution.md consistency: {solution_msg}\n" +
                         f"• problem_statement.md consistency: {problem_msg}"
            )
        
        except Exception as e:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Error during GitHub validation: {str(e)}"
            )
        
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass  # Ignore cleanup errors

    def validate_github_requirements_detailed(self, document: str) -> list:
        """Detailed validation method that returns separate results for each GitHub task"""
        results = []
        temp_dir = None
        
        try:
            # Task 1: GitHub URL Extraction
            github_url = self._extract_github_url(document)
            if not github_url:
                results.append(("GitHub URL Extraction", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning="No GitHub URL found in document metadata. Expected format: **GitHub URL:** https://github.com/owner/repo"
                )))
                return results
            else:
                results.append(("GitHub URL Extraction", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - GitHub URL found: {github_url}"
                )))
            
            # Task 2: GitHub URL Parsing
            owner, repo = self._parse_github_url(github_url)
            if not owner or not repo:
                results.append(("GitHub URL Parsing", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Invalid GitHub URL format: {github_url}. Expected format: https://github.com/owner/repo"
                )))
                # Critical failure, cannot continue without valid URL
                return results
            else:
                results.append(("GitHub URL Parsing", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - URL parsed: owner={owner}, repo={repo}"
                )))
            
            # Task 3: Repository Cloning
            temp_dir = tempfile.mkdtemp(prefix="github_review_")
            clone_success = self._clone_repository(github_url, temp_dir)
            if not clone_success:
                results.append(("Repository Cloning", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Failed to clone repository: {github_url}. Repository may not exist or be inaccessible."
                )))
                # Critical failure, cannot continue without repository
                return results
            else:
                results.append(("Repository Cloning", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - Repository cloned successfully"
                )))
            
            # Task 4: Overall.md File Detection
            overall_files = self._find_overall_md_files(temp_dir)
            if len(overall_files) == 0:
                results.append(("Overall.md File Detection", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"No overall.md file found in repository {github_url}"
                )))
                # Continue with remaining tasks even if overall.md is missing
                overall_md_path = None
            elif len(overall_files) > 1:
                # Select the overall.md file with the largest alphabetical path
                overall_files.sort()
                selected_file = overall_files[-1]
                relative_paths = [os.path.relpath(f, temp_dir) for f in overall_files]
                selected_relative = os.path.relpath(selected_file, temp_dir)
                results.append(("Overall.md File Detection", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - Found multiple overall.md files, selected: {selected_relative} (largest alphabetical path from: {', '.join(relative_paths)})"
                )))
                overall_md_path = selected_file
            else:
                relative_path = os.path.relpath(overall_files[0], temp_dir)
                results.append(("Overall.md File Detection", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - Found overall.md at: {relative_path}"
                )))
                overall_md_path = overall_files[0]
            
            # Task 5: Hunyuan CPP Files Check
            hunyuan_exists, hunyuan_msg = self._check_hunyuan_cpp_files(temp_dir)
            if not hunyuan_exists:
                results.append(("Hunyuan CPP Files Check", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Repository validation failed: {hunyuan_msg}"
                )))
            else:
                results.append(("Hunyuan CPP Files Check", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - {hunyuan_msg}"
                )))
            
            # Task 6: Overall.md Format Validation
            if overall_md_path:
                format_valid, format_msg = self._validate_overall_md_format(overall_md_path)
                if not format_valid:
                    results.append(("Overall.md Format Validation", ReviewResponse(
                        result=ReviewResult.FAIL,
                        reasoning=f"overall.md format validation failed: {format_msg}"
                    )))
                else:
                    results.append(("Overall.md Format Validation", ReviewResponse(
                        result=ReviewResult.PASS,
                        reasoning=f"✅ PASS - {format_msg}"
                    )))
            else:
                results.append(("Overall.md Format Validation", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning="Cannot validate overall.md format: file not found or multiple files detected"
                )))
            
            # Task 7: Solution.md Content Consistency
            solution_valid, solution_msg = self._validate_solution_md_consistency(temp_dir, document)
            if not solution_valid:
                results.append(("Solution.md Content Consistency", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"solution.md validation failed: {solution_msg}"
                )))
            else:
                results.append(("Solution.md Content Consistency", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - {solution_msg}"
                )))
            
            # Task 8: Problem Statement.md Content Consistency
            problem_valid, problem_msg = self._validate_problem_statement_md_consistency(temp_dir, document)
            if not problem_valid:
                results.append(("Problem Statement.md Content Consistency", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"problem_statement.md validation failed: {problem_msg}"
                )))
            else:
                results.append(("Problem Statement.md Content Consistency", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - {problem_msg}"
                )))
                
            return results
        
        except Exception as e:
            if not results:  # If no tasks completed yet
                results.append(("GitHub Validation Error", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Error during GitHub validation: {str(e)}"
                )))
            return results
        
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass  # Ignore cleanup errors


class DocumentReviewSystem:
    """Main system orchestrating all reviews"""
    
    def __init__(self, quiet_mode=False):
        # Initialize Anthropic client with API key from environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not found. Please set it in your .bashrc")
        
        self.client = Anthropic(api_key=api_key)
        self.detailed_output = []  # Capture all detailed output for the report
        self.output_lock = threading.Lock()  # Thread-safe output
        self.quiet_mode = quiet_mode  # Control output verbosity
        
        # Initialize GitHub validator (non-AI review)
        self.github_validator = GitHubReviewValidator(quiet_mode=quiet_mode)
        
        # Initialize all Ultimate reviewers - each as individual API call
        self.reviewers = {
            # Solution Uniqueness Validation
            "Unique Solution Validation": UniqueSolutionReviewer(self.client),
            
            # Time Complexity Check
            "Time Complexity Authenticity Check": TimeComplexityAuthenticityReviewer(self.client),
            
            # Code Quality
            "Style Guide Compliance": StyleGuideReviewer(self.client),
            "Naming Conventions": NamingConventionsReviewer(self.client),
            "Documentation Standards": DocumentationReviewer(self.client),
            
            # Response Quality  
            "Response Relevance to Problem": ResponseRelevanceReviewer(self.client),
            "Mathematical Equations Correctness": MathEquationsReviewer(self.client),
            "Problem Constraints Consistency": ConstraintsConsistencyReviewer(self.client),
            "Missing Approaches in Steps": MissingApproachesReviewer(self.client),
            "Code Elements Existence": CodeElementsExistenceReviewer(self.client),
            "Example Walkthrough with Optimal Algorithm": ExampleWalkthroughReviewer(self.client),
            "Time and Space Complexity Correctness": ComplexityCorrectnessReviewer(self.client),
            "Conclusion Quality": ConclusionQualityReviewer(self.client),
            
            # Problem Statement and Solution Quality
            "Problem Statement Consistency": ProblemConsistencyReviewer(self.client),
            "Solution Passability According to Limits": SolutionPassabilityReviewer(self.client),
            "Metadata Correctness": MetadataCorrectnessReviewer(self.client),
            "Test Case Validation": TestCaseValidationReviewer(self.client),
            "Sample Test Case Dry Run Validation": SampleDryRunValidationReviewer(self.client),
            "Note Section Explanation Approach": NoteSectionReviewer(self.client),
            
            # Reasoning Chain Quality
            "Inefficient Approaches Limitations": InefficientLimitationsReviewer(self.client),
            "Final Approach Discussion": FinalApproachDiscussionReviewer(self.client),
            "No Code in Reasoning Chains": NoCodeInReasoningReviewer(self.client),
            
            # Subtopic, Taxonomy, and Reasoning Analysis
            "Subtopic Taxonomy Validation": SubtopicTaxonomyReviewer(self.client),
            
            # Time and Memory Limit Validation
            "Time Limit Validation": TimeLimitValidationReviewer(self.client),
            "Memory Limit Validation": MemoryLimitValidationReviewer(self.client),
            "Typo and Spelling Check": TypoCheckReviewer(self.client),
            "Subtopic Relevance": SubtopicRelevanceReviewer(self.client),
            "Missing Relevant Subtopics": MissingSubtopicsReviewer(self.client),
            "No Predictive Headings in Thoughts": PredictiveHeadingsReviewer(self.client),
            "Chain Test Case Analysis Validation": Chain2TestCaseAnalysisReviewer(self.client),
            "Thought Heading Violations Check": ThoughtHeadingViolationsReviewer(self.client),
            "Mathematical Variables and Expressions Formatting": MathFormattingReviewer(self.client),
            "Comprehensive Reasoning Thoughts Review": ReasoningThoughtsReviewer(self.client)
        }
    
    def _thread_safe_print(self, message: str, force_quiet=False):
        """Thread-safe printing and logging"""
        with self.output_lock:
            # Always log to detailed output for the report
            self.detailed_output.append(message)
            # Only print to console if not in quiet mode (unless forced)
            if not self.quiet_mode and not force_quiet:
                print(message)
    
    def _progress_print(self, message: str):
        """Print progress messages (shown even in quiet mode)"""
        with self.output_lock:
            print(message)
            self.detailed_output.append(message)
    
    def _run_single_ai_review(self, review_name: str, reviewer, document: str, review_number: int) -> Tuple[str, ReviewResponse]:
        """Run a single AI review in a thread-safe manner"""
        start_time = time.time()
        try:
            # Show start message even in quiet mode for AI reviews
            start_msg = f"🔄 {review_number}. {review_name} - Starting..."
            self._thread_safe_print(start_msg)
            
            result = reviewer.review(document)
            
            elapsed_time = time.time() - start_time
            status_emoji = "✅" if result.result == ReviewResult.PASS else "❌"
            # Show completion message even in quiet mode for AI reviews
            completion_msg = f"{status_emoji} {review_number}. {review_name} - {result.result.value} ({elapsed_time:.1f}s)"
            self._thread_safe_print(completion_msg)
            
            return review_name, result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"💥 {review_number}. {review_name} - ERROR: {str(e)} ({elapsed_time:.1f}s)"
            self._thread_safe_print(error_msg)
            return review_name, ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Review failed with error: {str(e)}"
            )
    
    def _run_single_ai_review_quiet(self, review_name: str, reviewer, document: str, review_number: int) -> Tuple[str, ReviewResponse]:
        """Run a single AI review without showing start message (used when start message is shown upfront)"""
        start_time = time.time()
        try:
            result = reviewer.review(document)
            
            elapsed_time = time.time() - start_time
            status_emoji = "✅" if result.result == ReviewResult.PASS else "❌"
            # Show completion message
            completion_msg = f"{status_emoji} {review_number}. {review_name} - {result.result.value} ({elapsed_time:.1f}s)"
            self._progress_print(completion_msg)
            
            return review_name, result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"💥 {review_number}. {review_name} - ERROR: {str(e)} ({elapsed_time:.1f}s)"
            self._progress_print(error_msg)
            return review_name, ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Review failed with error: {str(e)}"
            )
    
    def load_document(self, file_path: str) -> str:
        """Load document from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Document file '{file_path}' not found")
        except Exception as e:
            raise Exception(f"Error reading document: {str(e)}")
    
    def run_reviews(self, document: str, resume_from: int = 0, github_only: bool = False, skip_github: bool = False, single_review = None) -> Dict[str, ReviewResponse]:
        """Run reviews on the document with various options"""
        results = {}
        self.detailed_output = []  # Reset for new run
        
        # Determine what to run
        if single_review:
            header_msg = f"🔍 Running single AI review: {single_review}..."
            self._progress_print(header_msg)
        elif github_only:
            header_msg = "🔍 Running GitHub Requirements Validation only..."
            self._progress_print(header_msg)
        elif skip_github:
            header_msg = f"🔍 Running AI reviews only (resuming from point {resume_from})..." if resume_from > 1 else "🔍 Running AI reviews only..."
            self._progress_print(header_msg)
        else:
            header_msg = f"🔍 Running complete review (AI + GitHub)..."
            self._progress_print(header_msg)
        
        separator = "=" * 70
        self._thread_safe_print(separator)
        
        # Convert reviewers dict to list for indexing
        reviewer_items = list(self.reviewers.items())
        
        # Separate GitHub and AI reviews
        github_reviews = [(name, reviewer) for name, reviewer in reviewer_items if reviewer is None]
        ai_reviews = [(name, reviewer) for name, reviewer in reviewer_items if reviewer is not None]
        
        # Handle GitHub-only mode with detailed tasks
        if github_only:
            start_time = time.time()
            github_tasks = self.github_validator.validate_github_requirements_detailed(document)
            end_time = time.time()
            
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60.0
            
            task_count = 0
            total_tasks = len(github_tasks)
            for task_name, result in github_tasks:
                task_count += 1
                # Just show progress in quiet mode
                progress_msg = f"🔄 GitHub Task {task_count}/{total_tasks}: {result.result.value}"
                self._progress_print(progress_msg)
                
                # Store detailed information for report only
                running_msg = f"\n🔄 Running GitHub Task: {task_name}"
                self._thread_safe_print(running_msg, force_quiet=True)
                
                # Show both seconds and minutes for better accuracy perception
                if duration_seconds < 60:
                    time_msg = f"⏱️ Completed in {duration_seconds:.1f} seconds ({duration_minutes:.2f} minutes)"
                else:
                    time_msg = f"⏱️ Completed in {duration_minutes:.2f} minutes ({duration_seconds:.1f} seconds)"
                self._thread_safe_print(time_msg, force_quiet=True)
                
                results[task_name] = result
                
                result_msg = f"Result: {result.result.value}"
                self._thread_safe_print(result_msg, force_quiet=True)
                
                if result.result == ReviewResult.FAIL:
                    issues_header = "\nIssues Found:"
                    self._thread_safe_print(issues_header, force_quiet=True)
                    self._thread_safe_print(result.reasoning, force_quiet=True)
                
                sep_msg = "-" * 40
                self._thread_safe_print(sep_msg, force_quiet=True)
            
            return results
        
        # Handle single review mode
        if single_review:
            reviewer = self.reviewers[single_review]
            if reviewer is None:
                # This is a GitHub task, handle it specially
                github_tasks = self.github_validator.validate_github_requirements_detailed(document)
                for task_name, result in github_tasks:
                    if task_name == single_review:
                        running_msg = f"\n🔄 Running GitHub Task: {task_name}"
                        print(running_msg)
                        self.detailed_output.append(running_msg)
                        
                        result_msg = f"Result: {result.result.value}"
                        print(result_msg)
                        self.detailed_output.append(result_msg)
                        
                        if result.result == ReviewResult.FAIL:
                            issues_header = "\nIssues Found:"
                            print(issues_header)
                            self.detailed_output.append(issues_header)
                            print(result.reasoning)
                            self.detailed_output.append(result.reasoning)
                        
                        results[single_review] = result
                        break
            else:
                # This is an AI review - use the same format as parallel reviews
                running_msg = f"🔄 1. {single_review} - Starting..."
                self._thread_safe_print(running_msg)
                
                start_time = time.time()
                
                try:
                    result = reviewer.review(document)
                    
                    end_time = time.time()
                    duration_seconds = end_time - start_time
                    
                    status_emoji = "✅" if result.result == ReviewResult.PASS else "❌"
                    completion_msg = f"{status_emoji} 1. {single_review} - {result.result.value} ({duration_seconds:.1f}s)"
                    self._thread_safe_print(completion_msg)
                    
                    results[single_review] = result
                    
                except Exception as e:
                    elapsed_time = time.time() - start_time
                    error_msg = f"💥 1. {single_review} - ERROR: {str(e)} ({elapsed_time:.1f}s)"
                    self._thread_safe_print(error_msg)
                    
                    results[single_review] = ReviewResponse(
                        result=ReviewResult.FAIL,
                        reasoning=f"Review failed with error: {str(e)}"
                    )
            
            return results
        
        # Handle AI reviews with resume functionality
        start_index = resume_from
        if start_index < 1:
            start_index = 1
        elif start_index > len(ai_reviews):
            warning_msg = f"⚠️  Resume point {resume_from} is beyond available AI reviews ({len(ai_reviews)}). Starting from beginning."
            print(warning_msg)
            self.detailed_output.append(warning_msg)
            start_index = 1
        
        # Add skipped AI reviews as "SKIPPED"
        for i in range(1, start_index):
            review_name, _ = ai_reviews[i-1]
            results[review_name] = ReviewResponse(
                result=ReviewResult.PASS,
                reasoning="SKIPPED - Resumed from later point"
            )
        
        # Run AI reviews in parallel
        ai_reviews_to_run = ai_reviews[start_index-1:]  # Reviews to actually run
        
        if ai_reviews_to_run:
            parallel_msg = f"🚀 Starting {len(ai_reviews_to_run)} AI reviews..."
            self._progress_print(parallel_msg)
            
            # Show all starting messages immediately
            for i, (review_name, reviewer) in enumerate(ai_reviews_to_run):
                review_number = start_index + i
                start_msg = f"🔄 {review_number}. {review_name} - Starting..."
                self._progress_print(start_msg)
            
            # Use ThreadPoolExecutor for parallel execution
            max_workers = min(8, len(ai_reviews_to_run))  # Limit concurrent threads to avoid rate limiting
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all AI reviews to the thread pool
                future_to_review = {}
                for i, (review_name, reviewer) in enumerate(ai_reviews_to_run):
                    review_number = start_index + i
                    future = executor.submit(self._run_single_ai_review_quiet, review_name, reviewer, document, review_number)
                    future_to_review[future] = (review_name, review_number)
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_review):
                    review_name, result = future.result()
                    results[review_name] = result
            
            # Summary after all parallel reviews complete
            total_completed = len(ai_reviews_to_run)
            # Count only the AI reviews we just ran
            ai_passed = sum(1 for name, result in results.items() 
                          if any(review_name == name for review_name, _ in ai_reviews_to_run) 
                          and result.result == ReviewResult.PASS)
            ai_failed = total_completed - ai_passed
            parallel_complete_msg = f"✅ AI reviews completed: {ai_passed} passed, {ai_failed} failed"
            self._progress_print(parallel_complete_msg)
            
        # Run GitHub validation at the end (unless skipped)
        if not skip_github:
            # Show progress message
            progress_msg = f"🔄 Running GitHub validation..."
            self._progress_print(progress_msg)
            
            # Use the detailed GitHub tasks approach for consistency with --github-only mode
            start_time = time.time()
            github_tasks = self.github_validator.validate_github_requirements_detailed(document)
            end_time = time.time()
            
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60.0
            
            # Count passing tasks for summary
            passed_tasks = sum(1 for _, result in github_tasks if result.result == ReviewResult.PASS)
            total_tasks = len(github_tasks)
            
            # Show overall result progress
            github_result_msg = f"✅ GitHub validation: {passed_tasks}/{total_tasks} passed"
            self._progress_print(github_result_msg)
            
            # Process each task for detailed logging
            for task_name, result in github_tasks:
                # Store result immediately without logging task details to detailed_output
                # (they will be logged in the report generation phase instead)
                results[task_name] = result
        
        return results
    
    def generate_report(self, results: Dict[str, ReviewResponse]) -> str:
        """Generate comprehensive review report for all 30 review points"""
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
        
        # Separate GitHub and AI results
        # GitHub results include both the main validation and individual GitHub tasks
        github_keywords = ["GitHub Requirements Validation", "GitHub URL Extraction", "GitHub URL Parsing", 
                          "Repository Cloning", "Overall.md File Detection", "Hunyuan CPP Files Check",
                          "Overall.md Format Validation", "Solution.md Content Consistency", 
                          "Problem Statement.md Content Consistency"]
        github_results = {name: result for name, result in results.items() 
                         if any(keyword in name for keyword in github_keywords)}
        ai_results = {name: result for name, result in results.items() 
                     if not any(keyword in name for keyword in github_keywords)}
        
        # Count results separately
        github_passed = sum(1 for r in github_results.values() if r.result == ReviewResult.PASS)
        github_failed = len(github_results) - github_passed
        
        ai_passed = sum(1 for r in ai_results.values() if r.result == ReviewResult.PASS and r.reasoning != "SKIPPED - Resumed from later point")
        ai_skipped = sum(1 for r in ai_results.values() if r.reasoning == "SKIPPED - Resumed from later point")
        ai_total = len(ai_results)
        ai_failed = ai_total - ai_passed - ai_skipped
        
        # Summary
        if github_results and ai_results:
            if ai_skipped > 0:
                report.append(f"📊 SUMMARY: GitHub: {github_passed}/{len(github_results)} passed | AI: {ai_passed}/{ai_total - ai_skipped} passed ({ai_skipped} skipped)")
            else:
                report.append(f"📊 SUMMARY: GitHub: {github_passed}/{len(github_results)} passed | AI: {ai_passed}/{ai_total} passed")
        elif github_results:
            report.append(f"📊 SUMMARY: GitHub: {github_passed}/{len(github_results)} passed")
        elif ai_results:
            if ai_skipped > 0:
                report.append(f"📊 SUMMARY: AI: {ai_passed}/{ai_total - ai_skipped} passed ({ai_skipped} skipped)")
            else:
                report.append(f"📊 SUMMARY: AI: {ai_passed}/{ai_total} passed")
        
        total_failed = github_failed + ai_failed
        if total_failed > 0:
            if github_failed > 0 and ai_failed > 0:
                report.append(f"⚠️  {total_failed} review(s) failed (GitHub: {github_failed}, AI: {ai_failed})")
            elif github_failed > 0:
                report.append(f"⚠️  {github_failed} GitHub review(s) failed")
            else:
                report.append(f"⚠️  {ai_failed} AI review(s) failed")
        
        if ai_skipped > 0:
            report.append(f"⏭️  {ai_skipped} AI review(s) skipped")
        report.append("")
        
        # Overall status
        if total_failed == 0 and ai_skipped == 0:
            report.append("🎉 OVERALL STATUS: ALL REVIEWS PASSED")
        elif total_failed == 0:
            report.append("🎉 OVERALL STATUS: ALL EXECUTED REVIEWS PASSED")
        else:
            report.append("⚠️  OVERALL STATUS: SOME REVIEWS FAILED")
        
        report.append("")
        report.append("=" * 70)
        
        # Results - show AI reviews first, then GitHub results
        ai_counter = 1
        for review_name, result in results.items():
            # Skip detailed GitHub tasks in first pass - show them after AI reviews
            if any(keyword in review_name for keyword in github_keywords):
                continue
                
            report.append("")
            report.append(f"📝 {ai_counter}. {review_name.upper()}")
            ai_counter += 1
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
        
        # Now add GitHub results after AI reviews
        github_counter = ai_counter
        for review_name, result in results.items():
            # Only show GitHub tasks in this pass
            if not any(keyword in review_name for keyword in github_keywords):
                continue
                
            report.append("")
            report.append(f"📝 {github_counter}. {review_name.upper()}")
            github_counter += 1
            report.append("-" * 50)
            
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
               '  python3 document_reviewer.py doc.txt                    # Run GitHub + AI reviews\n'
               '  python3 document_reviewer.py doc.txt --github-only      # Run only GitHub validation\n'
               '  python3 document_reviewer.py doc.txt --ai-only          # Run only AI reviews\n'
               '  python3 document_reviewer.py doc.txt --resume 5         # Run GitHub + AI (AI from point 5)\n'
               '  python3 document_reviewer.py doc.txt --ai-only --resume 5  # Run only AI from point 5\n'
               '  python3 document_reviewer.py doc.txt --single-review "Memory Limit Validation"  # Run single AI review\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('file', help='Path to the text file to review')
    parser.add_argument('--resume', type=int, default=1, metavar='X',
                       help='Resume AI reviews from point X (1-N, default: 1). GitHub validation always runs when enabled.')
    parser.add_argument('--github-only', action='store_true',
                       help='Run only GitHub requirements validation (non-AI review)')
    parser.add_argument('--ai-only', action='store_true',
                       help='Run only AI reviews, skip GitHub validation')
    parser.add_argument('--single-review', type=str, metavar='NAME',
                       help='Run only a single AI review by name (e.g., "Solution Uniqueness Validation")')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output (show all execution details in terminal)')
    
    args = parser.parse_args()
    
    # Handle conflicting arguments
    if args.github_only and args.ai_only:
        print("❌ Cannot use --github-only with --ai-only")
        sys.exit(1)
    
    if args.single_review and (args.github_only or args.ai_only):
        print("❌ Cannot use --single-review with other mode options")
        sys.exit(1)
    
    # Normalize skip options
    skip_github = args.ai_only
    github_only = args.github_only
    single_review = args.single_review
    
    # Initialize review system first for dynamic validation
    review_system = DocumentReviewSystem(quiet_mode=False)  # Use verbose mode for validation
    
    # Validate single review name if specified
    if single_review:
        available_reviews = list(review_system.reviewers.keys())
        ai_reviews = [name for name, reviewer in review_system.reviewers.items() if reviewer is not None]
        
        if single_review not in available_reviews:
            print(f"❌ Invalid review name: '{single_review}'")
            print(f"📋 Available AI reviews:")
            for name in ai_reviews:
                print(f"   - {name}")
            sys.exit(1)
    
    # Validate resume point (only applies to AI reviews)
    ai_reviewers_count = len([r for name, r in review_system.reviewers.items() if r is not None])
    if not single_review and (args.resume < 1 or args.resume > ai_reviewers_count):
        print(f"❌ Invalid resume point: {args.resume}. Must be between 1 and {ai_reviewers_count} for AI reviews.")
        sys.exit(1)
    
    try:
        # Initialize review system with quiet mode (unless verbose flag is set)
        review_system = DocumentReviewSystem(quiet_mode=not args.verbose)
        
        # Load document
        print(f"📖 Loading document from {args.file}...")
        document = review_system.load_document(args.file)
        print(f"✅ Document loaded ({len(document)} characters)")
        
        # Model information
        print("\n🤖 Model Configuration:")
        print("   Primary: Claude Opus 4.1 (claude-opus-4-1-20250805) with 20k thinking budget")
        print("   Secondary: Claude Sonnet 4 (claude-sonnet-4-20250514) for cleanup operations")
        print("   Max tokens: 32,000 (Opus 4.1) / 64,000 (Sonnet 4 cleanup)")
        print()
        
        # Run reviews with specified options
        results = review_system.run_reviews(
            document, 
            resume_from=args.resume,
            github_only=github_only,
            skip_github=skip_github,
            single_review=single_review
        )
        
        # Generate and save report (don't display detailed report in terminal)
        if not args.verbose:
            progress_msg = "📋 Generating final report..."
            print(progress_msg)
        else:
            print("\n" + "=" * 70)
            print("📋 GENERATING FINAL REPORT - ULTIMATE POINT ANALYSIS")
            print("=" * 70)
        
        report = review_system.generate_report(results)
        
        # Only display full report in verbose mode
        if args.verbose:
            print("\n" + report)
        
        # Save report
        review_system.save_report(report, args.file)
        
        # Exit code based on results (excluding skipped ones)
        failed_reviews = [name for name, result in results.items() 
                         if result.result == ReviewResult.FAIL]
        
        if failed_reviews:
            # Use the same classification logic as in generate_report
            github_keywords = ["GitHub Requirements Validation", "GitHub URL Extraction", "GitHub URL Parsing", 
                              "Repository Cloning", "Overall.md File Detection", "Hunyuan CPP Files Check",
                              "Overall.md Format Validation", "Solution.md Content Consistency", 
                              "Problem Statement.md Content Consistency"]
            github_failures = [name for name in failed_reviews 
                             if any(keyword in name for keyword in github_keywords)]
            ai_failures = [name for name in failed_reviews 
                         if not any(keyword in name for keyword in github_keywords)]
            
            if github_failures and ai_failures:
                print(f"\n❌ Review completed with {len(failed_reviews)} failures ({len(github_failures)} GitHub, {len(ai_failures)} AI)")
            elif github_failures:
                print(f"\n❌ Review completed with {len(github_failures)} GitHub failure(s)")
            else:
                print(f"\n❌ Review completed with {len(ai_failures)} AI failure(s)")
            sys.exit(1)
        else:
            print("\n✅ All reviews passed successfully!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()