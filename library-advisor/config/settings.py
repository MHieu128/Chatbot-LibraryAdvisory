import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # File Upload Configuration
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 52428800))  # 50MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './data/uploads')
    SUPPORTED_EXTENSIONS = os.getenv('SUPPORTED_EXTENSIONS', 
                                   '.js,.ts,.jsx,.tsx,.cs,.csproj,.sln,.json,.md,.txt,.py,.vue,.html,.css,.scss,.yaml,.yml,.xml,.config').split(',')
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY_GPT = os.getenv('AZURE_OPENAI_API_KEY_GPT')
    AZURE_OPENAI_API_KEY_EMBEDDING = os.getenv('AZURE_OPENAI_API_KEY_EMBEDDING')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_GPT_DEPLOYMENT = os.getenv('AZURE_OPENAI_GPT_DEPLOYMENT', 'gpt-4o-mini')
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
    AZURE_OPENAI_API_VERSION = "2024-02-01"
    
    # FAISS Configuration
    FAISS_DB_PATH = os.getenv('FAISS_DB_PATH', './data/faiss_db')
    EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', 1536))
    
    # Validation
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = [
            'AZURE_OPENAI_API_KEY_GPT',
            'AZURE_OPENAI_API_KEY_EMBEDDING',
            'AZURE_OPENAI_ENDPOINT'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Create necessary directories
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.FAISS_DB_PATH, exist_ok=True)
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
