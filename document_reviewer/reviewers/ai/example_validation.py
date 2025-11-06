"""
Example Validation Reviewer - validates examples consistency between metadata.json and problem statement
"""

import json
import re
import os
import tempfile
import shutil
import subprocess
from typing import Optional, Tuple
from ...core.base_reviewer import BaseReviewer
from ...core.models import ReviewResponse, ReviewResult
from ...prompts import ContentPrompts


class ExampleValidationReviewer(BaseReviewer):
    """Validates that examples in metadata.json match exactly with problem statement examples"""
    
    def review(self, document: str) -> ReviewResponse:
        """
        Main review method that validates example consistency
        """
        # Step 1: Extract GitHub URL from document
        github_url = self._extract_github_url(document)
        
        if not github_url:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning="Cannot validate examples: No GitHub URL found in document"
            )
        
        # Step 2: Clone repository and get metadata.json
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="example_validation_")
            
            # Clone repository
            clone_success = self._clone_repository(github_url, temp_dir)
            if not clone_success:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Cannot validate examples: Failed to clone repository {github_url}"
                )
            
            # Read metadata.json
            metadata_path = os.path.join(temp_dir, 'metadata.json')
            if not os.path.exists(metadata_path):
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning=f"Cannot validate examples: metadata.json not found in repository"
                )
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_content = f.read()
                metadata_data = json.loads(metadata_content)
            
            # Step 3: Extract examples from metadata.json
            if 'examples' not in metadata_data:
                return ReviewResponse(
                    result=ReviewResult.FAIL,
                    reasoning="Cannot validate examples: 'examples' field not found in metadata.json"
                )
            
            metadata_examples = metadata_data['examples']
            
            # Step 4: Create enhanced document with metadata examples for AI review
            enhanced_document = self._create_enhanced_document(document, metadata_content, metadata_examples)
            
            # Step 5: Use AI to perform comprehensive validation
            prompt = ContentPrompts.get_example_validation_prompt()
            response = self._make_api_call(prompt, enhanced_document)
            
            # Step 6: Parse and return the response
            return self._parse_response(response)
            
        except json.JSONDecodeError as e:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Cannot validate examples: Failed to parse metadata.json - {str(e)}"
            )
        except Exception as e:
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Error during example validation: {str(e)}"
            )
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
    
    def _create_enhanced_document(self, document: str, metadata_content: str, examples: list) -> str:
        """Create an enhanced document with metadata examples for AI review"""
        enhanced = f"""
=== VALIDATION TASK ===
Validate that examples in metadata.json match EXACTLY with examples in the problem statement.

=== METADATA.JSON EXAMPLES ===
{metadata_content}

Number of examples in metadata.json: {len(examples)}

Examples extracted from metadata.json:
"""
        
        for i, example in enumerate(examples, 1):
            enhanced += f"\nExample {i}:\n"
            enhanced += f"  Input: {example.get('input', 'NOT FOUND')}\n"
            enhanced += f"  Output: {example.get('output', 'NOT FOUND')}\n"
        
        enhanced += f"""

=== ORIGINAL DOCUMENT (Contains Problem Statement) ===
{document}

=== VALIDATION INSTRUCTIONS ===
1. Extract ALL examples from the problem statement (look in the **[Prompt]** section under "Examples" or similar)
2. Compare each example from metadata.json with the problem statement
3. Verify inputs match exactly (ignoring whitespace differences)
4. Verify outputs match exactly (ignoring whitespace differences)
5. Ensure the count matches
6. Report ANY discrepancies with exact details

Please perform comprehensive validation now.
"""
        
        return enhanced
    
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
