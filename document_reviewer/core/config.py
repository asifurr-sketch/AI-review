"""
Configuration settings for the document review system
"""

import os


class Config:
    """Configuration class for the document review system"""
    
    # Model Configuration
    PRIMARY_MODEL = "gpt-5"  # GPT-5 for main review calls
    SECONDARY_MODEL = "gpt-4o"  # GPT-4o for cleanup operations
    
    # Cleanup Configuration
    ENABLE_FAILURE_CLEANUP = False  # Toggle for second summarization call on failures
    
    # Token Limits
    MAX_OUTPUT_TOKENS = 20000
    CLEANUP_MAX_TOKENS = 16000
    
    # API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Retry Configuration
    API_RETRY_ATTEMPTS = 5  # Number of retry attempts for API calls (increased for reliability)
    API_RETRY_DELAY = 3  # Initial delay in seconds, will use exponential backoff
    API_TIMEOUT = 600  # Timeout in seconds for API calls (10 minutes for GPT-5 reasoning)
    
    # Rate Limiting
    API_CALL_DELAY = 0.5  # seconds
    MAX_PARALLEL_REVIEWS = 1  # Sequential execution (1 = no parallelism, prevents throttling)
    
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
