import os
from typing import Optional

from app.utils.logger import get_logger

from PySide6.QtCore import QCoreApplication, QLocale, QTranslator, QT_TRANSLATE_NOOP
from PySide6.QtWidgets import QApplication

"""
This module provides translation management utilities for the application, including:
- TranslationManager: a class that handles loading and switching translations,
- get_translation_manager: a singleton accessor for the TranslationManager instance,
"""

logger = get_logger(__name__)

class TranslationManager:
    def __init__(self):
        self.translator: Optional[QTranslator] = None
        self.current_language: str = "en"
        self.translations_dir = os.path.dirname(__file__)
    
    def load_translation(self, language: str = "sk") -> bool:
        app = QApplication.instance()
        if not app:
            logger.warning("QApplication not yet created")
            return False
        
        if self.translator:
            app.removeTranslator(self.translator)
        
        self.translator = QTranslator(app)
        
        translation_file = os.path.join(
            self.translations_dir,
            f"synapso_{language}.qm"
        )
        
        if self.translator.load(translation_file):
            app.installTranslator(self.translator)
            self.current_language = language
            logger.info(f"Translation loaded: {language}")
            return True
    
    def get_system_language(self) -> str:
        locale = QLocale.system().name()
        language = locale.split('_')[0]
        return language
    
    def switch_language(self, language: str) -> bool:
        return self.load_translation(language)


_translation_manager = None


def get_translation_manager() -> TranslationManager:
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def init_translations(language: Optional[str] = None) -> bool:
    manager = get_translation_manager()
    
    if language is None:
        language = manager.get_system_language()
        
        supported_languages = ['sk', 'en']
        if language not in supported_languages:
            language = 'en'
    
    return manager.load_translation(language)


def translate(context: str, source_text: str) -> str:
    return QCoreApplication.translate(context, source_text)

# error message translations
QT_TRANSLATE_NOOP('Errors', 'Invalid email format')
QT_TRANSLATE_NOOP('Errors', 'Invalid password')
QT_TRANSLATE_NOOP('Errors', 'Invalid credentials')
QT_TRANSLATE_NOOP('Errors', 'Email already in use')
QT_TRANSLATE_NOOP('Errors', 'Username already taken')
QT_TRANSLATE_NOOP('Errors', 'Code has expired or is invalid')
QT_TRANSLATE_NOOP('Errors', 'User already registered')
QT_TRANSLATE_NOOP('Errors', 'New password must be different from the old password')

# validator message translations with placeholders
QT_TRANSLATE_NOOP('Validator', 'Password must be at least %1 characters')
QT_TRANSLATE_NOOP('Validator', 'Password cannot exceed %1 characters')
QT_TRANSLATE_NOOP('Validator', 'Username must be between %1 and %2 characters')
QT_TRANSLATE_NOOP('Validator', 'You must be at least %1 years old to register')

# forgot password specific messages
QT_TRANSLATE_NOOP('ForgotPassword', 'Please wait before sending another reset request')


def get_error_message(error_code: str, context: str = "Errors") -> str:
    error_map = {
        # login errors
        "invalid_email_format": QCoreApplication.translate(context, "Invalid email format"),
        "invalid_password": QCoreApplication.translate(context, "Invalid password"),
        "invalid_credentials": QCoreApplication.translate(context, "Invalid credentials"),
        
        # registration errors
        "email_already_in_use": QCoreApplication.translate(context, "Email already in use"),
        "username_already_taken": QCoreApplication.translate(context, "Username already taken"),
        "user_already_registered": QCoreApplication.translate(context, "User already registered"),
        
        # forgot password errors
        "token_expired": QCoreApplication.translate(context, "Code has expired or is invalid"),
        "password_same_as_old": QCoreApplication.translate(context, "New password must be different from the old password"),
    }
    
    return error_map.get(error_code, error_code)
