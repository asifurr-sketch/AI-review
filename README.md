# Document Review System - Comprehensive Analysis

A comprehensive automated document review system using **Anthropic Claude Opus 4.1** with extended thinking capabilities to perform thorough quality analysis across 29+ individual review points.

## 🎯 What This Does

This system analyzes documents (particularly coding problem statements and solutions) and provides detailed feedback on:
- **Code Quality** (style, naming, documentation)
- **Content Accuracy** (mathematical correctness, constraint consistency)
- **Problem Structure** (metadata, test cases, explanations)
- **Reasoning Quality** (logic chains, approach justification)
- **Language & Taxonomy** (spelling, subtopic validation)
- **GitHub Integration** (repository validation, file consistency)

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Anthropic API key
- SSH key setup for GitHub (recommended)

### Setup
1. **Set your API key:**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   # Or add to your .bashrc for persistence
   echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
   source ~/.bashrc
   ```

2. **Optional: Setup SSH for GitHub (recommended):**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ssh-add ~/.ssh/id_ed25519
   # Add public key to GitHub: cat ~/.ssh/id_ed25519.pub
   ```

### Usage
```bash
# Run complete analysis (GitHub + AI reviews)
python3 document_reviewer.py your_document.txt

# Run only AI reviews (skip GitHub validation)
python3 document_reviewer.py your_document.txt --ai-only

# Run only GitHub validation
python3 document_reviewer.py your_document.txt --github-only

# Resume from a specific point (if previous run was interrupted)
python3 document_reviewer.py your_document.txt --resume 15

# Run a single specific review
python3 document_reviewer.py your_document.txt --single-review "Style Guide Compliance"
```

## 📁 File Structure

```
AI Review/
├── document_reviewer.py          # Main review script
├── clockmakers_chorus.txt        # Sample document
├── clockwork_nautilus.txt        # Sample document  
├── reports/                      # Generated reports folder
│   ├── clockmakers_chorus_report.txt
│   └── your_document_report.txt
└── README.md                     # This file
```

## 📊 Comprehensive Review Points

### **🔧 GitHub Integration**
1. **GitHub Requirements Validation** - Validates GitHub URL in metadata, repository accessibility, and overall.md file existence

### **🎯 Solution Validation**  
2. **Unique Solution Validation** - Checks if problem has unique valid solution for automated testing
3. **Time Complexity Authenticity Check** - Verifies time complexity in metadata covers all discussed approaches

### **💻 Code Quality (Points 4-6)**
4. **Style Guide Compliance** - Ensures code follows language-specific style guides (C++/Python)
5. **Naming Conventions** - Validates variable, function, and class naming conventions
6. **Documentation Standards** - Checks for proper docstrings and code documentation

### **📝 Response Quality (Points 7-14)**
7. **Response Relevance to Problem** - Verifies response content is relevant to problem description
8. **Mathematical Equations Correctness** - Validates mathematical formulas and equations
9. **Problem Constraints Consistency** - Ensures defined constraints match problem description
10. **Missing Approaches in Steps** - Checks if all approaches/data structures are explained
11. **Code Elements Existence** - Verifies mentioned variables/functions exist in code
12. **Example Walkthrough with Optimal Algorithm** - Validates example demonstrations
13. **Time and Space Complexity Correctness** - Checks accuracy of complexity analysis
14. **Conclusion Quality** - Evaluates quality and completeness of conclusions

### **📋 Problem Structure (Points 15-21)**
15. **Problem Statement Consistency** - Checks internal consistency of problem statement
16. **Solution Passability According to Limits** - Validates solution works within given constraints
17. **Metadata Correctness** - Verifies metadata format and content accuracy
18. **Test Case Validation** - Validates test cases against code and problem statement
19. **Sample Test Case Dry Run Validation** - Checks dry runs match given examples exactly
20. **Note Section Explanation Approach** - Reviews note section explanations
21. **Time Limit Validation** - Ensures time limit is specified in document
22. **Memory Limit Validation** - Validates memory limit is at least 32 MB

### **🧠 Reasoning Quality (Points 23-25)**
23. **Inefficient Approaches Limitations** - Checks if inefficient approaches mention limitations
24. **Final Approach Discussion** - Reviews completeness of final approach discussion
25. **No Code in Reasoning Chains** - Ensures reasoning chains don't contain code implementations

### **🏷️ Language & Taxonomy (Points 26-29)**
26. **Subtopic Taxonomy Validation** - Validates subtopics are from approved taxonomy
27. **Typo and Spelling Check** - Checks for spelling and grammar errors
28. **Subtopic Relevance** - Ensures selected subtopics are relevant to content
29. **Missing Relevant Subtopics** - Identifies important missing subtopics
30. **No Predictive Headings in Thoughts** - Checks for prohibited predictive headings
31. **Chain Test Case Analysis Validation** - Validates Chain 2 performs actual test case analysis
32. **Thought Heading Violations Check** - Checks for prohibited headings in thoughts
33. **Mathematical Variables and Expressions Formatting** - Validates math formatting
34. **Comprehensive Reasoning Thoughts Review** - Complete review of reasoning thought chains

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

## 🔧 Advanced Usage

### Command Line Options
```bash
# Run all reviews (GitHub + AI)
python3 document_reviewer.py document.txt

# Run only AI reviews (skip GitHub validation)  
python3 document_reviewer.py document.txt --ai-only

# Run only GitHub validation (skip AI reviews)
python3 document_reviewer.py document.txt --github-only

# Run a single specific review
python3 document_reviewer.py document.txt --single-review "Metadata Correctness"

# Resume from a specific AI review point
python3 document_reviewer.py document.txt --resume 16
```

### Resume Functionality
If a review is interrupted, resume from any point:
```bash
# Resume from point 16
python3 document_reviewer.py document.txt --resume 16
```

### GitHub Integration
The system validates:
- GitHub URL format in document metadata
- Repository accessibility via SSH (with HTTPS fallback)
- Existence of exactly one `overall.md` file
- Content consistency between document and repository files

### Understanding Document Structure
The system expects documents with this structure:
```
# Metadata
**Category:** - Coding
**Topic:** - Competitive Programming  
**Subtopics:** - ["Arrays", "Dynamic Programming"]
**Difficulty:** - Medium
**Languages:** - C++, Python
**Number of Approaches:** - 3, (O(n²) → O(n log n) → O(n))
**Number of Chains:** - 5
**GitHub URL:** - https://github.com/owner/repo

**[User]**
*Demark the start of the User's activity*

**[Prompt]**
Your problem statement goes here...

**[Assistant]**
**[CHAIN_01]**
**[THOUGHT_01_01]**
Reasoning content...
```

## 🚨 Common Issues & Solutions

### Setup Issues
- **Missing API Key**: Set `ANTHROPIC_API_KEY` environment variable
- **SSH Clone Failed**: Set up SSH keys or use `--ai-only` to skip GitHub validation
- **Permission Denied**: Ensure script has execute permissions

### Document Format Issues
- **Metadata Missing**: Document must start with proper metadata section
- **Invalid JSON in Subtopics**: Use proper JSON array format: `["topic1", "topic2"]`
- **Missing Required Fields**: All metadata fields must be present

### Performance Tips
- Use `--ai-only` for faster reviews (skips GitHub validation)
- Use `--single-review` to test specific issues
- Use `--resume X` to continue interrupted reviews

## 📈 Model Information

- **Primary Model**: Claude Opus 4.1 with 20,000 token thinking budget
- **Secondary Model**: Claude Sonnet 4 for cleanup operations  
- **Max Tokens**: 32,000 (Opus) / 64,000 (Sonnet cleanup)
- **Features**: Extended thinking for deep analysis and step-by-step reasoning
