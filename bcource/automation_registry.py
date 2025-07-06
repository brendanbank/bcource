
_automation_functions = {}

def register_automation_function(name=None, description=None, enabled=True):
    """
    A decorator to register automation functions.

    Args:
        name (str, optional): The name to register the function under.
                              If None, the function's own name will be used.
        description (str, optional): A brief description of the function.
        enabled (bool, optional): Whether the function is initially enabled.
                                   Defaults to True.
    """
    def decorator(func):
        func_name = name if name is not None else func.__name__
        if func_name in _automation_functions:
            raise ValueError(f"Automation function '{func_name}' already registered.")

        _automation_functions[func_name] = {
            'function': func,
            'description': description,
            'enabled': enabled,
            'module': func.__module__, # Useful for introspection
            'qualified_name': f"{func.__module__}.{func.__name__}" # For full path
        }
        return func
    return decorator

def get_registered_automation_functions():
    """
    Returns a copy of the dictionary of registered automation functions.
    """
    return _automation_functions.copy()

def get_automation_function(name):
    """
    Retrieves a specific registered automation function by its name.
    """
    return _automation_functions.get(name)
