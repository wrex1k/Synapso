from PySide6.QtGui import QFont, QFontDatabase
from numpy.ma import size

# Font families
GENERAL_SANS = "General Sans"

# Font weights
WEIGHT_LIGHT = QFont.Weight.Light
WEIGHT_REGULAR = QFont.Weight.Normal
WEIGHT_MEDIUM = QFont.Weight.Medium
WEIGHT_SEMIBOLD = QFont.Weight.DemiBold
WEIGHT_BOLD = QFont.Weight.Bold

# Shared font sizes
SIZE_TINY = 13
SIZE_XSMALL = 14
SIZE_SMALL = 15
SIZE_NORMAL = 16
SIZE_MEDIUM = 17
SIZE_LARGE = 18
SIZE_XLARGE = 20
SIZE_TITLE = 32

SIZE_HEADER_SMALL = 42
SIZE_HEADER_LARGE = 84
LOGIN_HEADER_SMALL = 56
LOGIN_HEADER_LARGE = 92

SIZE_TUTORIAL_TITLE = 37
SIZE_TUTORIAL_SUBTITLE = 26
SIZE_TUTORIAL_INTRO = 24
SIZE_TUTORIAL_HOW = 24
SIZE_TUTORIAL_BASE_TEXT = 24
SIZE_TUTORIAL_KEY_CHIP = 24
SIZE_TUTORIAL_TIP = 24
SIZE_TUTORIAL_STEP_TITLE = 24
SIZE_TUTORIAL_STEP_COUNTER = 19
SIZE_TUTORIAL_ADVICE = 23
SIZE_TUTORIAL_STIMUL = 79
SIZE_TUTORIAL_ANSWER_LABEL = 21
SIZE_TUTORIAL_ANSWER_TEXT = 21
SIZE_TUTORIAL_NEXT_BUTTON = 18


def load_fonts() -> None:
    font_db = QFontDatabase()
    font_db.addApplicationFont(":/font/general-sans/GeneralSans-Regular.otf")
    font_db.addApplicationFont(":/font/general-sans/GeneralSans-Bold.otf")
    font_db.addApplicationFont(":/font/general-sans/GeneralSans-Medium.otf")
    font_db.addApplicationFont(":/font/general-sans/GeneralSans-Light.otf")

def get_general_sans(size: int = SIZE_NORMAL, weight: QFont.Weight = WEIGHT_REGULAR) -> QFont:
    font = QFont(GENERAL_SANS, size)
    font.setWeight(weight)
    return font

FONT_TITLE_LEFT = get_general_sans(SIZE_HEADER_SMALL)
FONT_TITLE_RIGHT = get_general_sans(SIZE_HEADER_LARGE, WEIGHT_SEMIBOLD)
FONT_LABEL = get_general_sans(SIZE_MEDIUM)
FONT_INPUT = get_general_sans(SIZE_NORMAL)
FONT_BUTTON = get_general_sans(SIZE_NORMAL)
FONT_INFO = get_general_sans(SIZE_MEDIUM)
FONT_NAVBAR = get_general_sans(SIZE_TITLE, WEIGHT_BOLD)

# base.py
BASE_FONT_STYLES = f"""
    * {{
        font-family: \"General Sans\";
        font-weight: 400;
    }}

    QLabel#titleLabel {{
        font-size: {SIZE_HEADER_SMALL}px;
        font-weight: 600;
    }}

    #usernameLabel {{
        font-size: {SIZE_XSMALL}px;
    }}

    QLabel#profilePicture {{
        font-size: {SIZE_MEDIUM}px;
    }}

    QLabel#inputLabel {{
        font-size: {SIZE_MEDIUM}px;
    }}

    QLineEdit#inputEdit {{
        font-size: {SIZE_SMALL}px;
    }}

    QPushButton#primaryButton {{
        font-size: {SIZE_SMALL}px;
    }}

    QPushButton#back {{
        font-size: {SIZE_SMALL}px;
    }}

    QPushButton#back:hover {{
        font-size: {SIZE_LARGE}px;
    }}
"""

# login.py
LOGIN_FONT_STYLES = f"""
    QLabel#titleLabelLeft {{
        font-size: {LOGIN_HEADER_SMALL}px;
    }}

    QLabel#titleLabelRight {{
        font-size: {LOGIN_HEADER_LARGE}px;
        font-weight: 600;
    }}

    #forgotPasswordLink, #startRegistration, #startRegistrationLabel {{
        font-size: {SIZE_MEDIUM}px;
    }}
"""

# register.py
REGISTER_FONT_STYLES = f"""
    #info, #uploadRestriction {{
        font-size: {SIZE_MEDIUM}px;
    }}

    #birthMonth, #day, #year {{
        font-size: {SIZE_MEDIUM}px;
    }}

    #birthMonthBox, #dayBox, #yearBox {{
        font-size: {SIZE_NORMAL}px;
    }}

    #uploadImageButton {{
        font-size: {SIZE_XSMALL}px;
    }}
"""

# forgot_password.py
FORGOT_PASSWORD_FONT_STYLES = f"""
    #descLabel {{
        font-size: {SIZE_MEDIUM}px;
    }}

    #resendButton {{
        font-size: {SIZE_NORMAL}px;
    }}

    #titleLeft {{
        font-size: {SIZE_HEADER_SMALL}px;
    }}

    #titleRight {{
        font-size: {SIZE_HEADER_SMALL}px;
        font-weight: 600;
    }}

    #updateButton, #verifyButton, #approveButton {{
        font-size: {SIZE_NORMAL}px;
    }}
"""

# games.py
GAMES_FONT_STYLES = f"""
    QLabel#gameTitle {{
        font-size: 22px;
        font-weight: 600;
    }}

    QLabel#gameDescription {{
        font-size: 15px;
    }}

    QLabel#switcherTitle {{
        font-size: 14px;
        font-weight: 500;
    }}

    QLabel#infoCardTitle {{
        font-size: 20px;
        font-weight: 500;
    }}

    QLabel#infoCardDescription {{
        font-size: 15px;
        font-weight: 500;
    }}

    QLabel#rtCardTitle,
    QLabel#accCardTitle,
    QLabel#piCardTitle {{
        font-size: 20px;
        font-weight: 500;
    }}

    QLabel#rtCardValue,
    QLabel#accCardValue,
    QLabel#piCardValue {{
        font-size: 22px;
        font-weight: 500;
    }}

    QLabel#rtCardGlobal,
    QLabel#accCardGlobal,
    QLabel#piCardGlobal {{
        font-size: 17px;
        font-weight: 400;
    }}

    QLabel#activityCardTitle {{
        font-size: 20px;
        font-weight: 500;
    }}

    QLabel#activityCardDescription {{
        font-size: 14px;
    }}

    QLabel#activityPPRowNumber,
    QLabel#activityGTRowNumber,
    QLabel#activityTWRowNumber,
    QLabel#activityTGRowNumber {{
        font-size: 16px;
    }}

    QLabel#activityPPRowTitle,
    QLabel#activityGTRowTitle,
    QLabel#activityTWRowTitle,
    QLabel#activityTGRowTitle {{
        font-size: 15px;
        font-weight: 500;
    }}

    QPushButton#tutorialButton,
    QPushButton#playButton {{
        font-size: 14px;
        font-weight: 500;
    }}

    QLabel#leaderboardCardTitle {{
        font-size: 20px;
        font-weight: 500;
    }}

    QLabel#leaderboardRowTitle {{
        font-size: 14px;
        font-weight: 500;
    }}

    QLabel#leaderboardRowValue {{
        font-size: 15px;
        font-weight: 600;
    }}

    QLabel#userRankLabel {{
        font-size: 15px;
        font-weight: 500;
    }}
"""

# profile.py
PROFILE_FONT_STYLES = f"""
    QLabel#profileUsernameLabel {{
        font-size: {SIZE_XLARGE}px;
        font-weight: 600;
    }}

    QLabel#profileHandleLabel {{
        font-size: {SIZE_SMALL}px;
        font-weight: 400;
    }}

    QLabel#profileMemberLabel {{
        font-size: {SIZE_XSMALL}px;
        font-weight: 400;
    }}

    QLabel#profileSectionTitle {{
        font-size: {SIZE_XLARGE}px;
        font-weight: 600;
    }}

    QLabel#profileInfoKey {{
        font-size: {SIZE_XSMALL}px;
        font-weight: 400;
    }}

    QLabel#profileInfoValue {{
        font-size: {SIZE_SMALL}px;
        font-weight: 500;
    }}
"""

# tutorial.py
TUTORIAL_FONT_STYLES = f"""
    QLabel#stroopTutorialTitle {{
        font-size: {SIZE_TUTORIAL_TITLE}px;
        font-weight: 500;
    }}

    QLabel#stroopTutorialSubtitle {{
        font-size: {SIZE_TUTORIAL_SUBTITLE}px;
        font-weight: 400;
    }}

    QLabel#stroopTutorialHow {{
        font-size: {SIZE_TUTORIAL_HOW}px;
        font-weight: 500;
    }}

    QLabel#stroopTutorialIntro {{
        font-size: {SIZE_TUTORIAL_INTRO}px;
        font-weight: 400;
    }}

    QLabel#tutorialBaseText {{
        font-size: {SIZE_TUTORIAL_BASE_TEXT}px;
        font-weight: 400;
    }}

    QWidget#keyWidget[compact=\"true\"] QLabel#keyLabel {{
        font-size: {SIZE_TUTORIAL_KEY_CHIP}px;
        font-weight: 600;
    }}

    QLabel#stroopTutorialTip {{
        font-size: {SIZE_TUTORIAL_TIP}px;
        font-weight: 400;
    }}

    QLabel#practiceTutorialTitle {{
        font-size: {SIZE_TUTORIAL_STEP_TITLE}px;
        font-weight: 500;
    }}

    QLabel#practiceTutorialStep {{
        font-size: {SIZE_TUTORIAL_STEP_COUNTER}px;
        font-weight: 400;
    }}

    QLabel#practiceTutorialAdvice {{
        font-size: {SIZE_TUTORIAL_ADVICE}px;
        font-weight: 400;
    }}

    QLabel#practiceTutorialStimul {{
        font-size: {SIZE_TUTORIAL_STIMUL}px;
        font-weight: 700;
    }}

    QLabel#practiceTutorialAnswerLabel {{
        font-size: {SIZE_TUTORIAL_ANSWER_LABEL}px;
        font-weight: 400;
    }}

    QLabel#practiceTutorialAnswerText {{
        font-size: {SIZE_TUTORIAL_ANSWER_TEXT}px;
        font-weight: 400;
    }}

    QPushButton#practiceTutorialButton {{
        font-size: {SIZE_TUTORIAL_NEXT_BUTTON}px;
        font-weight: 400;
    }}

    QPushButton#tutorialButton {{
        font-size: {SIZE_TINY}px;
        font-weight: 500;
    }}

    QPushButton#transparentButton {{
        font-size: {SIZE_SMALL}px;
        font-weight: 500;
    }}
"""

# forgot_password.py (inline widgets)
FORGOT_PASSWORD_INLINE_FONT_STYLES = """
    #titleRight {
        font-weight: 600;
    }

    QLineEdit[objectName^=\"otpEdit\"] {
        font-weight: 700;
    }
"""


def get_full_fonts() -> str:
    return (
        BASE_FONT_STYLES
        + LOGIN_FONT_STYLES
        + REGISTER_FONT_STYLES
        + FORGOT_PASSWORD_FONT_STYLES
        + GAMES_FONT_STYLES
        + PROFILE_FONT_STYLES
        + TUTORIAL_FONT_STYLES
        + FORGOT_PASSWORD_INLINE_FONT_STYLES
    )
