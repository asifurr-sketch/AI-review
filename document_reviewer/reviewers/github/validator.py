"""
GitHub repository validator for document review system
"""

import os
import re
import subprocess
import tempfile
import shutil
import json
from typing import Optional, Tuple, List, Dict
from urllib.parse import urlparse
from openai import OpenAI

from ...core.models import ReviewResponse, ReviewResult


class GitHubReviewValidator:
    """Non-AI review: Validates GitHub post links and overall.md file existence"""
    
    def __init__(self, quiet_mode=False):
        self.quiet_mode = quiet_mode
    
    def _extract_github_url(self, document: str) -> Optional[str]:
        """Extract GitHub URL from document metadata - robust extraction for any *github.com* pattern"""
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
        
        # Robust fallback: Find any URL containing github.com and take the longest one
        github_urls = []
        
        # Pattern to match any URL containing github.com (case insensitive)
        robust_pattern = r'https?://[^\s\n]*github\.com[^\s\n]*'
        matches = re.finditer(robust_pattern, document, re.IGNORECASE)
        
        for match in matches:
            github_urls.append(match.group(0))
        
        # If multiple URLs found, return the longest one
        if github_urls:
            return max(github_urls, key=len)
        
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
    
    def _ensure_utilities_repo(self) -> Tuple[bool, str, str]:
        """
        Check if the utilities repository exists in the root of AI Review repo.
        Returns: (success, utilities_path, message)
        """
        # Get the root directory of the AI Review repository
        current_file = os.path.abspath(__file__)
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
        utilities_path = os.path.join(repo_root, 'utilities')
        
        # Check if utilities directory exists
        if os.path.exists(utilities_path) and os.path.isdir(utilities_path):
            # Check if create_full_delivery.py exists
            script_path = os.path.join(utilities_path, 'create_full_delivery.py')
            if os.path.exists(script_path):
                return True, utilities_path, "Utilities repository found"
            else:
                return False, utilities_path, "Utilities folder exists but create_full_delivery.py not found"
        else:
            return False, utilities_path, "Utilities folder not found. Please clone https://github.com/NOI-gen/utilities to the repository root."
    
    def _find_overall_md_files(self, repo_dir: str) -> List[str]:
        """Find all overall.md files in the repository (case-insensitive)"""
        overall_files = []
        
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                if file.lower() == 'overall.md':
                    overall_files.append(os.path.join(root, file))
        
        return overall_files
    
    def _check_hunyuan_cpp_files(self, repo_dir: str) -> Tuple[bool, str]:
        """Check if runs/hunyuan-2.0-thinking-dev-20251012/*.cpp or *.py files exist"""
        hunyuan_dir = os.path.join(repo_dir, 'runs', 'hunyuan-2.0-thinking-dev-20251012')
        
        if not os.path.exists(hunyuan_dir):
            return False, f"Directory 'runs/hunyuan-2.0-thinking-dev-20251012' does not exist"
        
        cpp_files = []
        py_files = []
        for file in os.listdir(hunyuan_dir):
            if file.endswith('.cpp'):
                cpp_files.append(file)
            elif file.endswith('.py'):
                py_files.append(file)
        
        all_files = cpp_files + py_files
        if not all_files:
            return False, f"No .cpp or .py files found in 'runs/hunyuan-2.0-thinking-dev-20251012' directory"
        
        file_summary = []
        if cpp_files:
            file_summary.append(f"{len(cpp_files)} .cpp files: {', '.join(cpp_files)}")
        if py_files:
            file_summary.append(f"{len(py_files)} .py files: {', '.join(py_files)}")
        
        return True, f"Found {'; '.join(file_summary)}"
    
    def _validate_overall_md_format(self, overall_md_path: str) -> Tuple[bool, str]:
        """Validate the format of overall.md file"""
        try:
            with open(overall_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "# Overall Test Report for",
                "**Error Code Legend:**",
                "## Detailed Model Performance",
                "### Model: `hunyuan-2.0-thinking-dev-20251012`",
                "## Overall Model Comparison"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                return False, f"Missing required sections: {', '.join(missing_sections)}"
            
            # Check for hunyuan model failure requirement
            if "hunyuan-2.0-thinking-dev-20251012" in content:
                # Look for failure indicators in hunyuan section
                hunyuan_section_start = content.find("### Model: `hunyuan-2.0-thinking-dev-20251012`")
                if hunyuan_section_start != -1:
                    # Find the next model section or end of content
                    next_model = content.find("### Model:", hunyuan_section_start + 1)
                    if next_model == -1:
                        hunyuan_section = content[hunyuan_section_start:]
                    else:
                        hunyuan_section = content[hunyuan_section_start:next_model]
                    
                    if "❌ FAIL" not in hunyuan_section and "✅ PASS" in hunyuan_section:
                        return False, "hunyuan-2.0-thinking-dev-20251012 model should show FAIL status (❌ FAIL), not PASS"
            
            # Check for standard model pass requirement (extension-agnostic)
            standard_model_match = re.search(r"^### Model: `standard[^`]*`", content, flags=re.MULTILINE)
            if not standard_model_match:
                return False, "Missing required standard model section: expected a header like ### Model: `standard` or `standard.<ext>`"
            else:
                standard_section_start = standard_model_match.start()
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
                    return False, "standard model section should show PASS status (✅ PASS)"
            
            # Check for solution_bf constraints if present (extension-agnostic)
            bf_model_match = re.search(r"^### Model: `solution_bf[^`]*`", content, flags=re.MULTILINE)
            if bf_model_match:
                bf_section_start = bf_model_match.start()
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
                            if re.search(r"\bsolution_bf(?:\.[A-Za-z0-9_]+)?\b", line):
                                # Split by | and filter out empty strings
                                parts = [p.strip() for p in line.split('|') if p.strip()]
                                # Table structure: Run File | Status | Score | Avg Time (s) | Max Time (s) | Avg Mem (MB) | Max Mem (MB) | Errors (WA/TLE/RTE/CE)
                                if len(parts) >= 8:  # Ensure we have enough columns
                                    errors_column = parts[7]  # Last column with errors (0-indexed, so 8th column)
                                    
                                    # Parse errors format: WA/TLE/RTE/CE
                                    if '/' in errors_column:
                                        error_counts = errors_column.split('/')
                                        if len(error_counts) >= 4:
                                            wa_count = error_counts[0].strip()
                                            ce_count = error_counts[3].strip()
                                            if wa_count != '0':
                                                return False, f"solution_bf should not have Wrong Answer (WA) errors. Found {wa_count} WA errors."
                                            if ce_count != '0':
                                                return False, f"solution_bf should not have Compilation Error (CE) errors. Found {ce_count} CE errors."
            
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
                    # Store the full diff line with prefix for proper formatting
                    violations.append(diff_line)
        
        if violations:
            # Show only the disallowed diffs in proper diff format
            violation_summary = '; '.join([f"'{line[1:]}'" for line in violations[:5]])  # Extract content for summary
            detailed_violations = '\n'.join([f"  {violation}" for violation in violations[:10]])  # Show up to 10 violations with +/- prefix
            return False, f"Content diff violations found: Disallowed diff: {violation_summary}\n\nDisallowed differences:\n{detailed_violations}"
        
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
    
    def _validate_solution_md_no_horizontal_lines(self, repo_dir: str) -> Tuple[bool, str]:
        """Validate that solution.md does not contain horizontal lines (---)"""
        solution_md_path = os.path.join(repo_dir, 'solution.md')
        
        if not os.path.exists(solution_md_path):
            return False, "solution.md file not found in repository"
        
        try:
            # Read solution.md
            with open(solution_md_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check for horizontal lines
            violations = []
            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()
                # Check if line is exactly "---" or just dashes
                if stripped_line == "---" or (stripped_line and all(c == '-' for c in stripped_line) and len(stripped_line) >= 3):
                    violations.append(f"Line {line_num}: '{line.rstrip()}'")
            
            if violations:
                violation_details = '\n  '.join(violations[:10])  # Show up to 10 violations
                total_count = len(violations)
                if total_count > 10:
                    return False, f"Found {total_count} horizontal line(s) in solution.md (showing first 10):\n  {violation_details}"
                else:
                    return False, f"Found {total_count} horizontal line(s) in solution.md:\n  {violation_details}"
            
            return True, "solution.md has no horizontal lines"
            
        except Exception as e:
            return False, f"Error validating solution.md for horizontal lines: {str(e)}"
    
    def _validate_limits_vs_usage(self, overall_md_path: str, document: str) -> Tuple[bool, str]:
        """Validate that memory limit is at least 1.5x the maximum usage in overall.md"""
        try:
            # Extract limits from document (problem statement section)
            prompt_section = self._extract_prompt_section(document)
            
            # Extract memory limit (in MB)
            memory_limit_match = re.search(r'Memory Limit:\s*\*\*(\d+(?:\.\d+)?)\s*MB\*\*', prompt_section, re.IGNORECASE)
            if not memory_limit_match:
                return False, "Could not extract memory limit from problem statement"
            memory_limit = float(memory_limit_match.group(1))
            
            # Read overall.md file
            with open(overall_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse all Max Mem values from the tables
            max_mems = []
            
            # Find all table rows with data
            lines = content.split('\n')
            for line in lines:
                # Skip header lines and separator lines
                if '|' not in line or line.strip().startswith('|---|') or 'Run File' in line or 'Model' in line:
                    continue
                
                # Parse table row
                parts = [p.strip() for p in line.split('|') if p.strip()]
                
                # Table structure: Run File | Status | Score | Avg Time (s) | Max Time (s) | Avg Mem (MB) | Max Mem (MB) | Errors
                if len(parts) >= 7:
                    try:
                        # Extract Max Mem (MB) - column index 6
                        max_mem_str = parts[6].strip()
                        if max_mem_str and max_mem_str != 'Max Mem (MB)':
                            max_mem = float(max_mem_str)
                            max_mems.append(max_mem)
                    except (ValueError, IndexError):
                        # Skip lines that can't be parsed
                        continue
            
            if not max_mems:
                return False, "Could not extract max memory values from overall.md tables"
            
            # Find the absolute maximum memory usage
            absolute_max_mem = max(max_mems)
            
            # Calculate required memory limit (1.5x the maximum usage)
            required_mem_limit = absolute_max_mem * 1.5
            
            # Check if memory limit is sufficient
            if memory_limit < required_mem_limit:
                return False, f"Memory limit ({memory_limit}MB) is less than 1.5x max usage ({absolute_max_mem:.2f}MB × 1.5 = {required_mem_limit:.2f}MB)"
            
            return True, f"Memory limit is sufficient ({memory_limit}MB ≥ {required_mem_limit:.2f}MB, max usage: {absolute_max_mem:.2f}MB)"
            
        except Exception as e:
            return False, f"Error validating limits vs usage: {str(e)}"
    
    def validate_github_requirements(self, document: str) -> ReviewResponse:
        """Main validation method for GitHub requirements"""
        # Step 1: Check for GitHub URL in document
        github_url = self._extract_github_url(document)
        if not github_url:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning="No GitHub URL found in document. Expected format: **GitHub URL:** https://github.com/owner/repo or any URL containing github.com"
            )
        
        # Step 2: Parse GitHub URL
        owner, repo = self._parse_github_url(github_url)
        if not owner or not repo:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Invalid GitHub URL format: {github_url}. URL must be a valid GitHub repository URL"
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
            
            # Step 9: Validate solution.md has no horizontal lines
            horizontal_valid, horizontal_msg = self._validate_solution_md_no_horizontal_lines(temp_dir)
            if not horizontal_valid:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"solution.md horizontal lines check failed: {horizontal_msg}"
                )
            
            # Step 10: Validate memory limit is at least 1.5x maximum usage
            limits_valid, limits_msg = self._validate_limits_vs_usage(overall_md_path, document)
            if not limits_valid:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Memory limit validation failed: {limits_msg}"
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
                         f"• problem_statement.md consistency: {problem_msg}\n" +
                         f"• solution.md horizontal lines: {horizontal_msg}\n" +
                         f"• memory limit vs usage: {limits_msg}"
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
    
    def _validate_utilities_delivery(self, repo_dir: str, document: str) -> Tuple[bool, str]:
        """
        Validate that create_full_delivery.py script runs successfully.
        Clones utilities repo if needed and runs the script.
        """
        # Step 1: Ensure utilities repository exists
        success, utilities_path, msg = self._ensure_utilities_repo()
        if not success:
            return False, f"Utilities repository setup failed: {msg}"
        
        # Step 2: Extract problem directory from repo_dir
        problem_dir = repo_dir
        
        # Step 3: Determine language by checking standard solution file extension
        language = None
        
        # Look for standard.* file in the repository
        if os.path.exists(repo_dir):
            for file in os.listdir(repo_dir):
                if file.startswith('standard.'):
                    ext = os.path.splitext(file)[1].lower()
                    if ext == '.cpp':
                        language = "C++"
                        break
                    elif ext == '.py':
                        language = "Python"
                        break
        
        # Fallback: try to detect from document if standard file not found
        if not language:
            if "python" in document.lower() or ".py" in document.lower():
                language = "Python"
            elif "c++" in document.lower() or ".cpp" in document.lower():
                language = "C++"
            else:
                # Default to C++ if cannot determine
                language = "C++"
        
        # Step 4: Run create_full_delivery.py script
        script_path = os.path.join(utilities_path, 'create_full_delivery.py')
        if not os.path.exists(script_path):
            return False, f"create_full_delivery.py script not found in utilities repository"
        
        try:
            if not self.quiet_mode:
                print(f"🧪 Running utilities validation: python {script_path} --problem-dir {problem_dir} --language {language}")
            
            result = subprocess.run([
                'python3', script_path,
                '--problem-dir', problem_dir,
                '--language', language
            ], capture_output=True, text=True, timeout=600, cwd=utilities_path)
            
            # Check for success indicators in output
            output = result.stdout + result.stderr
            
            # The script is successful if ALL these conditions are met:
            # 1. "All validations passed!" appears (optimal solution passes + model matches expectations)
            # 2. "All problems processed successfully!" appears
            # 3. "Full delivery package created successfully!" appears
            # 4. Return code is 0
            
            has_validations_passed = "All validations passed!" in output
            has_problems_processed = "All problems processed successfully!" in output
            has_delivery_created = "Full delivery package created successfully!" in output
            
            if result.returncode == 0 and has_validations_passed and has_problems_processed and has_delivery_created:
                # Return full output for successful runs too
                return True, f"Utilities delivery validation passed: Full delivery package created successfully for language {language}\n\n=== COMPLETE OUTPUT ===\n{output}"
            else:
                # Return complete output for failed runs - user wants to see everything
                return False, f"Utilities validation failed (return code {result.returncode})\n\n=== COMPLETE OUTPUT ===\n{output}"
        
        except subprocess.TimeoutExpired:
            return False, "Utilities validation timed out after 600 seconds"
        except Exception as e:
            return False, f"Error running utilities validation: {str(e)}"

    def validate_github_requirements_detailed(self, document: str) -> list:
        """Detailed validation method that returns separate results for each GitHub task"""
        results = []
        temp_dir = None
        
        try:
            # Task 1: GitHub Repository Setup (combined: URL extraction, parsing, cloning, overall.md detection)
            setup_steps = []
            
            # Step 1a: GitHub URL Extraction
            github_url = self._extract_github_url(document)
            if not github_url:
                results.append(("GitHub Repository Setup", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning="No GitHub URL found in document. Expected format: **GitHub URL:** https://github.com/owner/repo or any URL containing github.com"
                )))
                return results
            setup_steps.append(f"• GitHub URL found: {github_url}")
            
            # Step 1b: GitHub URL Parsing
            owner, repo = self._parse_github_url(github_url)
            if not owner or not repo:
                results.append(("GitHub Repository Setup", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Invalid GitHub URL format: {github_url}. URL must be a valid GitHub repository URL"
                )))
                return results
            setup_steps.append(f"• URL parsed: owner={owner}, repo={repo}")
            
            # Step 1c: Repository Cloning
            temp_dir = tempfile.mkdtemp(prefix="github_review_")
            clone_success = self._clone_repository(github_url, temp_dir)
            if not clone_success:
                results.append(("GitHub Repository Setup", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Failed to clone repository: {github_url}. Repository may not exist or be inaccessible."
                )))
                return results
            setup_steps.append(f"• Repository cloned successfully")
            
            # Step 1d: Overall.md File Detection
            overall_files = self._find_overall_md_files(temp_dir)
            if len(overall_files) == 0:
                results.append(("GitHub Repository Setup", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"No overall.md file found in repository {github_url}"
                )))
                overall_md_path = None
            elif len(overall_files) > 1:
                # Select the overall.md file with the largest alphabetical path
                overall_files.sort()
                selected_file = overall_files[-1]
                relative_paths = [os.path.relpath(f, temp_dir) for f in overall_files]
                selected_relative = os.path.relpath(selected_file, temp_dir)
                setup_steps.append(f"• Found multiple overall.md files, selected: {selected_relative}")
                overall_md_path = selected_file
            else:
                relative_path = os.path.relpath(overall_files[0], temp_dir)
                setup_steps.append(f"• Found overall.md at: {relative_path}")
                overall_md_path = overall_files[0]
            
            # Add successful setup result
            results.append(("GitHub Repository Setup", ReviewResponse(
                result=ReviewResult.PASS,
                reasoning=f"✅ PASS - Repository setup completed:\n" + "\n".join(setup_steps)
            )))
            
            # Task 2: Hunyuan CPP Files Check
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
            
            # Task 3: Overall.md Format Validation
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
            
            # Task 4: Solution.md Content Consistency
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
            
            # Task 5: Problem Statement.md Content Consistency
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
            
            # Task 6: Solution.md Horizontal Lines Check
            horizontal_valid, horizontal_msg = self._validate_solution_md_no_horizontal_lines(temp_dir)
            if not horizontal_valid:
                results.append(("Solution.md Horizontal Lines Check", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"solution.md horizontal lines check failed: {horizontal_msg}"
                )))
            else:
                results.append(("Solution.md Horizontal Lines Check", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - {horizontal_msg}"
                )))
            
            # Task 7: Memory Limit vs Maximum Usage Check
            if overall_md_path:
                limits_valid, limits_msg = self._validate_limits_vs_usage(overall_md_path, document)
                if not limits_valid:
                    results.append(("Memory Limit vs Maximum Usage Check", ReviewResponse(
                        result=ReviewResult.FAIL,
                        reasoning=f"Memory limit validation failed: {limits_msg}"
                    )))
                else:
                    results.append(("Memory Limit vs Maximum Usage Check", ReviewResponse(
                        result=ReviewResult.PASS,
                        reasoning=f"✅ PASS - {limits_msg}"
                    )))
            else:
                results.append(("Memory Limit vs Maximum Usage Check", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning="Cannot validate memory limit: overall.md file not found"
                )))
            
            # Task 8: Utilities Delivery Validation
            utilities_valid, utilities_msg = self._validate_utilities_delivery(temp_dir, document)
            if not utilities_valid:
                results.append(("Utilities Delivery Validation", ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Utilities delivery validation failed: {utilities_msg}"
                )))
            else:
                results.append(("Utilities Delivery Validation", ReviewResponse(
                    result=ReviewResult.PASS,
                    reasoning=f"✅ PASS - {utilities_msg}"
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

