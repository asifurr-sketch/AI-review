# Document Review System - Comprehensive Analysis

A comprehensive automated document review system using **Anthropic Claude Opus 4.1** with extended thinking capabilities to perform thorough quality analysis across 41 individual review points.

## 🎯 What This Does

This system analyzes documents (particularly coding problem statements and solutions) and provides detailed feedback on:
- **Code Quality** (style, naming, documentation)
- **Content Accuracy** (mathematical correctness, constraint consistency)
- **Problem Structure** (metadata, test cases, explanations)
- **Reasoning Quality** (logic chains, approach justification)
- **Language & Taxonomy** (spelling, subtopic validation)
- **GitHub Integration** (repository validation, file consistency)

## �️ Installation

### Prerequisites
- Python 3.7+
- Anthropic API key

### Quick Install
1. **Clone or download** the script:
   ```bash
   # Option 1: Clone the repository
   git clone https://github.com/asifurr-sketch/AI-review.git
   cd AI-review
   
   # Option 2: Download just the script
   wget https://raw.githubusercontent.com/asifurr-sketch/AI-review/main/document_reviewer.py
   ```

2. **Install dependencies**:
   ```bash
   pip install anthropic
   ```

3. **Set up API key**:
   ```bash
   # Copy example file and edit with your API key
   cp .env.example .env
   # Edit .env file: ANTHROPIC_API_KEY=your-api-key-here
   ```

4. **Test installation**:
   ```bash
   python3 document_reviewer.py --help
   ```

## 🚀 Quick Start

### Basic Usage
**Run your first review**:
```bash
# Complete analysis (recommended for first run)
python3 document_reviewer.py my_document.txt

# Fast AI-only analysis (skips GitHub validation)  
python3 document_reviewer.py my_document.txt --ai-only

# Only GitHub validation
python3 document_reviewer.py my_document.txt --github-only

# Resume from specific point 
python3 document_reviewer.py my_document.txt --resume 16

# Check specific issue
python3 document_reviewer.py my_document.txt --single-review "Style Guide Compliance"
```

### Optional: GitHub Integration Setup
For GitHub repository validation:
- **Public repos**: Works automatically with HTTPS
- **Private repos**: SSH access should be set up with GitHub
- **Note**: No GitHub API key needed - uses SSH/HTTPS for git operations

### Common Issues
- **"ANTHROPIC_API_KEY not found"**: Add your API key to `.env` file
- **"Git clone failed"**: Use `--ai-only` flag to skip GitHub validation
- **"Permission denied"**: Run `chmod +x document_reviewer.py`

## 📁 File Structure

```
AI Review/
├── document_reviewer.py          # Main review script
├── .env.example                  # Example environment variables file
├── document1.txt        # Sample document
├── document2.txt        # Sample document  
├── reports/                      # Generated reports folder
│   ├── document1_report.txt
│   └── document2_report.txt
└── README.md                     # This file
```

## 📊 Review Points Summary

**Total: 41 review points** (33 AI + 8 GitHub validation tasks)

### **🔧 GitHub Integration (8 tasks)**
- GitHub URL Extraction
- GitHub URL Parsing  
- Repository Cloning
- Overall.md File Detection
- Hunyuan CPP Files Check
- Overall.md Format Validation
- Solution.md Content Consistency
- Problem Statement.md Content Consistency

### **🎯 Solution Validation (2 points)**
1. **Unique Solution Validation** - Checks if problem has unique valid solution for automated testing
2. **Time Complexity Authenticity Check** - Verifies time complexity in metadata covers all discussed approaches

### **💻 Code Quality (3 points)**
3. **Style Guide Compliance** - Ensures code follows language-specific style guides (C++/Python)
4. **Naming Conventions** - Validates variable, function, and class naming conventions
5. **Documentation Standards** - Checks for proper docstrings and code documentation

### **📝 Response Quality (8 points)**
6. **Response Relevance to Problem** - Verifies response content is relevant to problem description
7. **Mathematical Equations Correctness** - Validates mathematical formulas and equations
8. **Problem Constraints Consistency** - Ensures defined constraints match problem description
9. **Missing Approaches in Steps** - Checks if all approaches/data structures are explained
10. **Code Elements Existence** - Verifies mentioned variables/functions exist in code
11. **Example Walkthrough with Optimal Algorithm** - Validates example demonstrations
12. **Time and Space Complexity Correctness** - Checks accuracy of complexity analysis
13. **Conclusion Quality** - Evaluates quality and completeness of conclusions

### **📋 Problem Structure (6 points)**
14. **Problem Statement Consistency** - Checks internal consistency of problem statement
15. **Solution Passability According to Limits** - Validates solution works within given constraints
16. **Metadata Correctness** - Verifies metadata format and content accuracy
17. **Test Case Validation** - Validates test cases against code and problem statement
18. **Sample Test Case Dry Run Validation** - Checks dry runs match given examples exactly
19. **Note Section Explanation Approach** - Reviews note section explanations

### **🧠 Reasoning Quality (3 points)**
20. **Inefficient Approaches Limitations** - Checks if inefficient approaches mention limitations
21. **Final Approach Discussion** - Reviews completeness of final approach discussion
22. **No Code in Reasoning Chains** - Ensures reasoning chains don't contain code implementations

### **🏷️ Language & Analysis (11 points)**
23. **Subtopic Taxonomy Validation** - Validates subtopics are from approved taxonomy
24. **Time Limit Validation** - Ensures time limit is specified in document
25. **Memory Limit Validation** - Validates memory limit is at least 32 MB
26. **Typo and Spelling Check** - Checks for spelling and grammar errors
27. **Subtopic Relevance** - Ensures selected subtopics are relevant to content
28. **Missing Relevant Subtopics** - Identifies important missing subtopics
29. **No Predictive Headings in Thoughts** - Checks for prohibited predictive headings
30. **Chain Test Case Analysis Validation** - Validates Chain 2 performs actual test case analysis
31. **Thought Heading Violations Check** - Checks for prohibited headings in thoughts
32. **Mathematical Variables and Expressions Formatting** - Validates math formatting
33. **Comprehensive Reasoning Thoughts Review** - Complete review of reasoning thought chains

## 📋 Understanding Reports

### Report Structure
Each generated report contains:

1. **Complete Execution Log** - All review progress with timestamps
2. **Final Summary** - Pass/fail status for each point
3. **Detailed Issues** - Specific problems found with suggested fixes

### Reading Results
- ✅ **PASS** - Review point passed successfully
- ❌ **FAIL** - Issues found, check detailed explanation
- ⏭️ **SKIPPED** - Point was skipped (when using --resume)

### Sample Output
```
📊 SUMMARY: 28/34 reviews passed
⚠️  6 review(s) failed

📝 4. STYLE GUIDE COMPLIANCE
Status: ❌ FAIL
Issues Found:
• Variable `p` should be `nodeIndex` for clarity
• Fix: Change `int p` to `int nodeIndex`
```
