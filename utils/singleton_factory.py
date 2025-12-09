def singleton(cls):
    """
    Decorator that returns a singleton instance of a class.

    The singleton pattern is a design pattern that restricts the instantiation of a class to a single instance. This is useful when exactly one object is needed to coordinate actions across the system.
    The singleton pattern is implemented by creating a private static instance of the class and returning it on demand. The private static instance is stored in a dictionary with the class name as the key.

    Args:
        cls (type): The class to be decorated.

    Returns:
        function: A function that returns a singleton instance of the class.
    """
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance
