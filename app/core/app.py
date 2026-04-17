from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow

from app.models.user import User

from app.utils.logger import get_logger
from app.utils.window import set_central_widget
from app.service.auth_service import refresh_up
from app.service.activity_service import start_heartbeat

from app.ui.views.login_auth import LoginAuth
from app.ui.views.register_personal import RegisterPersonal
from app.ui.views.register_auth import RegisterAuth
from app.ui.views.forgot_password import ForgotPassword
from app.ui.views.app_widget import AppWidget

from app.ui.styles.base import get_full_stylesheet

from app.controller.login_controller import LoginController
from app.controller.registration_controller import RegistrationController
from app.controller.forgot_password_controller import ForgotPasswordController
from app.controller.logout_controller import LogoutController

from app.utils.frameless_window import FramelessWindowMixin

logger = get_logger(__name__)

class App(FramelessWindowMixin, QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # set window title and icon
        self.setWindowTitle("Synapso")
        self.setWindowIcon(QIcon(":/images/graphics/logo.png"))

        # set initial window size and properties
        self.resize(1000, 800)
        
        # remove title bar and window frame
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint)
        
        # enable translucent background for rounded corners
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # create widgets
        self.loginWidget = LoginAuth(self)  
        self.loginWidget.hide()

        self.registerPersonalWidget = RegisterPersonal(self)
        self.registerPersonalWidget.hide()
        
        self.registerAuthWidget = RegisterAuth(self)
        self.registerAuthWidget.hide()

        self.forgotPasswordWidget = ForgotPassword(self)
        self.forgotPasswordWidget.hide()

        # create controllers
        self._loginController = LoginController(
            view=self.loginWidget,
            on_success=self.openApp,
            parent=self
        )

        self._logoutController = LogoutController(
            view=(self.loginWidget, self.registerPersonalWidget),
            on_logout=self._start_login_flow,
            parent=self
        )
    
        self._registrationController = RegistrationController(
            view=(self.registerPersonalWidget, self.registerAuthWidget),
            on_complete=self.openApp,
            on_back_to_login=self._back_to_login,
            on_back_to_personal=self._back_to_personal,
            on_next_to_auth=self._go_to_register_auth,
            parent=self
        )
        
        self._forgotPasswordController = ForgotPasswordController(
            view=self.forgotPasswordWidget,
            on_success=self._back_to_login,
            on_back=self._back_to_login,
            parent=self
        )

        # apply global stylesheet
        self.setStyleSheet(get_full_stylesheet())

        # app-level navigation
        self.loginWidget.start_registration.connect(self._start_registration_flow)
        self.loginWidget.forgot_password_signal.connect(self._go_to_forgot_password)

        # log the app initialization
        logger.info(f"{80 * "-"}")
        logger.info("Views, controllers, and signal connections initializing..")

        # attempt refreshing the remembered user or show the login screen
        try:
            user = refresh_up()

            if user and user.id:
                logger.info("User refreshed successfully..")
                self.openApp(user)
                return

            self._start_login_flow()

        except Exception as e:
            logger.exception("Session refresh failed: %s", e)
            self._start_login_flow()

    # show the login screen
    def _start_login_flow(self):
        logger.info("Login flow started..")
        set_central_widget(self, self.loginWidget)

    # show the registration flow starting with personal info step
    def _start_registration_flow(self):
        set_central_widget(self, self.registerPersonalWidget)
        logger.info("Registration flow started..")
    
    # go to forgot password screen
    def _go_to_forgot_password(self):
        set_central_widget(self, self.forgotPasswordWidget)
        logger.info("Forgot password flow started..")

    # return to the login screen
    def _back_to_login(self):
        set_central_widget(self, self.loginWidget)
        logger.info("Returned to login screen..")

    # return to the personal screen
    def _back_to_personal(self):
        set_central_widget(self, self.registerPersonalWidget)
        logger.info("Returned to personal registration step..")

    # go to the auth screen
    def _go_to_register_auth(self):
        set_central_widget(self, self.registerAuthWidget)
        logger.info("Navigated to auth registration step..")

    # show a app view
    def openApp(self, user: "User"):
        self.appWidget = AppWidget(user, parent=self)
        self.appWidget.logout_requested.connect(self._logoutController.logout)

        start_heartbeat(user.id)
        set_central_widget(self, self.appWidget)

    # clean up threads and resources on app close
    def closeEvent(self, event):
        logger.info("Application closing..")

        for controller in (
            getattr(self, "_registrationController", None),
            getattr(self, "_forgotPasswordController", None),
            getattr(self, "_loginController", None),
        ):
            if controller and hasattr(controller, "cleanup"):
                try:
                    controller.cleanup()
                except Exception as e:
                    logger.error("Cleanup error: %s", e)

        event.accept()
        super().closeEvent(event)