import os
from typing import Type, Dict

class Config:
    """
    Base configuration class.
    
    Contains default settings common to all environments. Other configuration
    classes inherit from this class and can override these settings.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_secret_key')
    DEBUG = False
    TESTING = False
    # Set a maximum content length for uploads, defaulting to 5MB
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))
    # Define allowed image formats from an environment variable
    ALLOWED_IMAGE_FORMATS = os.environ.get('ALLOWED_IMAGE_FORMATS', 'PNG,JPEG').split(',')
    GRPC_SERVER_ADDRESS = os.environ.get('GRPC_SERVER_ADDRESS', 'localhost:50051')


class DevelopmentConfig(Config):
    """
    Development configuration class.
    
    Enables debug mode for a better development experience, providing detailed
    error pages and auto-reloading.
    """
    DEBUG = True


class ProductionConfig(Config):
    """
    Production configuration class.
    
    This configuration should be used when the application is deployed live.
    It disables debug mode for security and performance.
    """
    # In a real production environment, you might override other settings
    # For example, setting a more secure SECRET_KEY from a vault
    pass


class TestingConfig(Config):
    """
    Testing configuration class.
    
    Enables testing mode, which can alter application behavior to make testing
    easier. For example, it might use a smaller payload size limit for uploads.
    """
    TESTING = True
    # Use a smaller size limit for tests to make them faster
    MAX_CONTENT_LENGTH = 500 * 1024  # 500 KB for testing


# Dictionary to map environment names to configuration classes
config_by_name: Dict[str, Type[Config]] = dict(
    development=DevelopmentConfig,
    production=ProductionConfig,
    testing=TestingConfig
)

def get_config_by_name(config_name: str) -> Type[Config]:
    """
    Retrieves a configuration class based on its name.
    
    Args:
        config_name: The name of the environment (e.g., 'development',
            'production', 'testing').
    
    Returns:
        The corresponding configuration class. Defaults to DevelopmentConfig if
        the name is not found.
    """
    return config_by_name.get(config_name, DevelopmentConfig)
