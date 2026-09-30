# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom exceptions module
"""

class MTSCOSError(Exception):
    """Base exception for MTSCOS project"""
    
    def __init__(self, message: str, error_code: int = 500):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"

class DatabaseError(MTSCOSError):
    """Database operation error"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=501)

class ConfigurationError(MTSCOSError):
    """Configuration error"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=502)

class APIError(MTSCOSError):
    """API operation error"""
    
    def __init__(self, message: str, error_code: int = 400):
        super().__init__(message, error_code=error_code)

class ValidationError(MTSCOSError):
    """Validation error"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=400)

class AuthenticationError(MTSCOSError):
    """Authentication error"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=401)

class AuthorizationError(MTSCOSError):
    """Authorization error"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=403)

class ResourceNotFoundError(MTSCOSError):
    """Resource not found error"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=404)

class RateLimitError(MTSCOSError):
    """Rate limit exceeded error"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=429)

class AIError(MTSCOSError):
    """AI service error"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=503)

class FileError(MTSCOSError):
    """File operation error"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=504)
