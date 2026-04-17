from enum import Enum

class AuthError(str, Enum):
    """Authentication and authorization error codes."""
    INVALID_CREDENTIALS = "invalid_credentials"
    USER_ALREADY_REGISTERED = "user_already_registered"
    EMAIL_ALREADY_IN_USE = "email_already_in_use"
    USERNAME_ALREADY_TAKEN = "username_already_taken"
    INVALID_EMAIL_FORMAT = "invalid_email_format"
    INVALID_PASSWORD = "invalid_password"
    WRONG_CURRENT_PASSWORD = "wrong_current_password"
    PASSWORD_SAME_AS_OLD = "password_same_as_old"
    TOKEN_EXPIRED = "token_expired"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

class ProfileError(str, Enum):
    """Profile management error codes."""
    USERNAME_TAKEN = "username_taken"
    SAVE_FAILED = "save_failed"
    PASSWORD_CHANGE_FAILED = "password_change_failed"
    DELETE_ACCOUNT_FAILED = "delete_account_failed"
    AVATAR_UPLOAD_FAILED = "avatar_upload_failed"

class ValidationError(str, Enum):
    """Validation error codes."""
    INVALID_USERNAME = "invalid_username"
    INVALID_EMAIL = "invalid_email"
    INVALID_BIRTHDATE = "invalid_birthdate"
    PASSWORDS_DONT_MATCH = "passwords_dont_match"
