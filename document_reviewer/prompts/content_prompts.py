"""
Review prompts for document validation
"""


class Prompts:
    """Container for review prompts"""
    
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

    @staticmethod
    def get_math_equations_prompt():
        """Enhanced mathematical equations correctness check with specific location reporting"""
        return """
You are an expert mathematical reviewer specializing in precise error identification.

TASK: Check if the mathematical equations throughout the document are mathematically correct.

CRITICAL LOCATION REPORTING REQUIREMENTS:
1. NEVER use generic placeholders like "CHAIN_XX" or "THOUGHT_XX_YY"  
2. ALWAYS identify EXACT locations using specific identifiers from the document
3. Use format: "CHAIN_01", "CHAIN_05", "THOUGHT_03_02", "Metadata section", etc.
4. If you find violations in CHAIN_03, write "CHAIN_03", NOT "CHAIN_XX"
5. If you find violations in THOUGHT_04_02, write "THOUGHT_04_02", NOT "THOUGHT_XX_YY"

WHAT TO EXAMINE:
- Mathematical notation correctness (Big-O, equations, formulas)
- Proper use of mathematical symbols and operators  
- Accuracy of mathematical statements and proofs
- Consistency in mathematical terminology
- Correct application of mathematical principles

VIOLATION REPORTING FORMAT:
For each mathematical error found, specify:
- EXACT location (specific chain, thought, or section identifier)
- Quote the incorrect mathematical expression
- Explain what is mathematically wrong
- Provide the correct mathematical form

EXAMPLE GOOD REPORTING:
- CHAIN_03: Big-O notation incorrectly written as "O!(n log n)" instead of "O(n log n)" (lines 45-46)
- THOUGHT_02_01: Mathematical formula "∑(i=1 to n) = n(n-1)/2" is incorrect; should be "∑(i=1 to n) i = n(n+1)/2"
- Response section: Space complexity "O(n,m)" uses ambiguous comma notation; should be "O(n·m)" or "O(nm)"

EXAMPLE BAD REPORTING (DO NOT DO THIS):
- CHAIN_XX: Big-O notation problems found
- Multiple mathematical errors in reasoning chains  
- Some notation issues detected

Examine the entire document systematically and report ALL mathematical correctness violations with exact locations.

RESPONSE FORMAT:
Provide detailed analysis with specific locations, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

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

    @staticmethod
    def get_metadata_correctness_prompt():
        """Check metadata correctness"""
        return """
You are an expert response evaluator. Is the metadata correct?

METADATA VALIDATION REQUIREMENTS:
The document MUST contain a metadata section at the beginning that contains all required fields:

# Metadata

REQUIRED FIELDS (order not strictly enforced, but all must be present):
- **Category:** - [value]
- **GitHub URL:** - [GitHub URL]
- **Topic:** - [value]  
- **Subtopic:** - [JSON array of subtopics]
- **Difficulty:** - [difficulty level]
- **Languages:** - [programming languages]
- **Number of Approaches:** - [approach count and complexity progression]
- **Number of Chains:** - [number]

REQUIRED FORMAT SPECIFICATIONS:
2. Each field must use the pattern: **FieldName:** - value
3. There must be a space after the colon, then a dash, then a space before the value
4. All fields must be present (order is flexible)
5. The subtopic must be a valid JSON array format with proper quotes
6. The GitHub URL must be a valid GitHub repository URL starting with https://github.com/

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
2. All required fields are present in correct order: Category, GitHub URL, Topic, Subtopic, Difficulty, Languages, Number of Approaches, Number of Chains
3. Each field follows the exact format: **FieldName:** - value
4. GitHub URL is a valid GitHub repository URL starting with https://github.com/
5. Number of Approaches contains both count and valid time complexity progression
6. Number of Chains matches actual CHAIN_XX sections count
7. Subtopic is a properly formatted JSON array
8. Values are appropriate for the content

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

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

    @staticmethod
    def get_time_complexity_authenticity_prompt():
        """Enhanced time complexity check with specific identification"""
        return """
You are an expert algorithm complexity analyst specializing in precise violation identification.

TASK: Verify that time complexity in metadata covers ALL approaches and uses only variables from the problem statement.

CRITICAL LOCATION REPORTING REQUIREMENTS:
1. NEVER use "CHAIN_XX" - use exact identifiers like "CHAIN_01", "CHAIN_03", etc.
2. NEVER use "THOUGHT_XX_YY" - use exact identifiers like "THOUGHT_02_01", "THOUGHT_04_03", etc.  
3. Always reference specific sections: "Metadata section", "Number of Approaches field", etc.
4. Quote exact text when showing violations
5. Provide specific line references when available

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

VIOLATION REPORTING FORMAT:
- [EXACT LOCATION]: [Specific violation with quoted text] 
- [EXACT LOCATION]: [Missing approach or incorrect variable usage]

EXAMPLE GOOD REPORTING:
- Metadata section: Uses variable "m" in "O(n*m)" but problem statement only defines "N" and "K"
- Number of Approaches field: Claims "3 approaches" but only lists 2 complexities: "O(N²) → O(N)"
- CHAIN_04: Discusses O(N log N) approach but metadata missing this complexity in progression

EXAMPLE BAD REPORTING (NEVER DO THIS):
- CHAIN_XX: Variable problems found
- Metadata has some issues
- Multiple complexity errors detected

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

RESPONSE FORMAT:
Examine ALL sections systematically, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

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

    @staticmethod
    def get_typo_check_prompt():
        """Enhanced typo and spelling check with precise location identification"""
        return """
You are an expert proofreader specializing in precise error location identification.

TASK: Find ALL typos, spelling errors, and grammatical mistakes throughout the document.

CRITICAL LOCATION REPORTING REQUIREMENTS:
1. Use EXACT identifiers: "CHAIN_01", "CHAIN_05", "THOUGHT_03_02", etc.
2. NEVER use generic placeholders like "CHAIN_XX" or "THOUGHT_XX_YY"
3. Include specific line numbers when possible
4. Quote the exact erroneous text
5. Provide the correct spelling/grammar

WHAT TO CHECK:
- Misspelled words (e.g., "recieve" → "receive")
- Grammar errors (subject-verb disagreement, tense inconsistencies) 
- Punctuation errors (missing commas, incorrect apostrophes)
- Formatting inconsistencies
- Mathematical notation typos (e.g., "O!" instead of "O()")
- Technical term misspellings
- Duplicated text or phrases
- Errant punctuation marks

VIOLATION REPORTING FORMAT:
- [EXACT LOCATION]: "[Quoted erroneous text]" → Correction: "[corrected text]"

EXAMPLE GOOD REPORTING:
- CHAIN_03: "algoritm" → Correction: "algorithm" (line 23)
- THOUGHT_02_01: "its a valid approach" → Correction: "it's a valid approach" 
- Response section: Duplicated text "Space (analysis):" appears twice consecutively
- CHAIN_05: Mathematical notation "O!\\Bigl(" contains erroneous exclamation mark → Correction: "O\\Bigl("
- THOUGHT_04_05: Formula "M = max_{y ≠ s,; 1 ≤ i ≤ w}" contains errant semicolon → Correction: "M = max_{y ≠ s, 1 ≤ i ≤ w}"

EXAMPLE BAD REPORTING (DO NOT DO THIS):
- CHAIN_XX: Spelling errors found
- Multiple typos in reasoning chains
- Some grammatical issues detected

Examine EVERY section systematically for any spelling, grammar, or typographical errors.

RESPONSE FORMAT:
List all specific violations with exact locations, then end with:
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

    @staticmethod
    def get_example_validation_prompt():
        """Comprehensive validation of examples from metadata.json against problem statement"""
        return """
You are an expert validator specializing in competitive programming problem verification.

TASK: Perform a comprehensive validation that ALL examples in the metadata.json match EXACTLY with the examples in the problem statement.

You will receive a document containing:
1. The problem statement with examples in the **[Prompt]** section
2. A GitHub repository that contains metadata.json with examples

VALIDATION REQUIREMENTS:

1. **EXACT MATCH OF EXAMPLES:**
   - Every example in metadata.json MUST appear in the problem statement
   - Every example in the problem statement MUST appear in metadata.json
   - Input values must match EXACTLY (character by character, ignoring whitespace)
   - Output values must match EXACTLY (character by character, ignoring whitespace)
   - Order of examples should be consistent

2. **COUNT VERIFICATION:**
   - The number of examples in metadata.json must equal the number in problem statement
   - No missing examples
   - No extra examples

3. **FORMAT VERIFICATION:**
   - Check that inputs are properly formatted
   - Check that outputs are properly formatted
   - Verify that code blocks or formatting don't cause mismatches

4. **CONTENT COVERAGE:**
   - All test cases mentioned should be validated
   - Edge cases should be properly represented
   - Multi-line inputs/outputs should be handled correctly

DETAILED ANALYSIS REQUIRED:

For EACH example, verify:
- Example number/index (e.g., Example 1, Example 2)
- Input data matches exactly
- Output data matches exactly
- Any explanations or notes are consistent

VIOLATION REPORTING:

If ANY mismatch is found, report:
- Which example number has the issue
- What is in metadata.json
- What is in the problem statement
- The specific difference (missing, extra, or different values)
- Quote the exact mismatching parts

EXAMPLE VIOLATION REPORT:
```
Example 2 Input Mismatch:
- metadata.json has: "9 1 7 0 998244352"
- Problem statement has: "9 1 7 0 998244353"
- Difference: Last value differs (998244352 vs 998244353)
```

PASS CONDITIONS:
- All examples in metadata.json match problem statement exactly
- No missing or extra examples
- Input/output values are identical
- Count matches perfectly

FAIL CONDITIONS:
- Any example doesn't match
- Missing examples in either location
- Extra examples in either location
- Any input or output value differs
- Count mismatch

RESPONSE FORMAT:
Provide detailed analysis of each example comparison, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""


