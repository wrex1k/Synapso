from app.ui.styles.colors import *

STATISTICS_STYLES = f"""
QWidget#statisticsView {{
    background-color: transparent;
}}

QLabel#gameDescription {{
    color: {GRAY};
}}

QWidget#statOverviewCard,
QWidget#statChartCard,
QWidget#statGameCard {{
    background-color: {BACKGROUND_GLASS};
    border-radius: 20px;
}}

QLabel#statOverviewValue {{
    color: {OFF_WHITE};
}}

QLabel#statOverviewSubtext {{
    color: {GRAY};
}}

QLabel#statChartTitle {{
    color: {OFF_WHITE};
}}

QLabel#statChartSubtitle {{
    color: {GRAY};
}}

QLabel#statGameMetricLabel {{
    color: {GRAY};
}}

QLabel#statGameMetricValue {{
    color: {OFF_WHITE};
}}

QFrame#statDivider {{
    background-color: rgba(255, 255, 255, 0.08);
    min-height: 1px;
    max-height: 1px;
    border: none;
}}

QWidget#statOverviewCard,
QWidget#statChartCard,
QWidget#statGameCard {{
    border: 1px solid {BORDER_LIGHTGREY};
}}

QLabel#trendHoverLabel {{
    color: {OFF_WHITE};
}}
"""