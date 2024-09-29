import os

def env_variable_check(key):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if key not in os.environ:
                raise KeyError(f"Environment variable '{key}' not found in environment file.")
            return func(*args, **kwargs)
        return wrapper
    return decorator
