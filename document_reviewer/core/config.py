"""
Configuration settings for the document review system
"""

import os


class Config:
    """Configuration class for the document review system"""
    
    # Model Configuration
    PRIMARY_MODEL = "gpt-5"  # GPT-5 for main review calls (highest quality)
    SECONDARY_MODEL = "gpt-4o"  # GPT-4o for cleanup operations
    GEMINI_MODEL = "gemini-2.0-flash-thinking-exp-1219"  # Gemini 2.5 Pro with thinking mode
    
    # Cleanup Configuration
    ENABLE_FAILURE_CLEANUP = True  # Toggle for second summarization call on failures
    
    # Token Limits
    MAX_OUTPUT_TOKENS = 16000  # Maximum for GPT-5 (no token shortage)
    CLEANUP_MAX_TOKENS = 16000
    GEMINI_MAX_OUTPUT_TOKENS = 8000  # Gemini supports higher token limits
    
    # API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # Google AI Studio API key
    
    # Retry Configuration
    API_RETRY_ATTEMPTS = 5  # Number of retry attempts for API calls (increased for reliability)
    API_RETRY_DELAY = 3  # Initial delay in seconds, will use exponential backoff
    API_TIMEOUT = None  # No timeout - let it run as long as needed
    
    # Rate Limiting
    API_CALL_DELAY = 0  # No delay needed with proper parallelism control
    MAX_PARALLEL_REVIEWS = 8  # Conservative parallelism for GPT-5 (prevents throttling, maintains quality)
    
    # GitHub Configuration
    CLONE_TIMEOUT = 60  # seconds
    SSH_TIMEOUT = 10  # seconds
    
    # Report Configuration
    REPORTS_DIR = "reports"
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.OPENAI_API_KEY:
            # Check .env file
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if key == 'OPENAI_API_KEY':
                                cls.OPENAI_API_KEY = value.strip().strip('"').strip("'")
                                break
        
        return bool(cls.OPENAI_API_KEY)
