#!/usr/bin/env python3
"""
Document Reviewer - Main Entry Point

A scalable AI-powered document review system for competitive programming problems.
"""

import sys
import argparse
from document_reviewer import DocumentReviewSystem, ReviewResult


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Document Review Script - Ultimate Point Analysis',
        epilog='Examples:\n'
               '  python3 main.py doc.txt                    # Run GitHub + AI reviews\n'
               '  python3 main.py doc.txt --github-only      # Run only GitHub validation\n'
               '  python3 main.py doc.txt --ai-only          # Run only AI reviews\n'
               '  python3 main.py doc.txt --resume 5         # Run GitHub + AI (AI from point 5)\n'
               '  python3 main.py doc.txt --ai-only --resume 5  # Run only AI from point 5\n'
               '  python3 main.py doc.txt --single-review "Memory Limit Validation"  # Run single AI review\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('file', help='Path to the text file to review')
    parser.add_argument('--resume', type=int, default=1, metavar='X',
                       help='Resume AI reviews from point X (1-N, default: 1). GitHub validation always runs when enabled.')
    parser.add_argument('--github-only', action='store_true',
                       help='Run only GitHub requirements validation (non-AI review)')
    parser.add_argument('--ai-only', action='store_true',
                       help='Run only AI reviews, skip GitHub validation')
    parser.add_argument('--single-review', type=str, metavar='NAME',
                       help='Run only a single AI review by name (e.g., "Solution Uniqueness Validation")')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output (show all execution details in terminal)')
    
    args = parser.parse_args()
    
    # Handle conflicting arguments
    if args.github_only and args.ai_only:
        print("❌ Cannot use --github-only with --ai-only")
        sys.exit(1)
    
    if args.single_review and (args.github_only or args.ai_only):
        print("❌ Cannot use --single-review with other mode options")
        sys.exit(1)
    
    # Normalize skip options
    skip_github = args.ai_only
    github_only = args.github_only
    single_review = args.single_review
    
    # Initialize review system first for dynamic validation
    review_system = DocumentReviewSystem(quiet_mode=False)
    
    # Validate single review name if specified
    if single_review:
        available_reviews = review_system.get_available_reviews()
        
        if single_review not in available_reviews:
            print(f"❌ Invalid review name: '{single_review}'")
            print(f"📋 Available reviews:")
            for name in available_reviews:
                print(f"   - {name}")
            sys.exit(1)
    
    # Validate resume point (only applies to AI reviews)
    ai_reviewers_count = len(review_system.get_available_reviews())
    if not single_review and (args.resume < 1 or args.resume > ai_reviewers_count):
        print(f"❌ Invalid resume point: {args.resume}. Must be between 1 and {ai_reviewers_count} for AI reviews.")
        sys.exit(1)
    
    try:
        # Initialize review system with quiet mode (unless verbose flag is set)
        review_system = DocumentReviewSystem(quiet_mode=not args.verbose)
        
        # Validate API key early if AI reviews will be needed
        if not github_only:
            review_system._ensure_openai_client()
        
        # Load document
        print(f"📖 Loading document from {args.file}...")
        document = review_system.load_document(args.file)
        print(f"✅ Document loaded ({len(document)} characters)")
        
        # Model information
        print("\n🤖 Model Configuration:")
        print("   Primary: GPT-5 (gpt-5) with thinking mode enabled (reasoning effort: low)")
        print("   Secondary: GPT-4o (gpt-4o) for cleanup operations")
        print("   Max tokens: 16,000 (GPT-5 + reasoning) / 16,000 (GPT-4o cleanup)")
        print()
        
        # Run reviews with specified options
        results = review_system.run_reviews(
            document, 
            resume_from=args.resume,
            github_only=github_only,
            skip_github=skip_github,
            single_review=single_review
        )
        
        # Generate and save report
        if not args.verbose:
            print("📋 Generating final report...")
        else:
            print("\n" + "=" * 70)
            print("📋 GENERATING FINAL REPORT - ULTIMATE POINT ANALYSIS")
            print("=" * 70)
        
        report = review_system.generate_report(results)
        
        # Only display full report in verbose mode
        if args.verbose:
            print("\n" + report)
        
        # Save report
        review_system.save_report(report, args.file)
        
        # Exit code based on results (excluding skipped ones)
        failed_reviews = [name for name, result in results.items() 
                         if result.result == ReviewResult.FAIL]
        
        if failed_reviews:
            # Classify failures
            github_keywords = ["GitHub Requirements Validation", "GitHub Repository Setup",
                              "Hunyuan CPP Files Check", "Overall.md Format Validation", 
                              "Solution.md Content Consistency", "Problem Statement.md Content Consistency",
                              "Solution.md Horizontal Lines Check", "Memory Limit vs Maximum Usage Check",
                              "Utilities Delivery Validation"]
            github_failures = [name for name in failed_reviews 
                             if any(keyword in name for keyword in github_keywords)]
            ai_failures = [name for name in failed_reviews 
                         if not any(keyword in name for keyword in github_keywords)]
            
            if github_failures and ai_failures:
                print(f"\n❌ Review completed with {len(failed_reviews)} failures ({len(github_failures)} GitHub, {len(ai_failures)} AI)")
            elif github_failures:
                print(f"\n❌ Review completed with {len(github_failures)} GitHub failure(s)")
            else:
                print(f"\n❌ Review completed with {len(ai_failures)} AI failure(s)")
            sys.exit(1)
        else:
            print("\n✅ All reviews passed successfully!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
