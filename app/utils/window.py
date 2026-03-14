from PySide6.QtWidgets import QWidget

"""Provide main window utilities, such as:
- window_resize: resize and center the main window
- set_central_widget: safely replace the central widget preserving size
"""


# resize current window with and center it
def window_resize(window: QWidget, new_width: int, new_height: int, lock_size: bool = False):
    screen = window.screen()
    if screen:
        screen_size = screen.size()

        window.setMinimumSize(0, 0)
        window.resize(new_width, new_height)

        if lock_size:
            window.setMinimumSize(new_width, new_height)

        window.move(
            (screen_size.width() - new_width) // 2,
            (screen_size.height() - new_height) // 2,
        )


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