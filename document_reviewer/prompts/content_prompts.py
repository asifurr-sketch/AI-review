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
You are an expert algorithm complexity analyst. Evaluate if the provided solution can pass within the given time and memory limits.

IMPORTANT: Be realistic and practical. Most competitive programming solutions are designed to pass, so only flag CLEAR violations, not marginal cases.

WHAT TO ANALYZE:

1. **Time Complexity Analysis:**
   - Extract the time complexity from the solution/metadata
   - Find the maximum input constraints from the problem statement
   - Calculate worst-case number of operations
   - Compare against the time limit (1 second ≈ 10^8 operations, 2 seconds ≈ 2×10^8 operations)
   - Allow reasonable constant factors (2-5x is acceptable)

2. **Memory Complexity Analysis:**
   - Extract the space complexity from the solution/metadata
   - Calculate worst-case memory usage based on constraints
   - Compare against the memory limit
   - Consider language-specific overheads realistically:
     * Python: 3-5x overhead for complex objects, but simple data types are much less
     * C++/C: Minimal overhead (1-1.5x)
     * Java: 2-3x overhead
   - **CRITICAL: Only flag if memory usage clearly exceeds 75% of limit with overhead**

3. **Key Factors to Check:**
   - Does the time complexity allow completion within time limit?
   - Does the space complexity fit within memory limit?
   - Are there catastrophic constant factors (100x+)?
   - Are there hidden exponential complexities?

MEMORY ESTIMATION GUIDELINES (Python):

**Small Data Structures (ALMOST ALWAYS ACCEPTABLE):**
- Output buffer storing t results where t ≤ 10^6: ~10-50 MB with overhead → PASS for 32MB+ if < 20MB estimated
- Single array of 10^5 integers: ~3-5 MB → PASS for any reasonable limit
- Hash map with 10^5 entries: ~10-15 MB → PASS for 32MB+ limits
- String buffer < 10^6 characters: ~5-10 MB → PASS for 32MB+ limits

**Realistic Calculations:**
- List of t=2×10^5 small strings (10-20 chars each):
  * Raw: 200K × 15 = 3 MB
  * Python overhead (strings + list): ~2-3x = 6-9 MB
  * Verdict for 32 MB limit: **PASS** (uses < 30% of limit)

- Array of n=10^5 integers:
  * Python list: ~28 bytes per int object
  * Total: 10^5 × 28 = 2.8 MB
  * Verdict for 32 MB limit: **PASS** (uses < 10% of limit)

**ONLY FLAG AS FAIL:**
- 2D array 10^4 × 10^4 for 32MB limit (100M elements × 28 bytes = 2.8 GB) → FAIL
- Storing all test case inputs when t=10^6 and each input is 10^5 elements → FAIL
- Exponential space like 2^n where n > 20 → FAIL
- Building string of length > 10^7 for 32MB limit → LIKELY FAIL

**DO NOT FLAG (THESE ARE ACCEPTABLE):**
- Output buffers with t ≤ 10^6 results
- Single work arrays of size ≤ 10^6
- Hash maps/sets with ≤ 10^6 entries for limits ≥ 64MB
- Small administrative overhead (counters, temp variables)
- Streaming/online solutions with O(1) or O(log n) space

VALIDATION STEPS:

1. Identify time complexity and maximum constraints
2. Calculate operations: ops = f(max_constraints)
3. **Time verdict**: FAIL only if ops > 5×10^8 for 1 second limit (be generous)
4. Identify space complexity and calculate memory
5. Apply conservative overhead multiplier (2-3x for Python, not 5x)
6. **Memory verdict**: FAIL only if estimated_memory > 0.75 × memory_limit
7. **Overall**: PASS if both time and memory are reasonable

EXAMPLE ANALYSIS:

Problem: t ≤ 2×10^5, each test case produces one integer result, Memory: 32 MB
Code: Stores all t results in list before printing

Memory Calculation:
- Results: 2×10^5 strings (avg 15 bytes each)
- Raw data: 3 MB
- Python overhead (string objects + list): 2.5x → 7.5 MB
- Total: ~7.5 MB
- Limit: 32 MB
- Usage: 7.5/32 = 23% → **PASS** ✅

PASS if: Solution uses < 75% of memory limit and < 5× time budget (be practical!)
FAIL if: Solution clearly exceeds limits (e.g., uses > 80% of memory, or 10× time budget)

RESPONSE FORMAT:
Provide detailed analysis showing realistic calculations, then end with:
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

REQUIRED FIELDS (all must be present, order does NOT matter):
- **Category:** - [value]
- **GitHub URL:** - [GitHub URL]  OR  **GitHub:** - [GitHub URL]
- **Topic:** - [value]  
- **Subtopic:** - [JSON array of subtopics]
- **Difficulty:** - [difficulty level]
- **Languages:** - [programming languages]
- **Number of Approaches:** - [approach count and complexity progression]
- **Number of Chains:** - [number]

REQUIRED FORMAT SPECIFICATIONS:
2. Each field must use the pattern: **FieldName:** - value
3. There must be a space after the colon, then a dash, then a space before the value
4. All fields must be present (order does NOT matter - any order is acceptable)
5. The subtopic must be a valid JSON array format with proper quotes
6. GitHub field can be either "**GitHub URL:**" or "**GitHub:**" - both are acceptable
7. The GitHub URL must be a valid GitHub repository URL starting with https://github.com/

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
- Variables used in the complexity progression must be consistent with those used throughout the FULL DOCUMENT (including problem statement, reasoning chains, and solution), not restricted to only the problem statement variables

CRITICAL VALIDATION FOR "Number of Chains":
- Count all reasoning chains in the document with format **[CHAIN_01]**, **[CHAIN_02]**, etc.
- The stated number must exactly match the actual count of CHAIN_XX sections in the document
- Do NOT count THOUGHT_XX_YY items - only count CHAIN_XX items
- Format must be: **Number of Chains:** - [number] (number can optionally be wrapped in LaTeX delimiters like $7$)
- Acceptable formats: "**Number of Chains:** - 10" or "**Number of Chains:** - $10$"
- Example: If document has CHAIN_01 through CHAIN_10, metadata must show "**Number of Chains:** - 10" or "**Number of Chains:** - $10$"

WHAT TO CHECK:
1. Metadata section exists with "# Metadata" header
2. All required fields are present (order does NOT matter - any order is acceptable)
3. Each field follows the exact format: **FieldName:** - value
4. GitHub field is present as either "**GitHub URL:**" or "**GitHub:**" (both acceptable)
5. GitHub URL is a valid GitHub repository URL starting with https://github.com/
6. Number of Approaches contains both count and valid time complexity progression
7. Number of Chains matches actual CHAIN_XX sections count
8. Subtopic is a properly formatted JSON array
9. Values are appropriate for the content
10. Variables in "Number of Approaches" complexity are consistent with the full document (not restricted to problem statement only)

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

TASK: Verify that time complexity in metadata covers ALL approaches and uses properly introduced variables from anywhere in the document.

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
5. **Variable-Based**: Time complexity should use variables that are properly introduced somewhere in the document (problem statement, reasoning chains, response section, etc.). Variables should not be completely unrelated, undefined, or incorrectly used without any context or introduction in the document.
6. **Correctness**: Each stated time complexity must be mathematically correct for its corresponding approach
7. **Complex Expressions**: Support complex mathematical expressions with multiple terms (e.g., "O(n²+qn²)", "O(n*m + k*log(n))")

**ACCEPTABLE VARIABLE USAGE:**
- Variables from problem statement (N, M, K, Q, etc.)
- Variables introduced in reasoning chains or thoughts (T for time steps, S for sum, etc.)
- Variables defined in the response or approach explanation sections
- Standard algorithm notation variables (n for input size, m for edges, etc.)

**UNACCEPTABLE VARIABLE USAGE:**
- Completely undefined variables with no introduction anywhere in the document
- Variables that contradict the problem or solution context
- Random symbols used without any explanation or definition

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
- Metadata section → Number of Approaches field: Uses variable "X" in "O(n*X)" but variable "X" is never introduced, defined, or explained anywhere in the entire document (problem statement, chains, thoughts, or response sections)
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
5. For each variable used in the complexity notation, verify it is introduced SOMEWHERE in the document (problem statement, chains, thoughts, response, or approach discussions) - only flag variables that are completely undefined and unintroduced throughout the entire document
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
You are an expert competitive programming problem validator specializing in detecting solution leakage.

CRITICAL SCOPE: This check ONLY applies to the **[Prompt]** section (problem statement). Other sections like **[Assistant]**, CHAIN_XX, THOUGHT_XX_YY, or solution sections can freely discuss algorithms and are NOT evaluated here.

═══════════════════════════════════════════════════════════════════
MISSION: Detect if the problem statement reveals the optimal algorithm
═══════════════════════════════════════════════════════════════════

A problem statement should be SOLVABLE by a contestant WITHOUT reading the solution. Test case explanations must be based PURELY on problem requirements, not algorithmic insights.

🚫 UNACCEPTABLE - SOLUTION LEAKAGE (Flag these as FAIL):

**1. Naming specific data structures or algorithms:**
   ❌ "Use a segment tree to find the k-th smallest"
   ❌ "Binary search can solve this efficiently"
   ❌ "A BFS/DFS traversal shows..."
   ❌ "Hash map allows O(1) lookup"
   ❌ "Dynamic programming state..."
   ❌ "Apply union-find to merge..."
   ❌ "Prefix sum array helps..."
   ❌ "Using a priority queue/heap..."
   ❌ "Trie data structure for..."
   ❌ "Persistent segment tree maintains..."

**2. Revealing algorithmic approaches:**
   ❌ "Sort the array first, then..."
   ❌ "Precompute all values using..."
   ❌ "Iterate from left to right while maintaining..."
   ❌ "Use two pointers technique..."
   ❌ "Greedy approach: always choose..."
   ❌ "Memoize intermediate results..."
   ❌ "Build a graph and find shortest path..."

**3. Explaining HOW to solve (process/methodology):**
   ❌ "First sort by value, then by index"
   ❌ "Maintain a running sum as you iterate"
   ❌ "Keep track of the maximum seen so far"
   ❌ "Process queries offline by sorting them"
   ❌ "Build the structure incrementally"
   ❌ "Use preprocessing to speed up queries"

**4. Mentioning time/space complexity or optimization:**
   ❌ "This can be done in O(n log n) time"
   ❌ "An O(1) lookup is needed per query"
   ❌ "Efficient implementation requires..."
   ❌ "To optimize, we can..."

**5. Describing solution flow in test case explanations:**
   ❌ "After sorting the sigils, we find..." (reveals sorting step)
   ❌ "Using binary search on the path..." (reveals binary search)
   ❌ "By maintaining a frequency map..." (reveals data structure)
   ❌ "The LCA of nodes x and y is..." (reveals LCA usage when not in problem)
   ❌ "After preprocessing the tree..." (reveals preprocessing)

✅ ACCEPTABLE - PROBLEM-BASED EXPLANATIONS (These are OK):

**1. Stating problem facts and requirements:**
   ✅ "The path from waypoint 2 to 3 is: 2 → filament 1 → 1 → filament 3 → 3"
   ✅ "The sigils on this path are: {1, 5, 4, 6, 2}"
   ✅ "We need to find the 3rd smallest sigil"
   ✅ "The 3rd smallest value in {1, 5, 4, 6, 2} is 4"
   ✅ "Therefore, the answer is 4"

**2. Mathematical/logical deductions from problem rules:**
   ✅ "According to the problem rules, each waypoint gets a sigil"
   ✅ "Since k=3, we need the 3rd smallest"
   ✅ "The constraints guarantee k ≤ path length"
   ✅ "Values are assigned uniquely as specified"

**3. Tracing through problem-defined operations:**
   ✅ "Following the path definition in the problem..."
   ✅ "Applying the sigil assignment rule..."
   ✅ "Based on the connectivity given in input..."
   ✅ "According to the waypoint ordering..."

**4. Showing intermediate states WITHOUT revealing HOW they were computed:**
   ✅ "The sigils collected are {1, 5, 4, 6, 2}" (just states the fact)
   ✅ "Among these values, sorted order is: 1, 2, 4, 5, 6" (sorting IS the problem requirement for k-th smallest)
   ✅ "The path consists of 5 nodes" (counting is obvious)

═══════════════════════════════════════════════════════════════════
KEY PRINCIPLE: "Could a contestant understand this explanation 
                WITHOUT knowing the optimal algorithm?"
═══════════════════════════════════════════════════════════════════

**THE GOLDEN RULE FOR TEST CASE EXPLANATIONS:**
- Explain WHAT happens (trace the problem rules)
- DON'T explain HOW to compute it efficiently (algorithm/data structure)

**Examples of the difference:**

BAD (reveals solution):
❌ "We use LCA to find the path, then query our persistent segment tree for the k-th smallest sigil."
→ Problem: Reveals specific data structures (LCA, persistent segment tree)

GOOD (problem-based):
✅ "The path from x to y passes through these nodes: [...]. The sigils on these nodes are: {...}. The 3rd smallest is 4."
→ Good: Just traces problem rules, doesn't reveal algorithm

BAD (reveals solution):
❌ "By preprocessing with DFS and storing depths, we can efficiently find..."
→ Problem: Reveals algorithmic technique

GOOD (problem-based):
✅ "Following the tree structure in the input, node x and y are connected through: [path]. This gives us the sigils: {...}"
→ Good: References input/problem structure, not algorithm

═══════════════════════════════════════════════════════════════════
VALIDATION CHECKLIST:
═══════════════════════════════════════════════════════════════════

For EACH explanation/note in the **[Prompt]** section, verify:

□ Does it mention ANY specific data structure? (segment tree, hash map, heap, etc.)
□ Does it mention ANY algorithmic technique? (binary search, DP, greedy, two pointers, etc.)
□ Does it describe HOW to compute something efficiently?
□ Does it mention time/space complexity?
□ Does it reveal preprocessing or optimization strategies?
□ Could someone solve the problem just from reading this explanation?

If you answer YES to any of these → FLAG AS FAIL

═══════════════════════════════════════════════════════════════════
IMPORTANT REMINDERS:
═══════════════════════════════════════════════════════════════════

1. **Sorting is OK ONLY when it's the explicit problem requirement** (like "find k-th smallest")
2. **Counting/listing is OK** (these are basic operations anyone would do)
3. **Following paths/connections is OK** (this is reading the input)
4. **Only check [Prompt] section** - ignore all solution/chain/thought sections
5. **Be specific in your report**: Quote the exact problematic phrases and explain WHY they leak the solution

RESPONSE FORMAT:
Provide detailed analysis with specific quotes, then end with:
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
You are an expert document reviewer. Check if reasoning chains (sections marked as CHAIN_XX and THOUGHT_XX_YY) contain actual code snippets or code blocks.

WHAT TO CHECK:
- Look for code blocks marked with ``` or code formatting
- Look for multi-line code snippets with programming syntax
- Look for function definitions, loops, conditionals written as actual code
- Check CHAIN_XX and THOUGHT_XX_YY sections specifically

WHAT IS ALLOWED (NOT considered code):
- Pseudocode or algorithm descriptions in plain English
- Mathematical formulas and expressions
- Single-line code references in explanatory text (e.g., "we use a variable 'count'")
- Algorithm steps described in natural language
- Variable names or function names mentioned in discussion

WHAT IS NOT ALLOWED (considered code):
- Multi-line code blocks with actual syntax (e.g., Python, C++, Java code)
- Complete function implementations
- Code snippets showing actual programming constructs (if/else, for/while loops written in code)
- Code blocks formatted with ``` markers

PASS if: No actual code blocks or code snippets found in reasoning chains
FAIL if: Any code blocks or code snippets found in CHAIN_XX or THOUGHT_XX_YY sections

RESPONSE FORMAT:
Provide detailed analysis with specific examples if violations are found, then end with:
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


