class FacebookAutomationException(Exception):
    """Base exception for Facebook automation"""
    pass

class LoginFailedException(FacebookAutomationException):
    """Raised when login fails"""
    pass

class SecurityChallengeException(FacebookAutomationException):
    """Raised when security challenge is encountered"""
    pass