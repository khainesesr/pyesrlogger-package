import os
from dotenv import load_dotenv

def load_env_files(*env_files):
    """Decorator to load multiple environment variable files."""
    def decorator(cls):
        def wrapper(*args, **kwargs):
            for env_file in env_files:
                load_dotenv(env_file)
            return cls(*args, **kwargs)  # Instantiate the class
        return wrapper
    return decorator
