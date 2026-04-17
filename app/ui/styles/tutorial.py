from app.ui.styles.colors import *

TUTORIAL_STYLESHEET = f"""
QLabel#stroopTutorialTitle {{
        color: {FONT_PRIMARY};
        background: transparent;
    }}

QLabel#stroopTutorialSubtitle {{
        color: {GRAY};
        background: transparent;
    }}

QLabel#stroopTutorialHow {{
        color: {FONT_PRIMARY};
        background: transparent;
    }}

QWidget#stroopTutorialCard {{
        background-color: {BACKGROUND_GLASS};
        border-radius: 20px;
    }}

QLabel#stroopTutorialIcon {{
    padding: 10px;
    }}

QWidget#stroopTutorialIntro {{
        color: {OFF_WHITE};
        background: transparent;
    }}

QLabel#tutorialBaseText {{
        color: {GRAY};
        background: transparent;
    }}

QLabel#stroopTutorialTip {{
        color: {FONT_PRIMARY};
        background: transparent;
    }}

QWidget#keyWidget[compact="true"] {{
        background-color: {BACKGROUND_KEY_CHIP};
        border-radius: 10px;
        padding: 6px 10px;
    }}

QWidget#keyWidget[compact="true"] QLabel#keyLabel {{
        color: {OFF_WHITE};
        background: transparent;
    }}

QWidget#tutorialCard {{
        background-color: {BACKGROUND_GLASS};
        border-radius: 15px;
    }}

QLabel#practiceTutorialTitle {{
        color: {OFF_WHITE};
        background: transparent;
    }}

QLabel#practiceTutorialStep {{
        color: #B5B5B5;
        background: transparent;
    }}

QLabel#practiceTutorialAdvice {{
        color: {OFF_WHITE};
        background: transparent;
    }}

QStackedWidget#practiceTutorialPages {{
        background-color: #151515;
        border: 1px solid {OFF_WHITE};
        border-radius: 20px;
    }}

QLabel#practiceTutorialStimul {{
        background: transparent;
    }}

QLabel#practiceTutorialAnswerLabel {{
        color: #B5B5B5;
        background: transparent;
    }}

QLabel#practiceTutorialAnswerText {{
        background: transparent;
    }}

QPushButton#practiceTutorialButton {{
        color: {OFF_WHITE};
        border: none;
        border-radius: 15px;
        padding: 8px 40px;
        background-color: {PRIMARY};
    }}

QPushButton#practiceTutorialButton:hover {{
        background-color: {HOVER_PRIMARY};
    }}

QPushButton#tutorialDot {{
        background-color: rgba(217, 217, 217, 0.5);
        border: none;
        border-radius: 4px;
    }}

QPushButton#tutorialDot[active="true"] {{
        background-color: {FONT_PRIMARY};
    }}
"""