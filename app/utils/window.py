from PySide6.QtWidgets import QApplication, QWidget

"""Provide main window utilities, such as:
- window_resize: resize and center the main window
- set_central_widget: safely replace the central widget preserving size
"""


# resize current window with and center it

def window_resize(window: QWidget, new_width: int, new_height: int):
    screen = window.screen() or QApplication.primaryScreen()
    if screen is None:
        window.resize(new_width, new_height)
        return

    geo = screen.availableGeometry()

    x = geo.x() + (geo.width() - new_width) // 2
    y = geo.y() + (geo.height() - new_height) // 2

    window.resize(new_width, new_height)
    window.move(x, y)


# safely swap the central widget of the main window, preserving size if possible
def set_central_widget(window, widget: QWidget):
    old = window.centralWidget()

    if old is not None:
        if old.width() or old.height():
            widget.resize(old.size())
        old.hide()
        old.setParent(None)

    window.setCentralWidget(widget)
    widget.show()