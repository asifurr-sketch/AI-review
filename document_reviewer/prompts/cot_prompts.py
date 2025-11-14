"""
Chain of Thought (CoT) review prompts for document validation
"""


class CoTPrompts:
    """Container for Chain of Thought review prompts"""
    
    @staticmethod
    def get_cot_structure_prompt():
        """Check if CoT follows the required structure - includes chain ordering, titles, counts, and manuscript style validation"""
        return """
You are an expert CoT structure evaluator.

TASK: Verify CoT structural format AND manuscript style.

REQUIREMENTS:

1. CHAIN_01: Problem understanding only (no solutions)
2. CHAIN_02: Test case explanation from problem statement
3. Chain titles: Clear, descriptive, action-oriented (not predictive like "Optimal Approach Discussion")
4. Minimum chains: 1 understanding, 1 test cases, 2+ problem-solving, 1 inefficient (where feasible)
5. Manuscript style: Exploration THEN conclusions (not "The answer is X. Here's why...")
6. No predictive content that reveals future chains upfront

LOCATION REPORTING:
- Use EXACT identifiers: "CHAIN_01", "THOUGHT_02_01" (NEVER "CHAIN_XX")
- Quote violations

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_thought_quality_prompt():
        """Check if thoughts contain proper reasoning and justification"""
        return """
You are an expert CoT reasoning evaluator.

TASK: Verify thoughts (THOUGHT_XX_YY) contain proper reasoning.

REQUIREMENTS:
- Explain WHY approach chosen, WHY others discarded
- Justify data structure choices with alternatives discussed
- Explain time/space complexity implications
- Discuss corner cases and impact
- All complexity discussed explicitly

LOCATION REPORTING: Use EXACT identifiers like "THOUGHT_03_02"

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_approach_progression_prompt():
        """Check if approaches progress from inefficient to optimal"""
        return """
You are an expert CoT progression evaluator.

TASK: Verify approaches progress from simple/inefficient to optimal.

REQUIREMENTS:
- Start with simpler approaches
- Each new approach improves previous (time/space complexity)
- Inefficient approaches: mention limitations/cons explicitly
- Transitions: explain WHY shift needed, reference previous limitations
- Final approach: explain improvements over previous
- Approaches relevant to problem type (graph→graph algorithms, DP→DP approaches)

LOCATION REPORTING: Use EXACT "CHAIN_03", "CHAIN_05" etc

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_variable_consistency_prompt():
        """Check variable name consistency between prompt and CoT"""
        return """
You are an expert CoT consistency validator.

TASK: Verify variable names match problem statement throughout all chains.

REQUIREMENTS:
- Use same names as problem (if problem uses 'n', chains use 'n' not 'size')
- Consistent across all chains
- Standard abbreviations (i,j,k for loops, dp for array) acceptable
- No unexplained renaming

LOCATION REPORTING: Use EXACT "CHAIN_02", quote mismatches

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_line_reference_prompt():
        """Check that chains don't reference line numbers when no code is present"""
        return """
You are an expert CoT validation specialist.

TASK: Verify chains don't reference code line numbers without showing code.

REQUIREMENTS:
- NO "(Line 11)" references in chains without code blocks
- Line references only acceptable in response section with code shown
- Use concept references instead ("the initialization step")

LOCATION REPORTING: Use EXACT "CHAIN_04", quote problematic references

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_logical_continuity_prompt():
        """Check that each chain logically follows from the previous one"""
        return """
You are an expert CoT continuity evaluator.

TASK: Verify each chain logically follows from previous, with failure reflections.

REQUIREMENTS:
- Build upon previous insights
- Acknowledge failures/limitations before new approach
- Justify new approaches based on previous discoveries
- No unexplained jumps
- Self-contained logical progression

LOCATION REPORTING: Use transitions like "CHAIN_03 → CHAIN_04"

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_markdown_formatting_prompt():
        """Check that code blocks use proper markdown formatting"""
        return """
You are an expert CoT formatting validator.

TASK: Verify proper markdown code block formatting.

REQUIREMENTS:
- Fenced blocks: ```cpp or ```python (with language tag)
- Complete blocks (opening + closing ```)
- Correct language tag matching actual code
- No inline backticks for multi-line code

LOCATION REPORTING: Use EXACT "CHAIN_03", "Response section"

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_metadata_alignment_prompt():
        """Check that metadata complexity matches CoT discussions"""
        return """
You are an expert metadata validator.

TASK: Verify metadata time complexities match chain discussions.

REQUIREMENTS:
- "Number of Approaches" matches actual chain count
- Each approach's time complexity in metadata matches chain discussion
- Variables in metadata consistent with chains
- All complexities discussed explicitly in chains
- Time complexity explicitly included in metadata

LOCATION REPORTING: Reference metadata fields and corresponding chains

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_language_consistency_prompt():
        """Check that chains don't mention wrong programming language"""
        return """
You are an expert CoT language consistency validator.

TASK: Verify chains don't mention wrong programming language.

REQUIREMENTS:
- If C++, don't mention Python/python/py
- If Python, don't mention C++/cpp/c++
- No language-specific terminology for wrong language
- Generic algorithm discussions acceptable

LOCATION REPORTING: Use EXACT "CHAIN_03", quote wrong mentions

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_constraint_validation_prompt():
        """Check if time and space constraints are present and correctly calculated"""
        return """
You are an expert constraint validator.

TASK: Verify time and space constraints present in problem.

REQUIREMENTS:
- Time limit stated clearly
- Space limit stated clearly
- If missing: suggest reasonable values based on brute force runtime and space complexity
- Constraints allow optimal solution, prevent inefficient ones

LOCATION REPORTING: Reference "Problem Statement", "Metadata"

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_response_structure_prompt():
        """Check if response section follows the required structure"""
        return """
You are an expert response section evaluator.

TASK: Verify response has all required components and is self-contained.

REQUIRED STRUCTURE:
1. Problem Understanding & Key Observations
2. Optimal Approach (narrative, NO pseudocode)
3. Full Code
4. Code Explanation / Example Execution
5. Complexity Analysis (with math formatting)
6. Conclusion

CRITICAL: Response must NOT reference chains (self-contained)

LOCATION REPORTING: Identify missing/inadequate components

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_plagiarism_check_prompt():
        """Check if final code is plagiarized (basic heuristic check)"""
        return """
You are an expert code originality validator.

TASK: Heuristic analysis for plagiarism indicators.

SUSPICIOUS INDICATORS:
- Code contradicts explained approach in chains
- Implementation details never discussed in reasoning
- Variable names/structure don't match problem context
- Code doesn't align with chain progression
- Unexplained optimizations never mentioned

ACCEPTABLE:
- Standard algorithms (sort, binary search)
- Common data structures
- Typical patterns (two pointers, sliding window)

FOCUS: Consistency between chains and final code

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

    @staticmethod
    def get_cot_accuracy_check_prompt():
        """Check if thoughts and chains are accurate and correct"""
        return """
You are an expert algorithmic accuracy validator.

TASK: Verify technical accuracy of all thoughts and chains.

CHECK:
- Algorithm correctness for the problem
- Complexity analysis accuracy (time and space)
- Data structure properties correct
- Mathematical formulas correct
- Problem interpretation correct

LOCATION REPORTING: Use EXACT "CHAIN_02", "THOUGHT_04_02", quote inaccurate statements

FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""
