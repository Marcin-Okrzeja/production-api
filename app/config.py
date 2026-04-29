"""
Configuration settings for Production AI API
Using pydantic-settings for type-safe configuration
"""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_debug: bool = Field(default=False)
    
    # Groq API Configuration
    groq_api_key: str = Field(default="your_groq_api_key_here")
    
    # LangSmith Configuration
    langsmith_api_key: Optional[str] = Field(default=None)
    langsmith_tracing: bool = Field(default=False)
    langsmith_project: str = Field(default="production-api")
    
    # Security Configuration
    secret_key: str = Field(default="dev-secret-key")
    cors_origins: str = Field(default="http://localhost:3000")
    
    # Monitoring Configuration
    log_level: str = Field(default="INFO")
    metrics_enabled: bool = Field(default=True)
    
    # Cost Optimization Configuration
    cache_ttl: int = Field(default=3600)  # 1 hour
    max_tokens_per_request: int = Field(default=4000)
    enable_model_routing: bool = Field(default=True)
    
    # Model Configuration
    cheap_model: str = Field(default="llama-3.1-8b-instant")
    expensive_model: str = Field(default="llama-3.3-70b-versatile")
    classifier_model: str = Field(default="llama-3.1-8b-instant")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return [self.cors_origins]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.api_debug and self.secret_key != "dev-secret-key"
    
    @property
    def langsmith_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled"""
        return self.langsmith_tracing and self.langsmith_api_key is not None


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


# Environment-specific settings
class DevelopmentSettings(Settings):
    """Development environment settings"""
    api_debug: bool = True
    log_level: str = "DEBUG"
    metrics_enabled: bool = False


class ProductionSettings(Settings):
    """Production environment settings"""
    api_debug: bool = False
    log_level: str = "INFO"
    metrics_enabled: bool = True


def get_environment_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "development":
        return DevelopmentSettings()
    else:
        return Settings()


# Configuration validation
def validate_configuration() -> bool:
    """Validate that required configuration is present"""
    errors = []
    
    if not settings.groq_api_key or settings.groq_api_key == "your_groq_api_key_here":
        errors.append("GROQ_API_KEY is required")
    
    if settings.is_production and settings.secret_key == "dev-secret-key":
        errors.append("SECRET_KEY must be set in production")
    
    if settings.langsmith_tracing and not settings.langsmith_api_key:
        errors.append("LANGSMITH_API_KEY is required when LANGSMITH_TRACING is true")
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


# Print configuration on startup
def print_configuration():
    """Print current configuration (without secrets)"""
    print("🔧 Configuration:")
    print(f"  Environment: {'Production' if settings.is_production else 'Development'}")
    print(f"  API Host: {settings.api_host}:{settings.api_port}")
    print(f"  Debug Mode: {settings.api_debug}")
    print(f"  Log Level: {settings.log_level}")
    print(f"  Metrics Enabled: {settings.metrics_enabled}")
    print(f"  Cache TTL: {settings.cache_ttl}s")
    print(f"  Max Tokens: {settings.max_tokens_per_request}")
    print(f"  Model Routing: {settings.enable_model_routing}")
    print(f"  LangSmith: {'Enabled' if settings.langsmith_enabled else 'Disabled'}")
    print(f"  CORS Origins: {', '.join(settings.cors_origins_list)}")


if __name__ == "__main__":
    # Test configuration
    print_configuration()
    print(f"\n✅ Configuration valid: {validate_configuration()}")
