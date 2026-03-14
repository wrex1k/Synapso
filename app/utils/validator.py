import re
import datetime
from app.utils.logger import get_logger
from translations.translation import translate

"""
This module provides common validation functions for user input, such as:
- validate_email: checks if an email address is in a valid format,
- validate_otp: checks if an OTP code is a 6-digit numeric string
- validate_passwords_match: checks if two password fields match,
- validate_password: checks if a password meets strength requirements (length, character types)
- validate_username: checks if a username is valid (length, allowed characters)
- validate_birthdate: checks if a birthdate is valid and within an acceptable age range
"""

logger = get_logger(__name__)

# validate email
def validate_email(email: str) -> str | None:
    email = (email or "").strip()
    if not email:
        logger.error("Email is empty")
        return translate("Validator", "Please fill email")

    email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(email_regex, email):
        logger.error("Email invalid format: %s", email)
        return translate("Validator", "Please enter a valid email address")
    return None


# validate OTP code (6-digit numeric)
def validate_otp(otp: str) -> str | None:
    otp = (otp or "").strip()
    if len(otp) != 6 or not otp.isdigit():
        logger.error("Invalid OTP code format: %s", otp)
        return translate("Validator", "Invalid verification code")
    return None

# validate password match
def validate_passwords_match(password: str, confirm_password: str) -> str | None:
    if (password or "").strip() != (confirm_password or "").strip():
        logger.error("Passwords do not match")
        return translate("Validator", "Passwords do not match")
    return None

# validate password strength
def validate_password(password: str, *, min_len: int = 8, max_len: int = 72) -> str | None:
    password = (password or "").strip()

    if len(password) < min_len:
        logger.error("Password is too short: %d characters", len(password))
        return translate("Validator", "Password must be at least %1 characters").replace("%1", str(min_len))
    if len(password) > max_len:
        logger.error("Password is too long: %d characters", len(password))
        return translate("Validator", "Password cannot exceed %1 characters").replace("%1", str(max_len))
    if not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password):
        logger.error("Password lacks uppercase or lowercase letters")
        return translate("Validator", "Password must include both uppercase and lowercase letters")
    if not re.search(r"\d", password):
        logger.error("Password lacks a numeric character")
        return translate("Validator", "Password must include at least one number")
    return None

# validate username
def validate_username(username: str, min_len: int = 3, max_len: int = 30) -> str | None:
    username = (username or "").strip()
    if not username:
        logger.error("Username is empty")
        return translate("Validator", "Please fill username")
    if not (min_len <= len(username) <= max_len):
        logger.error("Username is too short or too long: %d characters", len(username))
        msg = translate("Validator", "Username must be between %1 and %2 characters")
        return msg.replace("%1", str(min_len)).replace("%2", str(max_len))
    if not re.match(r"^[A-Za-z0-9_]+$", username):
        logger.error("Username contains invalid characters: %s", username)
        return translate("Validator", "Username can only contain letters, numbers, and underscores")
    return None

# validate birthdate and age range
def validate_birthdate(birthdate: datetime.date, *, min_years: int = 15, max_years: int = 120) -> str | None:
    if not birthdate:
        logger.error("Birthdate is empty")
        return translate("Validator", "Please enter a valid birth date")
    if not isinstance(birthdate, datetime.date):
        logger.error("Birthdate is not a valid date object")
        return translate("Validator", "Please enter a valid birth date")

    today = datetime.date.today()

    age = int((today - birthdate).days / 365.2425)
    if age < min_years:
        logger.error("User is too young: %d years old", age, )
        return translate("Validator", "You must be at least %1 years old to register").replace("%1", str(min_years))
    if age > max_years:
        logger.error("User is too old: %d years old", age)
        return translate("Validator", "Please enter a valid birth date")
    return None