from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QPushButton

from app.models.user import User

from app.utils.logger import get_logger
from app.utils.breadcrumbs import add_breadcrumb
from app.utils.logger import set_user_context
from app.utils.crash_handler import set_active_view
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
        
        self.setWindowTitle("Synapso")

        # set initial window size and properties
        self.resize(1000, 800)
        
        # remove title bar and window frame
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint)
        
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

        # set close button
        self.set_close_button()


        # app-level navigation
        self.loginWidget.start_registration.connect(self._start_registration_flow)
        self.loginWidget.forgot_password_signal.connect(self._go_to_forgot_password)

        logger.info("Views, controllers, and signal connections initialized")
        add_breadcrumb("app", "Main window initialized")

        # attempt refreshing the remembered user or show the login screen
        try:
            user = refresh_up()

            if user and user.id:
                logger.info("Session restored for user (user_id: ..%s)", user.id[-10:])
                add_breadcrumb("auth", "Session restored", user_id=user.id[-10:])
                self.openApp(user)
                return

            self._start_login_flow()

        except Exception as e:
            logger.exception("Session refresh failed: %s", e)
            add_breadcrumb("auth", "Session refresh failed", error=str(e))
            self._start_login_flow()

    # show the login screen
    def _start_login_flow(self):
        logger.info("Login flow started")
        set_active_view("login")
        add_breadcrumb("nav", "Login flow started")
        set_central_widget(self, self.loginWidget)

    # show the registration flow starting with personal info step
    def _start_registration_flow(self):
        set_central_widget(self, self.registerPersonalWidget)
        set_active_view("register_personal")
        add_breadcrumb("nav", "Registration flow started")
        logger.info("Registration flow started")
    
    # go to forgot password screen
    def _go_to_forgot_password(self):
        set_central_widget(self, self.forgotPasswordWidget)
        set_active_view("forgot_password")
        add_breadcrumb("nav", "Forgot password flow started")
        logger.info("Forgot password flow started")

    # return to the login screen
    def _back_to_login(self):
        set_central_widget(self, self.loginWidget)
        set_active_view("login")
        add_breadcrumb("nav", "Returned to login")
        logger.info("Returned to login screen")

    # return to the personal screen
    def _back_to_personal(self):
        set_central_widget(self, self.registerPersonalWidget)
        set_active_view("register_personal")
        logger.info("Returned to personal registration step")

    # go to the auth screen
    def _go_to_register_auth(self):
        set_central_widget(self, self.registerAuthWidget)
        set_active_view("register_auth")
        logger.info("Navigated to auth registration step")

    def set_close_button(self):
        self._close_btn = QPushButton("✕", self)
        self._close_btn.setObjectName("closeBtnOverlay")
        self._close_btn.setFixedSize(42, 42)
        self._close_btn.clicked.connect(self.close)
        self._close_btn.raise_()
        self._reposition_close_btn()
 
    # show a app view
    def openApp(self, user: "User"):
        set_user_context(user.id)
        add_breadcrumb("auth", "User logged in", user_id=user.id[-10:])
        set_active_view("dashboard")

        old_widget = getattr(self, "appWidget", None)
        if old_widget is not None:
            old_widget.cleanup()

        self.appWidget = AppWidget(user, parent=self)
        self.appWidget.logout_requested.connect(self._logoutController.logout)

        start_heartbeat(user.id)
        set_central_widget(self, self.appWidget)
        logger.info("App view opened for user (user_id: ..%s)", user.id[-10:])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_close_btn()

    def _reposition_close_btn(self):
        if hasattr(self, "_close_btn"):
            self._close_btn.move(self.width() - 50, 6)
            self._close_btn.raise_()

    # clean up threads and resources on app close
    def closeEvent(self, event):
        logger.info("Application shutdown started")
        add_breadcrumb("app", "Application shutdown started")

        for controller in (
            getattr(self, "_registrationController", None),
            getattr(self, "_forgotPasswordController", None),
            getattr(self, "_loginController", None),
        ):
            if controller and hasattr(controller, "cleanup"):
                try:
                    controller.cleanup()
                except Exception as e:
                    logger.error("Cleanup error in %s: %s", controller.__class__.__name__, e)

        logger.info("Application shutdown completed")
        add_breadcrumb("app", "Application shutdown completed")
        event.accept()
        super().closeEvent(event)