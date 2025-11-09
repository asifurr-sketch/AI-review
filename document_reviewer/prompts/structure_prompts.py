"""
Review prompts for document validation
"""


class Prompts:
    """Container for review prompts"""
    
    @staticmethod
    def get_math_equations_prompt():
        """Check if LaTeX equations are syntactically correct and acceptable"""
        return r"""
You are an expert LaTeX and mathematical notation reviewer.

TASK: Check if the LaTeX equations and mathematical notation throughout the document are syntactically correct and properly formatted.

IMPORTANT: This review should ONLY check LaTeX syntax and notation formatting, NOT the mathematical correctness or logical validity of the content.

CRITICAL LOCATION REPORTING REQUIREMENTS:
1. NEVER use generic placeholders like "CHAIN_XX" or "THOUGHT_XX_YY"  
2. ALWAYS identify EXACT locations using specific identifiers from the document
3. Use format: "CHAIN_01", "CHAIN_05", "THOUGHT_03_02", "Metadata section", etc.
4. If you find violations in CHAIN_03, write "CHAIN_03", NOT "CHAIN_XX"
5. If you find violations in THOUGHT_04_02, write "THOUGHT_04_02", NOT "THOUGHT_XX_YY"

WHAT TO EXAMINE (LaTeX/Notation Syntax ONLY):
- LaTeX syntax correctness (proper delimiters, command syntax)
- Mathematical notation formatting (symbols, operators)
- Consistency in notation style throughout the document
- Proper use of LaTeX commands and environments
- Readability and clarity of mathematical expressions

DO NOT CHECK:
- Mathematical logic or correctness of the content
- Validity of mathematical proofs or derivations
- Accuracy of complexity analysis or mathematical statements
- Whether mathematical claims are true or false
- Correctness of numerical calculations

ACCEPTABLE LaTeX/Notation:
- ✅ Well-formed LaTeX: $O(n^2)$, $\sum_{i=1}^{n}$, $O(m \cdot d^2 + m^2 \cdot d)$
- ✅ Consistent notation: Using either $O(n·m)$ or $O(nm)$ consistently
- ✅ Proper LaTeX commands: $\log$, $\sqrt{n}$, $\frac{a}{b}$
- ✅ Clear formatting: $k = m - \text{rank}$, $k \leq \min(m, d)$

UNACCEPTABLE LaTeX/Notation (Syntax errors only):
- ❌ Malformed LaTeX: $O(n^2$ (missing closing delimiter)
- ❌ Invalid commands: $\unknown{n}$ (undefined command)
- ❌ Inconsistent mixing: Using both $O(n \cdot m)$ and O(nm) without $ delimiters
- ❌ Broken syntax: $\sum_i=1^n$ (incorrect subscript/superscript)

VIOLATION REPORTING FORMAT:
For each LaTeX/notation syntax error found, specify:
- EXACT location (specific chain, thought, or section identifier)
- Quote the problematic LaTeX/notation
- Explain what syntax/formatting issue exists
- Provide the correct syntax if applicable

EXAMPLE GOOD REPORTING (Syntax issues):
- CHAIN_03: LaTeX delimiter mismatch "$O(n log n" missing closing $
- THOUGHT_02_01: Inconsistent notation - uses both $O(n \cdot m)$ and O(nm) without delimiters
- Response section: Invalid LaTeX command "\unknown" not recognized

EXAMPLE OF WHAT NOT TO REPORT (These are content issues, not syntax issues):
- ❌ DO NOT report: "k ≤ d bound is incorrect because k can be larger than d" (This is mathematical logic, not syntax)
- ❌ DO NOT report: "Time complexity should be O(m^3) not O(m^2)" (This is correctness, not syntax)
- ❌ DO NOT report: "The proof is wrong because..." (This is logical validity, not syntax)

Examine the entire document systematically and report ONLY LaTeX/notation syntax violations with exact locations.

RESPONSE FORMAT:
Provide detailed analysis with specific locations, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""
    
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

    @staticmethod
    def get_predictive_headings_prompt():
        """Check for predictive headings in thoughts"""
        return """
You are an expert response evaluator. Check if there are predictive headings specifically in THOUGHTS (THOUGHT_XX_YY format) that break natural thinking flow by revealing solutions prematurely.

IMPORTANT DISTINCTION:
- ✅ CHAIN_XX: Predictive headings are ALLOWED (e.g., "CHAIN_03: Implementing brute force approach")
- ❌ THOUGHT_XX_YY: Overly predictive headings that break natural thinking flow are NOT ALLOWED

NATURAL THINKING FLOW GUIDELINES:
ACCEPTABLE thought headings (somewhat predictive is OK if it doesn't break flow):
- ✅ "THOUGHT_01_01: List of things we need to check"
- ✅ "THOUGHT_02_03: Understanding the problem constraints" 
- ✅ "THOUGHT_03_02: Analyzing time complexity requirements"
- ✅ "THOUGHT_04_01: Considering different data structures"
- ✅ "THOUGHT_05_02: Evaluating the brute force approach"
- ✅ "THOUGHT_06_01: Looking for optimization opportunities"

UNACCEPTABLE thought headings (break natural thinking flow):
- ❌ "THOUGHT_03_02: The efficient way is to use hash tables" (reveals specific solution)
- ❌ "THOUGHT_04_01: Using dynamic programming will solve this" (jumps to conclusion)
- ❌ "THOUGHT_05_02: Binary search is the optimal approach" (reveals final answer)
- ❌ "THOUGHT_06_01: The answer is O(n log n)" (gives away result)

WHAT TO CHECK:
- Only examine THOUGHT_XX_YY headings for flow-breaking predictive content
- Ignore CHAIN_XX headings - they can be fully predictive
- Allow somewhat predictive thought headings that maintain natural thinking progression
- Flag only thoughts that reveal specific solutions, final approaches, or definitive conclusions before proper analysis
- Consider whether the heading allows for natural exploration or forces a predetermined path

Please answer pass or fail.

RESPONSE FORMAT:
Provide detailed analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

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

