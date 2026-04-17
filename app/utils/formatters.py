from datetime import datetime, timedelta

from app.games.core.base_game import GAME_LABELS
from translations.translation import get_translation_manager, translate

def format_time_duration(seconds: int) -> str:
    """Convert seconds to formatted time string."""
    if not seconds:
        return translate("DashboardView", "0 min")

    hours, rem = divmod(int(seconds), 3600)
    minutes = rem // 60

    if hours:
        return translate("DashboardView", "{hours}h {minutes}m").format(
            hours=hours,
            minutes=minutes,
        )

    return translate("DashboardView", "{minutes} min").format(minutes=minutes)

def format_day_label(count: int) -> str:
    """Format day count with proper pluralization."""
    lang = getattr(get_translation_manager(), "current_language", "en")

    if lang == "en" or str(lang).startswith("en-"):
        return f"{count} day" if count == 1 else f"{count} days"

    txt = translate("DashboardView", "%n day", n=count)
    result = txt.replace("%n", str(count))

    if result.endswith(" day") and not result.endswith(" days") and count != 1:
        return f"{count} days"

    return result

def format_percentage(value: float | None) -> str:
    """Format float as percentage string."""
    if value is None:
        return "0%"
    pct = value * 100 if value <= 1.0 else value
    return f"{pct:.0f}%"


def format_milliseconds(value: float | None) -> str:
    """Format millisecond value for display."""
    if value is None:
        return "0 ms"
    return f"{int(value)} ms"


def format_relative_datetime(dt: datetime | None) -> str:
    """Format datetime relative to now."""
    if dt is None:
        return translate("DashboardView", "No data")

    now = datetime.now().astimezone()

    if dt.date() == now.date():
        return translate("DashboardView", "Today at {time}").format(
            time=dt.strftime("%H:%M")
        )

    if dt.date() == (now.date() - timedelta(days=1)):
        return translate("DashboardView", "Yesterday at {time}").format(
            time=dt.strftime("%H:%M")
        )

    return dt.strftime("%d.%m.%Y • %H:%M")


def format_pi(value: float | int | None) -> str:
    """Format PI value with 2 decimal places."""
    if value is None:
        return translate("DashboardView", "No data")
    return f"{value:.2f} PI"


def format_game_label(slug: str | None) -> str:
    """Format game slug to translated label."""
    if not slug:
        return translate("DashboardView", "No data")
    return translate("DashboardView", GAME_LABELS.get(slug, slug))


def format_float(value: float | None, decimals: int = 2) -> str:
    """Format float value with given decimal places."""
    if value is None:
        return "0"
    return f"{value:.{decimals}f}"


def format_int(value: int | None) -> str:
    """Format integer value for display."""
    if value is None:
        return "0"
    return str(value)
