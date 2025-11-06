"""
Review prompts for document validation
"""


class Prompts:
    """Container for review prompts"""
    
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

    @staticmethod
    def get_documentation_prompt():
        """Check appropriate documentation style"""
        return """
You are a practical code reviewer focused on reasonable documentation standards.

**STEP 1: LANGUAGE DETECTION**
First, carefully analyze the document to determine the programming language by:
1. Looking for code blocks in the response section (not reasoning chains)
2. Examining syntax patterns, keywords, and structure
3. Identifying language-specific elements like:
   - C++: #include, std::, namespace, class/struct with public/private, semicolons, curly braces, template<>, vector<int>, iostream, using namespace std
   - Python: def, class without access modifiers, indentation-based blocks, import statements, snake_case, if __name__ == "__main__"
4. State your conclusion: "DETECTED LANGUAGE: [C++ or Python]"

**STEP 2: DOCUMENTATION ANALYSIS**
Check if the provided code uses reasonable documentation for important functions, classes, and public APIs.

**IMPORTANT EXCEPTIONS (DO NOT require documentation for these):**
- The `main` function (both C++ and Python) - it's self-explanatory
- Simple getters/setters
- Obvious utility functions with clear names
- Private helper functions that are trivial

**C++ Documentation Guidelines (be reasonable):**
- Complex functions, classes, and public APIs should have doxygen-style comments
- Simple functions with obvious purposes don't need verbose documentation
- Focus on non-obvious behavior, edge cases, and complex logic

**Python Documentation Guidelines (be reasonable):**
- Classes and non-trivial functions should have docstrings
- Type hints are nice to have but not required everywhere
- Simple, self-explanatory functions don't need lengthy docstrings
- Focus on documenting complex logic, algorithms, and non-obvious behavior
- Example of good documentation:
```python
def complex_function(parameter: type) -> return_type:
    '''Brief description of what it does and why.'''
```

**REVIEW PHILOSOPHY:**
- Be practical, not pedantic
- Focus on meaningful documentation, not bureaucratic overhead
- If the code is clear and self-documenting, that's often good enough
- Only flag missing documentation when it would genuinely help understand the code

CRITICAL VIOLATION REPORTING:
- Only report significant documentation issues
- Focus on complex functions/classes that really need explanation
- Identify which important functions/classes lack helpful documentation

Please answer pass or fail based on REASONABLE standards.

RESPONSE FORMAT:
Provide practical analysis, then end with:
FINAL VERDICT: PASS or FINAL VERDICT: FAIL
"""

