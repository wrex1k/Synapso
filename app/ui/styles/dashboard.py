from app.ui.styles.colors import *

DASHBOARD_STYLES = f"""
QWidget#dashboardView {{
    background-color: transparent;
}}

QLabel#gameDescription {{
    color: {GRAY};
}}

QWidget#dashboardHeroCard,
QWidget#dashboardSideCard,
QWidget#dashboardCard {{
    background-color: {BACKGROUND_GLASS};
    border: 1px solid {BORDER_LIGHTGREY};
    border-radius: 20px;
}}

QLabel#dashboardHeroTitle {{
    color: {OFF_WHITE};
}}

QLabel#dashboardHeroSubtitle {{
    color: {GRAY};
}}

QLabel#dashboardInlineStatValue {{
    color: {OFF_WHITE};
}}

QLabel#dashboardInlineStatLabel {{
    color: {GRAY};
}}

QLabel#dashboardCardTitle {{
    color: {OFF_WHITE};
}}

QLabel#dashboardCardSubtitle {{
    color: {GRAY};
}}

QLabel#dashboardGoalValue {{
    color: {OFF_WHITE};
}}

QLabel#dashboardMutedText,
QLabel#dashboardRowSubtitle {{
    color: {GRAY};
}}

QLabel#dashboardHighlightValue {{
    color: {OFF_WHITE};
}}

QLabel#dashboardMetricLabel {{
    color: {GRAY};
}}

QLabel#dashboardMetricValue,
QLabel#dashboardRowValue {{
    color: {OFF_WHITE};
}}

QLabel#dashboardRowTitle {{
    color: {OFF_WHITE};
}}

QLabel#recentGameTitle {{
    color: {PRIMARY_LIGHT};
}}

QPushButton#dashboardPrimaryButton {{
    background-color: {PRIMARY};
    border-radius: 16px;
    min-height: 42px;
    padding: 0 16px;
}}

QPushButton#dashboardPrimaryButton:hover {{
    background-color: {HOVER_PRIMARY};
}}

QPushButton#dashboardPrimaryButton:disabled {{
    background-color: rgba(62, 172, 145, 0.35);
    color: rgba(255, 255, 255, 0.75);
}}

QFrame#dashboardDivider {{
    background-color: rgba(255, 255, 255, 0.08);
    min-height: 1px;
    max-height: 1px;
    border: none;
}}
"""
