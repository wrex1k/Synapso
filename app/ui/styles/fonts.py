from PySide6.QtGui import QFont, QFontDatabase

"""
This module handles loading and providing access to custom fonts used in the application.
Centralized font management with predefined sizes and styles.
"""

# Font families
GENERAL_SANS = "General Sans"
CLASH_GROTESK = "ClashGrotesk"

# Font weights
WEIGHT_LIGHT = QFont.Weight.Light
WEIGHT_REGULAR = QFont.Weight.Normal
WEIGHT_MEDIUM = QFont.Weight.Medium
WEIGHT_SEMIBOLD = QFont.Weight.DemiBold
WEIGHT_BOLD = QFont.Weight.Bold

# Font sizes (most used)
SIZE_SMALL = 13
SIZE_NORMAL = 14
SIZE_MEDIUM = 15
SIZE_LARGE = 16
SIZE_XLARGE = 32
SIZE_TITLE = 35
SIZE_HEADER = 48
SIZE_HEADER_LARGE = 52
SIZE_HUGE = 72

def load_fonts():
    font_db = QFontDatabase()
    # General Sans fonts
    font_db.addApplicationFont(":/font/general-sans/GeneralSans-Regular.otf")
    font_db.addApplicationFont(":/font/general-sans/GeneralSans-Bold.otf")
    font_db.addApplicationFont(":/font/general-sans/GeneralSans-Medium.otf")
    font_db.addApplicationFont(":/font/general-sans/GeneralSans-Light.otf")
    # ClashGrotesk fonts
    font_db.addApplicationFont(":/font/ClashGrotesk_Complete/Fonts/OTF/ClashGrotesk-Regular.otf")
    font_db.addApplicationFont(":/font/ClashGrotesk_Complete/Fonts/OTF/ClashGrotesk-Bold.otf")
    font_db.addApplicationFont(":/font/ClashGrotesk_Complete/Fonts/OTF/ClashGrotesk-Medium.otf")
    font_db.addApplicationFont(":/font/ClashGrotesk_Complete/Fonts/OTF/ClashGrotesk-Semibold.otf")

# Predefined font objects
def get_general_sans(size=SIZE_NORMAL, weight=WEIGHT_REGULAR):
    font = QFont(GENERAL_SANS, size)
    font.setWeight(weight)
    return font

def get_clash_grotesk(size=SIZE_NORMAL, weight=WEIGHT_REGULAR):
    font = QFont(CLASH_GROTESK, size)
    font.setWeight(weight)
    return font

# Common font presets
FONT_TITLE_LEFT = get_general_sans(SIZE_HEADER)  # 48px
FONT_TITLE_RIGHT = get_clash_grotesk(SIZE_HEADER_LARGE, WEIGHT_SEMIBOLD)  # 52px, semibold
FONT_LABEL = get_general_sans(SIZE_MEDIUM)  # 15px
FONT_INPUT = get_general_sans(SIZE_NORMAL)  # 14px
FONT_BUTTON = get_general_sans(SIZE_NORMAL)  # 14px
FONT_INFO = get_general_sans(SIZE_MEDIUM)  # 15px
FONT_OTP = get_general_sans(SIZE_XLARGE, WEIGHT_BOLD)  # 32px, bold
FONT_NAVBAR = get_general_sans(SIZE_TITLE, WEIGHT_MEDIUM)  # 35px, medium

# Font size stylesheet
FONT_SIZE_STYLESHEET = f"""
    /* Font size classes */
    .font-small {{
        font-size: {SIZE_SMALL}px;
    }}

    .font-normal {{
        font-size: {SIZE_NORMAL}px;
    }}

    .font-medium {{
        font-size: {SIZE_MEDIUM}px;
    }}

    .font-large {{
        font-size: {SIZE_LARGE}px;
    }}

    .font-xlarge {{
        font-size: {SIZE_XLARGE}px;
    }}

    .font-title {{
        font-size: {SIZE_TITLE}px;
    }}

    .font-header {{
        font-size: {SIZE_HEADER}px;
    }}

    .font-header-large {{
        font-size: {SIZE_HEADER_LARGE}px;
    }}

    .font-huge {{
        font-size: {SIZE_HUGE}px;
    }}

    /* Specific component fonts */
    #titleLabelLeft {{
        font-size: {SIZE_HEADER}px;
    }}

    #titleLabelRight {{
        font-size: {SIZE_HUGE}pt;
        font-weight: 600;
    }}

    #titleLabel {{
        font-size: {SIZE_TITLE}px;
    }}

    #descLabel, #info, #uploadRestriction {{
        font-size: {SIZE_MEDIUM}px;
    }}

    #forgotPasswordLink, #startRegistration, #startRegistrationLabel {{
        font-size: {SIZE_MEDIUM}px;
    }}

    QLineEdit#inputEdit {{
        font-size: {SIZE_NORMAL}px;
    }}

    QPushButton {{
        font-size: {SIZE_NORMAL}px;
    }}

    QLabel#inputLabel {{
        font-size: {SIZE_MEDIUM}px;
    }}

    #profilePicture, #birthMonth, #day, #year {{
        font-size: {SIZE_LARGE}px;
    }}

    #birthMonthBox, #dayBox, #yearBox {{
        font-size: {SIZE_NORMAL}px;
    }}

    #uploadImageButton {{
        font-size: {SIZE_NORMAL}px;
    }}

    #resendButton {{
        font-size: {SIZE_NORMAL}px;
    }}

    #titleRight {{
        font-size: {SIZE_HEADER_LARGE}px;
        font-weight: 600;
    }}

    #titleLeft {{
        font-size: {SIZE_HEADER}px;
    }}

    #updateButton, #verifyButton, #approveButton {{
        font-size: {SIZE_NORMAL}px;
    }}
"""