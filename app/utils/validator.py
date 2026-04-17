import re
import datetime
from app.utils.logger import get_logger
from translations.translation import translate

logger = get_logger(__name__) 

def validate_email(email: str) -> str | None:
    """Return an error message if the email is empty or malformed, else None."""
    email = (email or "").strip()
    if not email:
        logger.error("Email is empty")
        return translate("Validator", "Please fill email")

    email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(email_regex, email):
        logger.error("Email invalid format: %s", email)
        return translate("Validator", "Please enter a valid email address")
    return None


def validate_otp(otp: str) -> str | None:
    """Return an error message if the OTP is not a 6-digit code, else None."""
    otp = (otp or "").strip()
    if len(otp) != 6 or not otp.isdigit():
        logger.error("Invalid OTP code format: %s", otp)
        return translate("Validator", "Invalid verification code")
    return None

def validate_passwords_match(password: str, confirm_password: str) -> str | None:
    """Return an error message if the passwords differ, else None."""
    if (password or "").strip() != (confirm_password or "").strip():
        logger.error("Passwords do not match")
        return translate("Validator", "Passwords do not match")
    return None

def validate_password(password: str, *, min_len: int = 8, max_len: int = 72) -> str | None:
    """Return an error message if the password is weak or out of length range, else None."""
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

def validate_username(username: str, min_len: int = 3, max_len: int = 30) -> str | None:
    """Return an error message if the username is invalid, else None."""
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

def validate_birthdate(birthdate: datetime.date, *, min_years: int = 15, max_years: int = 120) -> str | None:
    """Return an error message if the birthdate is missing or out of age range, else None."""
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