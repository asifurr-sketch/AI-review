# Document Review System - 26-Point Analysis

A comprehensive automated document review system using **Anthropic Claude Opus 4.1** with extended thinking capabilities to perform thorough quality analysis across 26 individual review points.

## 🎯 What This Does

This system analyzes documents (particularly coding problem statements and solutions) and provides detailed feedback on:
- **Code Quality** (style, naming, documentation)
- **Content Accuracy** (mathematical correctness, constraint consistency)
- **Problem Structure** (metadata, test cases, explanations)
- **Reasoning Quality** (logic chains, approach justification)
- **Language & Taxonomy** (spelling, subtopic validation)

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Anthropic API key

### Setup
1. **Install dependencies:**
   ```bash
   pip install anthropic
   ```

2. **Set your API key:**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   # Or add to your .bashrc for persistence
   echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Usage
```bash
# Run complete 26-point analysis
python3 document_reviewer.py your_document.txt

# Resume from a specific point (if previous run was interrupted)
python3 document_reviewer.py your_document.txt --resume 15
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

## 📊 Review Points Overview

### **Code Quality (Points 1-3)**
- Style guide compliance (variable naming, coding standards)
- Naming conventions (camelCase, constants, functions)
- Doxygen documentation completeness

### **Content Accuracy (Points 4-11)**
- Response relevance to problem
- Mathematical equation correctness
- Problem constraint consistency
- Approach completeness
- Code element validation
- Example walkthroughs
- Time/space complexity accuracy
- Conclusion quality

### **Problem Structure (Points 12-17)**
- Problem statement consistency
- Solution performance validation
- Metadata accuracy
- Test case validation
- Sample dry run verification
- Note section approach

### **Reasoning Quality (Points 18-20)**
- Inefficient approach limitations
- Final approach discussion
- Code presence in reasoning chains

### **Language & Taxonomy (Points 21-26)**
- Subtopic taxonomy validation
- Spelling and grammar check
- Subtopic relevance
- Missing relevant subtopics
- Predictive heading validation
- Comprehensive reasoning analysis

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
📊 SUMMARY: 20/26 reviews passed
⚠️  6 review(s) failed

📝 1. STYLE GUIDE COMPLIANCE
Status: ❌ FAIL
Issues Found:
• Variable `p` should be `nodeIndex` for clarity
• Fix: Change `int p` to `int nodeIndex`
```

## 🔧 Advanced Usage

### Resume Functionality
If a review is interrupted, resume from any point:
```bash
# Resume from point 16
python3 document_reviewer.py document.txt --resume 16
```

### Understanding Document Structure
The system expects documents with this structure:
```
# Metadata
**Category:** - Coding
**Topic:** - Competitive Programming
**Subtopics:** - ["Arrays", "Dynamic Programming"]
...

**[User]**
*Demark the start of the User's activity*

**[Prompt]**
Your problem statement goes here...

**[Assistant]**
**[CHAIN_01]**
**[THOUGHT_01_01]**
Reasoning content...
```
