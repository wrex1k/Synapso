@echo off
cd /d C:\Users\pohan\Desktop\Synapso

del app\ui\authPage_ui.py 2>nul
del app\ui\appWidget_ui.py 2>nul

pyside6-uic app\ui\authPage.ui -o app\ui\authPage_ui.py

pyside6-uic app\ui\appWidget.ui -o app\ui\appWidget_ui.py

pyside6-rcc resources\resources.qrc -o resources_rc.py

python -m main

pause


