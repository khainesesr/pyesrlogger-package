import os
from dotenv import load_dotenv

def load_env_files(*env_files):
    """Decorator to load multiple environment variable files."""
    def decorator(cls):
        original_init = cls.__init__  # Store the original __init__ method
        
        def wrapper(self, *args, **kwargs):
            # If no env files are provided, skip loading
            if env_files:
                for env_file in env_files:
                    load_dotenv(env_file)
            else:
                print("No environment files provided to load.")
            return original_init(self, *args, **kwargs)  # Call the original __init__ method
        cls.__init__ = wrapper  # Override the __init__ method
        return cls
    return decorator
