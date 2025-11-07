"""
Main review system orchestration
"""

import os
import threading
import time
import concurrent.futures
from typing import Dict, List, Tuple, Optional
from openai import OpenAI

from ..core.models import ReviewResponse, ReviewResult
from ..core.config import Config
from ..reviewers.ai import *
from ..reviewers.github import GitHubReviewValidator


class DocumentReviewSystem:
    """Main system orchestrating all reviews"""
    
    def __init__(self, quiet_mode=False):
        self.detailed_output = []  # Capture all detailed output for the report
        self.output_lock = threading.Lock()  # Thread-safe output
        self.quiet_mode = quiet_mode  # Control output verbosity
        self.client = None  # Will be initialized when needed
        self.reviewers = {}  # Will be initialized when needed
        
        # Initialize GitHub validator (non-AI review) - works without API key
        self.github_validator = GitHubReviewValidator(quiet_mode=quiet_mode)
    
    def get_available_reviews(self):
        """Get list of available review names without initializing OpenAI client"""
        return [
            # Solution Uniqueness Validation
            "Unique Solution Validation",
            # Time Complexity Check
            "Time Complexity Authenticity Check",
            # Code Quality
            "Style Guide Compliance",
            "Naming Conventions", 
            "Documentation Standards",
            # Response Quality  
            "Response Relevance to Problem",
            "Mathematical Equations Correctness",
            "Problem Constraints Consistency",
            "Missing Approaches in Steps",
            "Code Elements Existence",
            "Example Walkthrough with Optimal Algorithm",
            "Time and Space Complexity Correctness",
            "Conclusion Quality",
            # Problem Statement and Solution Quality
            "Problem Statement Consistency",
            "Solution Passability According to Limits", 
            "Metadata Correctness",
            "Test Case Validation",
            "Sample Test Case Dry Run Validation",
            "Note Section Explanation Approach",
            # Reasoning Chain Quality
            "Inefficient Approaches Limitations",
            "Final Approach Discussion",
            "No Code in Reasoning Chains",
            # Subtopic, Taxonomy, and Reasoning Analysis
            "Subtopic Taxonomy Validation",
            # Time and Memory Limit Validation
            "Time Limit Validation",
            "Memory Limit Validation",
            "Subtopic Relevance",
            "Missing Relevant Subtopics",
            "Natural Thinking Flow in Thoughts",
            "Mathematical Variables and Expressions Formatting",
            # Limits Consistency Check
            "Limits Consistency Check",
            # Example Validation
            "Example Validation"
        ]
        

    def _ensure_openai_client(self):
        """Ensure OpenAI client is initialized with proper error handling"""
        if self.client is not None:
            return  # Already initialized
            
        # Try multiple API key sources in order
        keys_to_try = []
        
        # First check .env file
        env_path = '.env'
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key == 'OPENAI_API_KEY':
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            # Only try non-placeholder keys
                            if value and not value.startswith('your-key') and not value.startswith('sk-proj-placeholder'):
                                keys_to_try.append(('.env file', value))
        
        # Add environment variable as fallback
        env_key = os.getenv('OPENAI_API_KEY')
        if env_key and not env_key.startswith('your-key') and not env_key.startswith('sk-proj-placeholder'):
            keys_to_try.append(('environment variable', env_key))
        
        if not keys_to_try:
            # No valid keys found
            error_msg = """
❌ OPENAI_API_KEY not found!

📝 Setup Instructions:
   Option 1 (Recommended): Create .env file
   └─ echo "OPENAI_API_KEY=your-actual-key-here" > .env
   
   Option 2: Set environment variable  
   └─ export OPENAI_API_KEY=your-actual-key-here
   
💡 Get your API key from: https://platform.openai.com/api-keys
⚠️  Note: GPT-5 access is required for this tool

🔍 Current search locations:
   1. .env file in current directory (preferred)
   2. OPENAI_API_KEY environment variable
"""
            raise ValueError(error_msg.strip())
        
        # Try each key until one works
        last_error = None
        for source, api_key in keys_to_try:
            try:
                print(f"🔑 Testing API key from {source}...")
                
                self.client = OpenAI(api_key=api_key)
                
                # Test the key with a simple call
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Use cheapest/fastest model for testing
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                
                if response.choices and response.choices[0].message.content:
                    print(f"✅ API key from {source} is valid and working!")
                    # Initialize reviewers now that we have a working client
                    self.__init_reviewers__()
                    return
                else:
                    raise ValueError("API responded but with no content")
                    
            except Exception as e:
                last_error = e
                print(f"❌ API key from {source} failed: {str(e)}")
                self.client = None  # Reset client for next attempt
                continue
        
        # All keys failed
        error_msg = f"""
❌ All API keys failed validation!

🔧 Last error: {str(last_error)}

🔧 Common issues:
   • Invalid API key format
   • API key doesn't have GPT-5 access
   • Network connectivity problems
   • Rate limiting or quota exceeded

💡 Get a valid API key from: https://platform.openai.com/api-keys
⚠️  Ensure your key has access to GPT-5 models

🔍 Tried sources: {', '.join([source for source, _ in keys_to_try])}
"""
        raise ValueError(error_msg.strip())
        
    def __init_reviewers__(self):
        """Initialize all Ultimate reviewers - each as individual API call"""
        # At this point, self.client should be initialized by _ensure_openai_client()
        assert self.client is not None, "OpenAI client must be initialized before creating reviewers"
        
        self.reviewers = {
            # Solution Uniqueness Validation
            "Unique Solution Validation": UniqueSolutionReviewer(self.client),
            
            # Time Complexity Check
            "Time Complexity Authenticity Check": TimeComplexityAuthenticityReviewer(self.client),
            
            # Code Quality
            "Style Guide Compliance": StyleGuideReviewer(self.client),
            "Naming Conventions": NamingConventionsReviewer(self.client),
            "Documentation Standards": DocumentationReviewer(self.client),
            
            # Response Quality  
            "Response Relevance to Problem": ResponseRelevanceReviewer(self.client),
            "Mathematical Equations Correctness": MathEquationsReviewer(self.client),
            "Problem Constraints Consistency": ConstraintsConsistencyReviewer(self.client),
            "Missing Approaches in Steps": MissingApproachesReviewer(self.client),
            "Code Elements Existence": CodeElementsExistenceReviewer(self.client),
            "Example Walkthrough with Optimal Algorithm": ExampleWalkthroughReviewer(self.client),
            "Time and Space Complexity Correctness": ComplexityCorrectnessReviewer(self.client),
            "Conclusion Quality": ConclusionQualityReviewer(self.client),
            
            # Problem Statement and Solution Quality
            "Problem Statement Consistency": ProblemConsistencyReviewer(self.client),
            "Solution Passability According to Limits": SolutionPassabilityReviewer(self.client),
            "Metadata Correctness": MetadataCorrectnessReviewer(self.client),
            "Test Case Validation": TestCaseValidationReviewer(self.client),
            "Sample Test Case Dry Run Validation": SampleDryRunValidationReviewer(self.client),
            "Note Section Explanation Approach": NoteSectionReviewer(self.client),
            
            # Reasoning Chain Quality
            "Inefficient Approaches Limitations": InefficientLimitationsReviewer(self.client),
            "Final Approach Discussion": FinalApproachDiscussionReviewer(self.client),
            "No Code in Reasoning Chains": NoCodeInReasoningReviewer(self.client),
            
            # Subtopic, Taxonomy, and Reasoning Analysis
            "Subtopic Taxonomy Validation": SubtopicTaxonomyReviewer(self.client),
            
            # Time and Memory Limit Validation
            "Time Limit Validation": TimeLimitValidationReviewer(self.client),
            "Memory Limit Validation": MemoryLimitValidationReviewer(self.client),
            "Subtopic Relevance": SubtopicRelevanceReviewer(self.client),
            "Missing Relevant Subtopics": MissingSubtopicsReviewer(self.client),
            "Natural Thinking Flow in Thoughts": PredictiveHeadingsReviewer(self.client),
            "Mathematical Variables and Expressions Formatting": MathFormattingReviewer(self.client),
            
            # Limits Consistency Check
            "Limits Consistency Check": LimitsConsistencyReviewer(self.client),
            
            # Example Validation
            "Example Validation": ExampleValidationReviewer(self.client)
        }
    
    def _thread_safe_print(self, message: str, force_quiet=False):
        """Thread-safe printing and logging"""
        with self.output_lock:
            # Always log to detailed output for the report
            self.detailed_output.append(message)
            # Only print to console if not in quiet mode (unless forced)
            if not self.quiet_mode and not force_quiet:
                print(message)
    
    def _progress_print(self, message: str):
        """Print progress messages (shown even in quiet mode)"""
        with self.output_lock:
            print(message)
            self.detailed_output.append(message)
    
    def _run_single_ai_review(self, review_name: str, reviewer, document: str, review_number: int) -> Tuple[str, ReviewResponse]:
        """Run a single AI review in a thread-safe manner"""
        start_time = time.time()
        try:
            # Show start message even in quiet mode for AI reviews
            start_msg = f"🔄 {review_number}. {review_name} - Starting..."
            self._thread_safe_print(start_msg)
            
            result = reviewer.review(document)
            
            elapsed_time = time.time() - start_time
            status_emoji = "✅" if result.result == ReviewResult.PASS else "❌"
            # Show completion message even in quiet mode for AI reviews
            completion_msg = f"{status_emoji} {review_number}. {review_name} - {result.result.value} ({elapsed_time:.1f}s)"
            self._thread_safe_print(completion_msg)
            
            return review_name, result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"💥 {review_number}. {review_name} - ERROR: {str(e)} ({elapsed_time:.1f}s)"
            self._thread_safe_print(error_msg)
            return review_name, ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Review failed with error: {str(e)}"
            )
    
    def _run_single_ai_review_quiet(self, review_name: str, reviewer, document: str, review_number: int) -> Tuple[str, ReviewResponse]:
        """Run a single AI review without showing start message (used when start message is shown upfront)"""
        start_time = time.time()
        try:
            result = reviewer.review(document)
            
            elapsed_time = time.time() - start_time
            status_emoji = "✅" if result.result == ReviewResult.PASS else "❌"
            # Show completion message
            completion_msg = f"{status_emoji} {review_number}. {review_name} - {result.result.value} ({elapsed_time:.1f}s)"
            self._progress_print(completion_msg)
            
            return review_name, result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"💥 {review_number}. {review_name} - ERROR: {str(e)} ({elapsed_time:.1f}s)"
            self._progress_print(error_msg)
            return review_name, ReviewResponse(
                result=ReviewResult.FAIL,
                reasoning=f"Review failed with error: {str(e)}"
            )
    
    def load_document(self, file_path: str) -> str:
        """Load document from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Document file '{file_path}' not found")
        except Exception as e:
            raise Exception(f"Error reading document: {str(e)}")
    
    def run_reviews(self, document: str, resume_from: int = 0, github_only: bool = False, skip_github: bool = False, single_review = None) -> Dict[str, ReviewResponse]:
        """Run reviews on the document with various options"""
        results = {}
        self.detailed_output = []  # Reset for new run
        
        # Determine what to run
        if single_review:
            header_msg = f"🔍 Running single AI review: {single_review}..."
            self._progress_print(header_msg)
        elif github_only:
            header_msg = "🔍 Running GitHub Requirements Validation only..."
            self._progress_print(header_msg)
        elif skip_github:
            header_msg = f"🔍 Running AI reviews only (resuming from point {resume_from})..." if resume_from > 1 else "🔍 Running AI reviews only..."
            self._progress_print(header_msg)
        else:
            header_msg = f"🔍 Running complete review (AI + GitHub)..."
            self._progress_print(header_msg)
        
        separator = "=" * 70
        self._thread_safe_print(separator)
        
        # Ensure OpenAI client is initialized if AI reviews are needed
        if not github_only:
            self._ensure_openai_client()
        
        # Convert reviewers dict to list for indexing
        reviewer_items = list(self.reviewers.items())
        
        # Separate GitHub and AI reviews
        github_reviews = [(name, reviewer) for name, reviewer in reviewer_items if reviewer is None]
        ai_reviews = [(name, reviewer) for name, reviewer in reviewer_items if reviewer is not None]
        
        # Handle GitHub-only mode with detailed tasks
        if github_only:
            start_time = time.time()
            github_tasks = self.github_validator.validate_github_requirements_detailed(document)
            end_time = time.time()
            
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60.0
            
            task_count = 0
            total_tasks = len(github_tasks)
            for task_name, result in github_tasks:
                task_count += 1
                # Just show progress in quiet mode
                progress_msg = f"🔄 GitHub Task {task_count}/{total_tasks}: {result.result.value}"
                self._progress_print(progress_msg)
                
                # Store detailed information for report only
                running_msg = f"\n🔄 Running GitHub Task: {task_name}"
                self._thread_safe_print(running_msg, force_quiet=True)
                
                # Show both seconds and minutes for better accuracy perception
                if duration_seconds < 60:
                    time_msg = f"⏱️ Completed in {duration_seconds:.1f} seconds ({duration_minutes:.2f} minutes)"
                else:
                    time_msg = f"⏱️ Completed in {duration_minutes:.2f} minutes ({duration_seconds:.1f} seconds)"
                self._thread_safe_print(time_msg, force_quiet=True)
                
                results[task_name] = result
                
                result_msg = f"Result: {result.result.value}"
                self._thread_safe_print(result_msg, force_quiet=True)
                
                if result.result == ReviewResult.FAIL:
                    issues_header = "\nIssues Found:"
                    self._thread_safe_print(issues_header, force_quiet=True)
                    self._thread_safe_print(result.reasoning, force_quiet=True)
                
                sep_msg = "-" * 40
                self._thread_safe_print(sep_msg, force_quiet=True)
            
            return results
        
        # Handle single review mode
        if single_review:
            # Ensure OpenAI client is initialized if we need it
            self._ensure_openai_client()
            
            reviewer = self.reviewers[single_review]
            if reviewer is None:
                # This is a GitHub task, handle it specially
                github_tasks = self.github_validator.validate_github_requirements_detailed(document)
                for task_name, result in github_tasks:
                    if task_name == single_review:
                        running_msg = f"\n🔄 Running GitHub Task: {task_name}"
                        print(running_msg)
                        self.detailed_output.append(running_msg)
                        
                        result_msg = f"Result: {result.result.value}"
                        print(result_msg)
                        self.detailed_output.append(result_msg)
                        
                        if result.result == ReviewResult.FAIL:
                            issues_header = "\nIssues Found:"
                            print(issues_header)
                            self.detailed_output.append(issues_header)
                            print(result.reasoning)
                            self.detailed_output.append(result.reasoning)
                        
                        results[single_review] = result
                        break
            else:
                # This is an AI review - use the same format as parallel reviews
                running_msg = f"🔄 1. {single_review} - Starting..."
                self._thread_safe_print(running_msg)
                
                start_time = time.time()
                
                try:
                    result = reviewer.review(document)
                    
                    end_time = time.time()
                    duration_seconds = end_time - start_time
                    
                    status_emoji = "✅" if result.result == ReviewResult.PASS else "❌"
                    completion_msg = f"{status_emoji} 1. {single_review} - {result.result.value} ({duration_seconds:.1f}s)"
                    self._thread_safe_print(completion_msg)
                    
                    results[single_review] = result
                    
                except Exception as e:
                    elapsed_time = time.time() - start_time
                    error_msg = f"💥 1. {single_review} - ERROR: {str(e)} ({elapsed_time:.1f}s)"
                    self._thread_safe_print(error_msg)
                    
                    results[single_review] = ReviewResponse(
                        result=ReviewResult.FAIL,
                        reasoning=f"Review failed with error: {str(e)}"
                    )
            
            return results
        
        # Handle AI reviews with resume functionality
        start_index = resume_from
        if start_index < 1:
            start_index = 1
        elif start_index > len(ai_reviews):
            warning_msg = f"⚠️  Resume point {resume_from} is beyond available AI reviews ({len(ai_reviews)}). Starting from beginning."
            print(warning_msg)
            self.detailed_output.append(warning_msg)
            start_index = 1
        
        # Add skipped AI reviews as "SKIPPED"
        for i in range(1, start_index):
            review_name, _ = ai_reviews[i-1]
            results[review_name] = ReviewResponse(
                result=ReviewResult.PASS,
                reasoning="SKIPPED - Resumed from later point"
            )
        
        # Run AI reviews in parallel
        ai_reviews_to_run = ai_reviews[start_index-1:]  # Reviews to actually run
        
        if ai_reviews_to_run:
            parallel_msg = f"🚀 Starting {len(ai_reviews_to_run)} AI reviews in parallel..."
            self._progress_print(parallel_msg)
            
            # Show all starting messages immediately
            for i, (review_name, reviewer) in enumerate(ai_reviews_to_run):
                review_number = start_index + i
                start_msg = f"🔄 {review_number}. {review_name} - Starting..."
                self._progress_print(start_msg)
            
            # Use ThreadPoolExecutor for parallel execution with higher concurrency
            # Increased max_workers for better parallelism (all reviews run simultaneously)
            max_workers = len(ai_reviews_to_run)  # Run all AI reviews in parallel
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all AI reviews to the thread pool
                future_to_review = {}
                for i, (review_name, reviewer) in enumerate(ai_reviews_to_run):
                    review_number = start_index + i
                    future = executor.submit(self._run_single_ai_review_quiet, review_name, reviewer, document, review_number)
                    future_to_review[future] = (review_name, review_number)
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_review):
                    review_name, result = future.result()
                    results[review_name] = result
            
            # Summary after all parallel reviews complete
            total_completed = len(ai_reviews_to_run)
            # Count only the AI reviews we just ran
            ai_passed = sum(1 for name, result in results.items() 
                          if any(review_name == name for review_name, _ in ai_reviews_to_run) 
                          and result.result == ReviewResult.PASS)
            ai_failed = total_completed - ai_passed
            parallel_complete_msg = f"✅ All {total_completed} AI reviews completed in parallel: {ai_passed} passed, {ai_failed} failed"
            self._progress_print(parallel_complete_msg)
            
        # Run GitHub validation at the end (unless skipped)
        if not skip_github:
            # Show progress message
            progress_msg = f"🔄 Running GitHub validation..."
            self._progress_print(progress_msg)
            
            # Use the detailed GitHub tasks approach for consistency with --github-only mode
            start_time = time.time()
            github_tasks = self.github_validator.validate_github_requirements_detailed(document)
            end_time = time.time()
            
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60.0
            
            # Count passing tasks for summary
            passed_tasks = sum(1 for _, result in github_tasks if result.result == ReviewResult.PASS)
            total_tasks = len(github_tasks)
            
            # Show overall result progress
            github_result_msg = f"✅ GitHub validation: {passed_tasks}/{total_tasks} passed"
            self._progress_print(github_result_msg)
            
            # Process each task for detailed logging
            for task_name, result in github_tasks:
                # Store result immediately without logging task details to detailed_output
                # (they will be logged in the report generation phase instead)
                results[task_name] = result
        
        return results
    
    def generate_report(self, results: Dict[str, ReviewResponse]) -> str:
        """Generate comprehensive review report for all review points"""
        report = []
        
        # Add the complete detailed execution log first
        report.append("📋 COMPLETE EXECUTION LOG")
        report.append("=" * 70)
        report.append("")
        
        # Add all the detailed output that was captured during execution
        for line in self.detailed_output:
            report.append(line)
        
        report.append("")
        report.append("")
        report.append("📋 FINAL SUMMARY REPORT - ULTIMATE POINT ANALYSIS")
        report.append("=" * 70)
        report.append("")
        
        # Separate GitHub and AI results
        # GitHub results include both the main validation and individual GitHub tasks
        github_keywords = ["GitHub Requirements Validation", "GitHub Repository Setup",
                          "Hunyuan CPP Files Check", "Overall.md Format Validation", 
                          "Solution.md Content Consistency", "Problem Statement.md Content Consistency", 
                          "Solution.md Horizontal Lines Check", "Memory Limit vs Maximum Usage Check",
                          "Utilities Delivery Validation"]
        github_results = {name: result for name, result in results.items() 
                         if any(keyword in name for keyword in github_keywords)}
        ai_results = {name: result for name, result in results.items() 
                     if not any(keyword in name for keyword in github_keywords)}
        
        # Count results separately
        github_passed = sum(1 for r in github_results.values() if r.result == ReviewResult.PASS)
        github_failed = len(github_results) - github_passed
        
        ai_passed = sum(1 for r in ai_results.values() if r.result == ReviewResult.PASS and r.reasoning != "SKIPPED - Resumed from later point")
        ai_skipped = sum(1 for r in ai_results.values() if r.reasoning == "SKIPPED - Resumed from later point")
        ai_total = len(ai_results)
        ai_failed = ai_total - ai_passed - ai_skipped
        
        # Summary
        if github_results and ai_results:
            if ai_skipped > 0:
                report.append(f"📊 SUMMARY: GitHub: {github_passed}/{len(github_results)} passed | AI: {ai_passed}/{ai_total - ai_skipped} passed ({ai_skipped} skipped)")
            else:
                report.append(f"📊 SUMMARY: GitHub: {github_passed}/{len(github_results)} passed | AI: {ai_passed}/{ai_total} passed")
        elif github_results:
            report.append(f"📊 SUMMARY: GitHub: {github_passed}/{len(github_results)} passed")
        elif ai_results:
            if ai_skipped > 0:
                report.append(f"📊 SUMMARY: AI: {ai_passed}/{ai_total - ai_skipped} passed ({ai_skipped} skipped)")
            else:
                report.append(f"📊 SUMMARY: AI: {ai_passed}/{ai_total} passed")
        
        total_failed = github_failed + ai_failed
        if total_failed > 0:
            if github_failed > 0 and ai_failed > 0:
                report.append(f"⚠️  {total_failed} review(s) failed (GitHub: {github_failed}, AI: {ai_failed})")
            elif github_failed > 0:
                report.append(f"⚠️  {github_failed} GitHub review(s) failed")
            else:
                report.append(f"⚠️  {ai_failed} AI review(s) failed")
        
        if ai_skipped > 0:
            report.append(f"⏭️  {ai_skipped} AI review(s) skipped")
        report.append("")
        
        # Overall status
        if total_failed == 0 and ai_skipped == 0:
            report.append("🎉 OVERALL STATUS: ALL REVIEWS PASSED")
        elif total_failed == 0:
            report.append("🎉 OVERALL STATUS: ALL EXECUTED REVIEWS PASSED")
        else:
            report.append("⚠️  OVERALL STATUS: SOME REVIEWS FAILED")
        
        report.append("")
        report.append("=" * 70)
        
        # Results - show AI reviews first, then GitHub results
        ai_counter = 1
        for review_name, result in results.items():
            # Skip detailed GitHub tasks in first pass - show them after AI reviews
            if any(keyword in review_name for keyword in github_keywords):
                continue
                
            report.append("")
            report.append(f"📝 {ai_counter}. {review_name.upper()}")
            ai_counter += 1
            report.append("-" * 50)
            
            if result.reasoning == "SKIPPED - Resumed from later point":
                report.append("Status: ⏭️ SKIPPED")
            else:
                report.append(f"Status: {result.result.value}")
                
                if result.result == ReviewResult.FAIL:
                    report.append("")
                    report.append("Issues Found:")
                    report.append(result.reasoning)
                elif result.result == ReviewResult.PASS:
                    report.append("Review passed successfully")
            
            report.append("")
            report.append("-" * 50)
        
        # Now add GitHub results after AI reviews
        github_counter = ai_counter
        for review_name, result in results.items():
            # Only show GitHub tasks in this pass
            if not any(keyword in review_name for keyword in github_keywords):
                continue
                
            report.append("")
            report.append(f"📝 {github_counter}. {review_name.upper()}")
            github_counter += 1
            report.append("-" * 50)
            
            report.append(f"Status: {result.result.value}")
            
            if result.result == ReviewResult.FAIL:
                report.append("")
                report.append("Issues Found:")
                report.append(result.reasoning)
            elif result.result == ReviewResult.PASS:
                # For Utilities Delivery Validation, always show full output even on pass
                if "Utilities Delivery Validation" in review_name:
                    report.append("")
                    report.append(result.reasoning)
                else:
                    report.append("Review passed successfully")
        
            report.append("")
            report.append("-" * 50)
        
        return "\n".join(report)
    
    def save_report(self, report: str, original_filename: str):
        """Save report to file in reports folder with filename_report.txt format"""
        try:
            # Create reports directory if it doesn't exist
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Extract base filename without extension
            base_name = os.path.splitext(os.path.basename(original_filename))[0]
            
            # Create report filename
            report_filename = f"{base_name}_report.txt"
            report_path = os.path.join(reports_dir, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n💾 Report saved to: {report_path}")
        except Exception as e:
            print(f"\n❌ Error saving report: {str(e)}")
