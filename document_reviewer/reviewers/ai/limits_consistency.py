"""
Limits Consistency Reviewer - validates time and space limits across all files
"""

import json
import re
from typing import Optional, Dict
from ...core.base_reviewer import BaseReviewer
from ...core.models import ReviewResponse, ReviewResult


class LimitsConsistencyReviewer(BaseReviewer):
    """Reviews if time and space limits are consistent across report, problem_statement.md, requirements.json, and metadata.json"""
    
    def review(self, document: str) -> ReviewResponse:
        """
        Main review method that orchestrates the entire limits consistency check
        """
        # Step 1: Extract limits from the report file (document parameter)
        report_limits = self._extract_limits_from_report(document)
        
        if not report_limits['time'] or not report_limits['space']:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Failed to extract time and/or space limits from report file.\nExtracted: Time={report_limits['time']}, Space={report_limits['space']}"
            )
        
        # Step 2: Extract problem_statement.md content from document
        problem_statement_content = self._extract_problem_statement_from_report(document)
        
        if not problem_statement_content:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning="Failed to extract problem statement content from report file. Could not find **[Prompt]** section."
            )
        
        # Step 3: Use GPT-5 to extract limits from problem_statement.md
        problem_limits = self._extract_limits_with_gpt(problem_statement_content, "problem_statement.md")
        
        if not problem_limits or not problem_limits.get('time') or not problem_limits.get('space'):
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Failed to extract time and/or space limits from problem_statement.md using GPT-5.\nExtracted: {problem_limits}"
            )
        
        # Step 4: Extract GitHub URL from report
        github_url = self._extract_github_url(document)
        
        if not github_url:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning="Failed to extract GitHub URL from report file."
            )
        
        # Step 5: Clone repository and get requirements.json and metadata.json
        import tempfile
        import shutil
        import subprocess
        import os
        
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="limits_check_")
            
            # Clone repository
            clone_success = self._clone_repository(github_url, temp_dir)
            if not clone_success:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Failed to clone repository: {github_url}"
                )
            
            # Read requirements.json
            requirements_path = os.path.join(temp_dir, 'requirements.json')
            if not os.path.exists(requirements_path):
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"requirements.json file not found in repository: {github_url}"
                )
            
            with open(requirements_path, 'r', encoding='utf-8') as f:
                requirements_data = json.load(f)
            
            # Read metadata.json
            metadata_path = os.path.join(temp_dir, 'metadata.json')
            if not os.path.exists(metadata_path):
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"metadata.json file not found in repository: {github_url}"
                )
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_data = json.load(f)
            
            # Extract time and space from JSON files
            requirements_time = requirements_data.get('time')
            requirements_space = requirements_data.get('space')
            metadata_time = metadata_data.get('time')
            metadata_space = metadata_data.get('space')
            
            # Step 6: Compare all limits
            all_limits = {
                'report': report_limits,
                'problem_statement.md': problem_limits,
                'requirements.json': {'time': requirements_time, 'space': requirements_space},
                'metadata.json': {'time': metadata_time, 'space': metadata_space}
            }
            
            # Check for consistency
            inconsistencies = []
            
            # Compare time limits
            time_values = {
                'report': report_limits['time'],
                'problem_statement.md': problem_limits['time'],
                'requirements.json': requirements_time,
                'metadata.json': metadata_time
            }
            
            unique_time_values = set(time_values.values())
            if len(unique_time_values) > 1:
                inconsistencies.append(f"Time limit mismatch: {time_values}")
            
            # Compare space limits
            space_values = {
                'report': report_limits['space'],
                'problem_statement.md': problem_limits['space'],
                'requirements.json': requirements_space,
                'metadata.json': metadata_space
            }
            
            unique_space_values = set(space_values.values())
            if len(unique_space_values) > 1:
                inconsistencies.append(f"Space limit mismatch: {space_values}")
            
            if inconsistencies:
                reasoning = "Limits consistency check FAILED:\n\n" + "\n".join([f"- {issue}" for issue in inconsistencies])
                reasoning += f"\n\nDetailed limits by file:\n"
                for file, limits in all_limits.items():
                    reasoning += f"  {file}: Time={limits['time']}, Space={limits['space']}\n"
                
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=reasoning
                )
            
            # All limits match
            return ReviewResponse(
                result=ReviewResult.PASS,
                reasoning=f"Final verdict: PASS - All time and space limits are consistent across all files (Time={report_limits['time']}, Space={report_limits['space']})"
            )
        
        except json.JSONDecodeError as e:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Failed to parse JSON file: {str(e)}"
            )
        except Exception as e:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Error during limits consistency check: {str(e)}"
            )
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
    
    def _extract_limits_from_report(self, document: str) -> dict:
        """Extract time and space limits from report file using regex"""
        time_limit = None
        space_limit = None
        
        # Pattern 1: "Time Limit: **X seconds**" or "Time Limit: **X second**"
        time_match = re.search(r'Time Limit:\s*\*\*(\d+(?:\.\d+)?)\s*seconds?\*\*', document, re.IGNORECASE)
        if time_match:
            time_limit = float(time_match.group(1))
            # Convert to int if it's a whole number
            if time_limit == int(time_limit):
                time_limit = int(time_limit)
        
        # Pattern 2: "Memory Limit: **X MB**"
        space_match = re.search(r'Memory Limit:\s*\*\*(\d+(?:\.\d+)?)\s*MB\*\*', document, re.IGNORECASE)
        if space_match:
            space_limit = float(space_match.group(1))
            # Convert to int if it's a whole number
            if space_limit == int(space_limit):
                space_limit = int(space_limit)
        
        return {
            'time': time_limit,
            'space': space_limit
        }
    
    def _extract_problem_statement_from_report(self, document: str) -> str:
        """Extract content between **[Prompt]** and **[Assistant]** sections"""
        lines = document.split('\n')
        result_lines = []
        in_prompt_section = False
        
        for line in lines:
            if line.strip() == "**[Prompt]**":
                in_prompt_section = True
                continue
            elif line.strip() == "**[Assistant]**":
                break
            elif in_prompt_section:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _extract_limits_with_gpt(self, content: str, filename: str) -> Optional[Dict]:
        """Use GPT-5 to extract time and space limits from content"""
        """Use GPT-5 to extract time and space limits from content"""
        prompt = f"""
You are an expert at extracting structured information from competitive programming problem statements.

Your task is to extract the time limit and space/memory limit from the following problem statement.

IMPORTANT REQUIREMENTS:
1. Return ONLY a valid JSON object with exactly two fields: "time" and "space"
2. "time" should be a number representing the time limit in seconds (e.g., 1, 2, 1.5)
3. "space" should be a number representing the memory limit in MB (e.g., 32, 64, 256)
4. If the time is given in milliseconds, convert to seconds
5. If the space is given in GB, convert to MB
6. Return ONLY the JSON object, no explanations, no markdown code blocks, no additional text
7. The JSON must be parseable by json.loads() in Python

Example valid response:
{{"time": 1, "space": 32}}

Example valid response:
{{"time": 2.5, "space": 256}}

Now extract the time and space limits from this problem statement:

{content}

Return ONLY the JSON object:
"""
        
        try:
            response = self._make_api_call(prompt, "")
            
            # Clean up the response - remove markdown code blocks if present
            response = response.strip()
            if response.startswith('```'):
                # Remove code block markers
                lines = response.split('\n')
                # Remove first and last lines if they are code block markers
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].startswith('```'):
                    lines = lines[:-1]
                response = '\n'.join(lines).strip()
            
            # Parse JSON
            limits = json.loads(response)
            
            # Validate the structure
            if 'time' not in limits or 'space' not in limits:
                return None
            
            # Convert to proper numeric types
            time_val = limits['time']
            space_val = limits['space']
            
            # Handle various numeric formats
            if isinstance(time_val, str):
                time_val = float(time_val)
            if isinstance(space_val, str):
                space_val = float(space_val)
            
            # Convert to int if they are whole numbers
            if time_val == int(time_val):
                time_val = int(time_val)
            if space_val == int(space_val):
                space_val = int(space_val)
            
            return {
                'time': time_val,
                'space': space_val
            }
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return None
            return None
        except Exception as e:
            return None
    
    def _extract_github_url(self, document: str) -> Optional[str]:
        """Extract GitHub URL from document"""
        # Try exact format first
        github_url_pattern = r'\*\*GitHub URL:\*\*\s+(https://github\.com/[^\s\n]+)'
        match = re.search(github_url_pattern, document)
        if match:
            return match.group(1)
        
        # Try alternative formats
        alternative_patterns = [
            r'\*\*GitHub URL\*\*\s*:\s+(https://github\.com/[^\s\n]+)',
            r'\*\*GitHub URL:\*\*[^\n]*?(https://github\.com/[^\s\n]+)',
            r'GitHub URL[^:]*:\s*(https://github\.com/[^\s\n]+)',
        ]
        
        for pattern in alternative_patterns:
            match = re.search(pattern, document, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Robust fallback: Find any URL containing github.com
        robust_pattern = r'https?://[^\s\n]*github\.com[^\s\n]*'
        matches = re.finditer(robust_pattern, document, re.IGNORECASE)
        
        github_urls = [match.group(0) for match in matches]
        if github_urls:
            return max(github_urls, key=len)
        
        return None
    
    def _convert_to_ssh_url(self, https_url: str) -> str:
        """Convert HTTPS GitHub URL to SSH format"""
        if https_url.startswith('https://github.com/'):
            repo_path = https_url.replace('https://github.com/', '')
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
            ssh_url = f"git@github.com:{repo_path}.git"
            return ssh_url
        return https_url
    
    def _clone_repository(self, url: str, temp_dir: str) -> bool:
        """Clone GitHub repository to temporary directory"""
        import subprocess
        import os
        import shutil
        
        try:
            # Convert HTTPS URL to SSH format
            ssh_url = self._convert_to_ssh_url(url)
            
            # Ensure temp_dir doesn't exist
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # Try SSH first
            result = subprocess.run([
                'git', 'clone', '--depth=1', ssh_url, temp_dir
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return True
            
            # Fallback to HTTPS
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            https_result = subprocess.run([
                'git', 'clone', '--depth=1', url, temp_dir
            ], capture_output=True, text=True, timeout=120)
            
            return https_result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
