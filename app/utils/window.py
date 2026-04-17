from PySide6.QtWidgets import QApplication, QWidget

def window_resize(window: QWidget, new_width: int, new_height: int):
    """Resize and center a window on its current screen."""
    screen = window.screen() or QApplication.primaryScreen()
    if screen is None:
        window.resize(new_width, new_height)
        return

    geo = screen.availableGeometry()

    x = geo.x() + (geo.width() - new_width) // 2
    y = geo.y() + (geo.height() - new_height) // 2

    window.resize(new_width, new_height)
    window.move(x, y)

def set_central_widget(window, widget: QWidget):
    """Replace the central widget of a window, cleaning up the old one."""
    old = window.centralWidget()

    if old is not None:
        if old.width() or old.height():
            widget.resize(old.size())
        old.hide()
        old.setParent(None)

    window.setCentralWidget(widget)
    widget.show()

    if hasattr(window, "_reposition_close_btn"):
        window._reposition_close_btn()