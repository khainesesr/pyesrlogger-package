import os

def env_variable_check(key):
    """Decorator to check if an environment variable is set."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if key not in os.environ:
                raise KeyError(f"Environment variable '{key}' not found in environment file.")
            return func(self, *args, **kwargs)  # Call the original __init__ method
        return wrapper
    return decorator
