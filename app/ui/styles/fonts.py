from PySide6.QtGui import QFont, QFontDatabase

from app.ui.styles.colors import GRAY

# font family
GENERAL_SANS = "General Sans"

# font weights
WEIGHT_LIGHT = QFont.Weight.Light
WEIGHT_REGULAR = QFont.Weight.Normal
WEIGHT_MEDIUM = QFont.Weight.Medium
WEIGHT_SEMIBOLD = QFont.Weight.DemiBold
WEIGHT_BOLD = QFont.Weight.Bold

# font sizes
SIZE_XXSMALL = 12
SIZE_XSMALL = 14
SIZE_SMALL = 15

SIZE_NORMAL = 16
SIZE_MEDIUM = 17

SIZE_LARGE = 18
SIZE_XLARGE = 19

# headings
SIZE_H1 = 26
SIZE_H2 = 24
SIZE_H3 = 22
SIZE_H4 = 21
SIZE_H5 = 20

# display
SIZE_DISPLAY_SM = 28
SIZE_DISPLAY_MD = 32
SIZE_DISPLAY_LG = 38
SIZE_DISPLAY_XL = 42
SIZE_DISPLAY_XXL = 56
SIZE_DISPLAY_XXXL = 92

# navbar
SIZE_NAVBAR_TITLE = SIZE_DISPLAY_LG

# register
REGISTER_TITLE = SIZE_DISPLAY_XL

# login
LOGIN_HEADER_LEFT = SIZE_DISPLAY_XXL
LOGIN_HEADER_RIGHT = SIZE_DISPLAY_XXXL

# forgot password
FORGOT_HEADER_LEFT = SIZE_DISPLAY_XL
FORGOT_HEADER_RIGHT = SIZE_DISPLAY_XXL

# tutorial
SIZE_TUTORIAL_SMALL = 23
SIZE_TUTORIAL_NORMAL = SIZE_H2
SIZE_TUTORIAL_LARGE = SIZE_H1
SIZE_TUTORIAL_XLARGE = 37
SIZE_TUTORIAL_XXLARGE = SIZE_DISPLAY_XXXL
SIZE_TUTORIAL_ANSWER_LABEL = SIZE_H2
SIZE_TUTORIAL_COMPLETION = 46


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

# default fonts
FONT_LABEL = get_general_sans(SIZE_MEDIUM)
FONT_INPUT = get_general_sans(SIZE_NORMAL)
FONT_BUTTON = get_general_sans(SIZE_NORMAL)
FONT_INFO = get_general_sans(SIZE_MEDIUM)


# base.py
BASE_FONT_STYLES = f"""
    * {{
        font-family: "{GENERAL_SANS}";
        font-weight: {WEIGHT_REGULAR};
    }}
    
    QLabel#titleLabel {{
        font-size: {REGISTER_TITLE}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#pageTitleLabel {{
        font-size: {SIZE_H2}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#pageSubtitleLabel {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_REGULAR};
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
    QPushButton#langSkBtn,
    QPushButton#langEnBtn {{
        font-size: {SIZE_MEDIUM}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#titleLabelLeft {{
        font-size: {LOGIN_HEADER_LEFT}px;
    }}

    QLabel#titleLabelRight {{
        font-size: {LOGIN_HEADER_RIGHT}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    #forgotPasswordLink, #startRegistration, #startRegistrationLabel {{
        font-size: {SIZE_MEDIUM}px;
    }}
"""


# register.py
REGISTER_FONT_STYLES = f"""
    QLabel#profilePicture {{
        font-size: {SIZE_MEDIUM}px;
    }}

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
        font-size: {FORGOT_HEADER_LEFT}px;
    }}

    #titleRight {{
        font-size: {FORGOT_HEADER_RIGHT}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    #updateButton, #verifyButton, #approveButton {{
        font-size: {SIZE_NORMAL}px;
    }}
"""


# navbar.py
NAVBAR_FONT_STYLES = f"""
    QLabel#titleNavbarLabel {{
        font-size: {SIZE_NAVBAR_TITLE}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    #usernameLabel {{
        font-size: {SIZE_XSMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}
"""

# dashboard.py
DASHBOARD_FONT_STYLES = f"""
    QLabel#gameTitle {{
        font-size: {SIZE_H2}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#gameDescription {{
        font-size: {SIZE_XSMALL}px;
    }}

    QLabel#dashboardHeroTitle {{
        font-size: {SIZE_H5}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#dashboardHeroSubtitle {{
        font-size: {SIZE_H4}px;
    }}

    QLabel#dashboardInlineStatValue {{
        font-size: 25px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#dashboardInlineStatLabel {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#dashboardCardTitle {{
        font-size: {SIZE_H5}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#dashboardCardSubtitle {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#dashboardGoalValue {{
        font-size: {SIZE_H2}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#dashboardMutedText,
    QLabel#dashboardRowSubtitle {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#dashboardHighlightValue {{
        font-size: {SIZE_H5}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#dashboardMetricLabel {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM}
    }}

    QLabel#dashboardMetricValue,
    QLabel#dashboardRowTitle,
    QLabel#dashboardRowValue {{
        font-size: {SIZE_MEDIUM}px;
        font-weight: {WEIGHT_MEDIUM}
    }}

    QLabel#recentGameTitle {{
        font-size: {SIZE_H4}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#recentGameSubtitle {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#recentGameValue {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QPushButton#dashboardPrimaryButton {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM}
    }}
"""


# games.py
GAMES_FONT_STYLES = f"""
    QLabel#gameTitle {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#gameDescription {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#switcherTitle {{
        font-size: {SIZE_XSMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#infoCardTitle {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#infoCardDescription {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#rtCardTitle,
    QLabel#accCardTitle,
    QLabel#piCardTitle {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#rtCardValue,
    QLabel#accCardValue,
    QLabel#piCardValue {{
        font-size: {SIZE_H3}px;
    }}

    QLabel#rtCardGlobal,
    QLabel#accCardGlobal,
    QLabel#piCardGlobal {{
        font-size: {SIZE_MEDIUM}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QLabel#activityCardTitle {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#activityCardDescription {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#activityPPRowNumber,
    QLabel#activityGTRowNumber,
    QLabel#activityTWRowNumber,
    QLabel#activityTGRowNumber {{
        font-size: {SIZE_NORMAL}px;
    }}

    QLabel#activityPPRowTitle,
    QLabel#activityGTRowTitle,
    QLabel#activityTWRowTitle,
    QLabel#activityTGRowTitle {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QPushButton#tutorialButton,
    QPushButton#playButton {{
        font-size: {SIZE_XSMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#leaderboardCardTitle {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#leaderboardRowTitle {{
        font-size: {SIZE_XSMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#leaderboardRowValue {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#userRankLabel {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}
"""


# profile.py
PROFILE_FONT_STYLES = f"""
    QLabel#profileUsernameLabel {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#usernameLabel {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#profileHandleLabel {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#profileMemberLabel {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#profileSectionTitle {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#profileInputLabel {{
        font-size: {SIZE_SMALL}px;
    }}

    QLineEdit#profileLineEdit,
    QDateEdit#profileDateEdit {{
        font-size: {SIZE_SMALL}px;
    }}

    QWidget#profileView,
    QFrame#profileHeroCard,
    QFrame#profileMainCard {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#profileHeroMetaValue,
    QLabel#profileHeroMetaSubtext {{
        font-size: {SIZE_SMALL}px;
    }}

    QComboBox#profileBirthMonthBox,
    QComboBox#profileDayBox,
    QComboBox#profileYearBox {{
        font-size: {SIZE_NORMAL}px;
    }}

    QLabel#profileFeedbackLabel {{
        font-size: {SIZE_SMALL}px;
    }}

    QPushButton#profilePrimaryButton,
    QPushButton#profileDangerButton {{
        font-size: {SIZE_SMALL}px;
    }}

    QPushButton#profileDangerButton {{
        font-weight: {WEIGHT_MEDIUM};
    }}
        
    QLabel#profileDangerTitle {{
        font-size: {SIZE_H5}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#profileDangerDescription {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#profileInfoKey {{
        font-size: {SIZE_XSMALL}px;
    }}

    QLabel#profileInfoValue {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#profileReadonlyValue {{
        font-size: {SIZE_SMALL}px;
    }}
"""


# tutorial.py
TUTORIAL_FONT_STYLES = f"""
    QLabel#stroopTutorialTitle {{
        font-size: {SIZE_TUTORIAL_XLARGE}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#stroopTutorialSubtitle {{
        font-size: {SIZE_TUTORIAL_LARGE}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QLabel#stroopTutorialHow {{
        font-size: {SIZE_TUTORIAL_NORMAL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#stroopTutorialIntro {{
        font-size: {SIZE_TUTORIAL_NORMAL}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QLabel#tutorialBaseText {{
        font-size: {SIZE_TUTORIAL_NORMAL}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QWidget#keyWidget[compact="true"] QLabel#keyLabel {{
        font-size: {SIZE_TUTORIAL_NORMAL}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#stroopTutorialTip {{
        font-size: {SIZE_TUTORIAL_NORMAL}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QLabel#practiceTutorialTitle {{
        font-size: {SIZE_TUTORIAL_NORMAL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#practiceTutorialStep {{
        font-size: {SIZE_XLARGE}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QLabel#practiceTutorialAdvice {{
        font-size: {SIZE_TUTORIAL_SMALL}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QLabel#practiceTutorialStimul {{
        font-size: {SIZE_TUTORIAL_XXLARGE}px;
        font-weight: {WEIGHT_BOLD};
    }}

    QLabel#practiceTutorialAnswerLabel {{
        font-size: {SIZE_TUTORIAL_ANSWER_LABEL}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QLabel#practiceTutorialAnswerText {{
        font-size: {SIZE_H4}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QPushButton#practiceTutorialButton {{
        font-size: {SIZE_LARGE}px;
        font-weight: {WEIGHT_REGULAR};
    }}

    QPushButton#tutorialButton {{
        font-size: {SIZE_XSMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QPushButton#transparentButton {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}
"""
# statistics.py
STATISTICS_FONT_STYLES = f"""
    QWidget#statisticsView {{
        background-color: transparent;
    }}

    QLabel#statOverviewLabel {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#statOverviewValue {{
        font-size: {SIZE_H2}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#statOverviewSubtext {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#statChartTitle {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#statChartSubtitle {{
        font-size: {SIZE_SMALL}px;
    }}

    QLabel#statGameTitle {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#statGameMetricLabel {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#statGameMetricValue {{
        font-size: {SIZE_SMALL}px;
    }}
"""

# about.py
ABOUT_FONT_STYLES = f"""
    QLabel#aboutCardTitle {{
        font-size: {SIZE_H3}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#aboutSectionTitle {{
        font-size: {SIZE_H4}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#aboutDescriptionText {{
        font-size: {SIZE_MEDIUM}px;
    }}

    QLabel#aboutMetaText {{
        font-size: {SIZE_SMALL}px;
    }}

    QTextEdit#reportEditor {{
        font-size: {SIZE_SMALL}px;
    }}

    QPushButton#reportSendButton {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#builtWithName {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#builtWithDesc {{
        font-size: {SIZE_SMALL}px;
    }}

    QComboBox#changelogCombo {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_MEDIUM};
    }}

    QLabel#changelogBullet {{
        font-size: {SIZE_SMALL}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}
"""

# settings.py
SETTINGS_FONT_STYLES = f"""
    QLabel#settingsCardTitle {{
        font-size: {SIZE_H5}px;
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLabel#settingsCardDescription {{
        font-size: {SIZE_SMALL}px;
    }}

    QPushButton#langBtn {{
        font-size: {SIZE_SMALL}px;
    }}

    QPushButton#themeBtn {{
        font-size: {SIZE_SMALL}px;
    }}
"""


# forgot_password inline
FORGOT_PASSWORD_INLINE_FONT_STYLES = f"""
    #titleRight {{
        font-weight: {WEIGHT_SEMIBOLD};
    }}

    QLineEdit[objectName^="otpEdit"] {{
        font-size: {SIZE_DISPLAY_XXL}px;
        font-weight: {WEIGHT_BOLD};
    }}
"""


def get_full_fonts() -> str:
    return (
        BASE_FONT_STYLES
        + LOGIN_FONT_STYLES
        + REGISTER_FONT_STYLES
        + FORGOT_PASSWORD_FONT_STYLES
        + NAVBAR_FONT_STYLES
        + DASHBOARD_FONT_STYLES
        + GAMES_FONT_STYLES
        + STATISTICS_FONT_STYLES
        + PROFILE_FONT_STYLES
        + TUTORIAL_FONT_STYLES
        + ABOUT_FONT_STYLES
        + SETTINGS_FONT_STYLES
        + FORGOT_PASSWORD_INLINE_FONT_STYLES
    )
