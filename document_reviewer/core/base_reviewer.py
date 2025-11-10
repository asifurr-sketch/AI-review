"""
Base reviewer class that all specific reviewers inherit from
"""

import re
import time
from openai import OpenAI
from ..core.models import ReviewResponse, ReviewResult
from ..core.config import Config


class BaseReviewer:
    """Base class for all document reviewers"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.primary_model = Config.PRIMARY_MODEL
        self.secondary_model = Config.SECONDARY_MODEL
    
    def review(self, document: str) -> ReviewResponse:
        """Perform the review and return structured results"""
        raise NotImplementedError("Subclasses must implement review method")
    
    def _clean_failure_response(self, failure_response: str) -> str:
        """Enhanced cleanup with specific instructions for precise location reporting"""
        
        # Handle empty or "No text content" responses
        if not failure_response or failure_response.strip() == "":
            return "No failure details available - empty response from API"
        
        if "No text content" in failure_response:
            return "No failure details available - API returned no content"
        
        cleanup_prompt = """
You are an expert at extracting and cleaning failure information with PRECISE location identification.

TASK: Extract and present ONLY the failure-related information from the provided response. 

CRITICAL REQUIREMENTS FOR LOCATION PRECISION:
1. NEVER use generic placeholders like "CHAIN_XX" or "THOUGHT_XX_YY"
2. ALWAYS use EXACT identifiers like "CHAIN_01", "CHAIN_03", "THOUGHT_04_02", etc.
3. If multiple violations occur in the same location, list them separately with the same specific identifier
4. Keep ALL violation locations exactly as they appear in the original document
5. Include specific line numbers, function names, variable names when provided
6. Quote exact text that demonstrates violations
7. Preserve all specific examples and suggested fixes

LOCATION IDENTIFICATION RULES:
- Use exact chain identifiers: "CHAIN_01", "CHAIN_02", etc. (NEVER "CHAIN_XX")  
- Use exact thought identifiers: "THOUGHT_01_03", "THOUGHT_05_01", etc. (NEVER "THOUGHT_XX_YY")
- Use exact section names: "Metadata", "Problem Statement", "Response", etc.
- Include line numbers when available: "line 45", "lines 12-15"
- Include code elements: "function calculateTotal()", "variable userName", "class DataProcessor"

KEEP ALL FAILURE INSTANCES:
1. Keep EVERY instance of failure, even if the same error appears multiple times
2. Keep ALL specific quotes and examples that show violations
3. Remove all introductory text, long explanations, and verbose descriptions
4. Present failures in a clear, concise format with bullet points
5. Keep specific examples of violations and suggested fixes
6. Remove any "PASS" sections or successful parts
7. Keep the essential failure details but make them concise
8. If there are code examples, keep only the essential violation examples and fixes
9. Remove repetitive explanations but keep all distinct failure instances
10. DO NOT include "improved code examples", "alternative options", or multiple code variations
11. DO NOT include "Option 1", "Option 2" or similar alternative implementations
12. Focus only on what is wrong and the direct fix needed
13. PRESERVE ALL SPECIFIC QUOTES that demonstrate violations

FORMATTING REQUIREMENTS:
- Use clean bullet points with dashes (-)
- No **bold** or special markdown formatting
- Keep specific quotes that show violations
- Remove verbose explanations but keep essential failure details
- Group related violations by location when appropriate

EXAMPLE OF GOOD OUTPUT:
- CHAIN_03: Variable name "usr" violates naming conventions (line 45)  
- CHAIN_03: Function "calc" uses vague abbreviation (line 52)
- THOUGHT_02_01: Mathematical formula uses incorrect notation "O!" instead of "O()"
- Metadata section: Missing required field "GitHub URL"

EXAMPLE OF BAD OUTPUT:
- CHAIN_XX: Variable naming issues found
- Multiple violations in reasoning chains
- Some formatting problems detected

CRITICAL: Do NOT summarize multiple violations into general statements. Each violation must be listed separately with its exact location.

IMPORTANT: Focus on actionable failure information that helps the user understand what needs to be fixed. Avoid providing multiple code alternatives or improved examples.

Original Response:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.secondary_model,
                messages=[
                    {
                        "role": "user",
                        "content": f"{cleanup_prompt}\n\n{failure_response}"
                    }
                ],
                max_tokens=Config.CLEANUP_MAX_TOKENS,
                temperature=0.1
            )
            
            cleaned_response = response.choices[0].message.content
            
            if not cleaned_response:
                cleaned_response = "No text content in cleanup response"
            
            cleaned_response = cleaned_response.strip()
            
            # Remove **bold** and *italic* formatting
            cleaned_response = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_response)
            cleaned_response = re.sub(r'\*(.*?)\*', r'\1', cleaned_response)
            
            # Add delay to respect API rate limits
            time.sleep(Config.API_CALL_DELAY)
            
            return cleaned_response.strip()
        except Exception as e:
            return f"[Cleanup failed: {str(e)}]\n\n{failure_response}"

    def _make_api_call(self, prompt: str, document: str) -> str:
        """Make API call to GPT-5 with thinking mode enabled"""
        try:
            if self.primary_model.startswith("gpt-5"):
                # GPT-5 uses Responses API with thinking mode
                response = self.client.responses.create(
                    model=self.primary_model,
                    input=[
                        {
                            "role": "user", 
                            "content": f"{prompt}\n\n=== DOCUMENT TO REVIEW ===\n{document}"
                        }
                    ],
                    reasoning={"effort": "high"},
                    max_output_tokens=Config.MAX_OUTPUT_TOKENS
                )
                output_text = response.output_text if hasattr(response, 'output_text') and response.output_text else None
                if not output_text or output_text.strip() == "":
                    return "Error: API returned empty response. This may indicate the prompt needs refinement or the model timed out."
                return output_text
                
            elif self.primary_model.startswith("o"):
                # O-series models
                response = self.client.chat.completions.create(
                    model=self.primary_model,
                    messages=[
                        {
                            "role": "user", 
                            "content": f"{prompt}\n\n=== DOCUMENT TO REVIEW ===\n{document}"
                        }
                    ],
                    max_completion_tokens=Config.MAX_OUTPUT_TOKENS,
                    temperature=0.3
                )
                response_text = response.choices[0].message.content if response.choices and response.choices[0].message.content else None
                if not response_text or response_text.strip() == "":
                    return "Error: API returned empty response. This may indicate the prompt needs refinement or the model timed out."
                return response_text
                
            else:
                # GPT-4 models
                response = self.client.chat.completions.create(
                    model=self.primary_model,
                    messages=[
                        {
                            "role": "user",
                            "content": f"{prompt}\n\n=== DOCUMENT TO REVIEW ===\n{document}"
                        }
                    ],
                    max_tokens=Config.MAX_OUTPUT_TOKENS,
                    temperature=0.3
                )
                response_text = response.choices[0].message.content if response.choices and response.choices[0].message.content else None
                if not response_text or response_text.strip() == "":
                    return "Error: API returned empty response. This may indicate the prompt needs refinement or the model timed out."
                return response_text
            
        except Exception as e:
            return f"Error in AI call: {str(e)}"
    
    def _parse_response(self, response: str) -> ReviewResponse:
        """Parse the LLM response to extract pass/fail and reasoning"""
        response_lower = response.lower()
        
        # Check for API errors first
        if response.startswith("Error:") or response.startswith("Error in AI call:"):
            return ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=response
            )
        
        # Look for clear pass/fail indicators
        if "final verdict: pass" in response_lower or "conclusion: pass" in response_lower:
            result = ReviewResult.PASS
            lines = response.split('\n')
            for line in lines:
                if 'final verdict: pass' in line.lower() or 'conclusion: pass' in line.lower():
                    reasoning = line.strip()
                    break
            else:
                reasoning = "PASS - Review completed successfully"
        elif "final verdict: fail" in response_lower or "conclusion: fail" in response_lower:
            result = ReviewResult.FAIL
            reasoning = self._clean_failure_response(response.strip())
        elif "✅" in response or "pass" in response_lower.split()[-20:]:
            result = ReviewResult.PASS
            reasoning = "PASS - Review completed successfully"
        elif "❌" in response or "fail" in response_lower.split()[-20:]:
            result = ReviewResult.FAIL
            reasoning = self._clean_failure_response(response.strip())
        else:
            result = ReviewResult.FAIL
            reasoning = self._clean_failure_response(response.strip() + "\n\n[NOTE: Response was ambiguous, defaulting to FAIL]")
        
        return ReviewResponse(
            result=result,
            reasoning=reasoning
        )
