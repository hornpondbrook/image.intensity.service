import os
from typing import Type, Dict

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_secret_key')
    DEBUG = False
    TESTING = False
    # Set a maximum content length for uploads, defaulting to 5MB
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))
    # Define allowed image formats from an environment variable
    ALLOWED_IMAGE_FORMATS = os.environ.get('ALLOWED_IMAGE_FORMATS', 'PNG,JPEG').split(',')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    # In a real production environment, you might override other settings
    # For example, setting a more secure SECRET_KEY from a vault
    pass


class TestingConfig(Config):
    """Testing configuration."""
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
    """Returns the configuration class for the given environment name."""
    return config_by_name.get(config_name, DevelopmentConfig)
