class SessionNotEndedError(Exception):
    """Raised when the latest session is not ended yet."""
    pass

class SessionAlreadyEndedError(Exception):
    """Raised when the latest session is already ended."""
    pass

class NoActiveSessionError(Exception):
    """Raised when there is no active session to end."""
    pass

class SessionNotFoundError(Exception):
    """Raised when a session with the specified ID is not found."""
    pass
