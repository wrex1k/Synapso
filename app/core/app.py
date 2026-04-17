from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QPushButton

from app.models.user import User

from app.utils.logger import get_logger, set_user_context
from app.utils.crash_handler import set_active_view
from app.utils.window import set_central_widget
from app.service.auth_service import refresh_up
from app.service.activity_service import start_heartbeat
from app.utils.scaling import set_main_window

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
    """Main application window managing authentication and navigation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle("Synapso")

        set_main_window(self)
        self._last_resize_size = None

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.loginWidget = LoginAuth(self)  
        self.loginWidget.hide()
 
        self.registerPersonalWidget = RegisterPersonal(self)
        self.registerPersonalWidget.hide()
        
        self.registerAuthWidget = RegisterAuth(self)
        self.registerAuthWidget.hide()

        self.forgotPasswordWidget = ForgotPassword(self)
        self.forgotPasswordWidget.hide()

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
            on_back=self._back_to_login,
            parent=self
        )

        self.setStyleSheet(get_full_stylesheet())
        self.set_close_button()
        self.loginWidget.start_registration.connect(self._start_registration_flow)
        self.loginWidget.forgot_password_signal.connect(self._go_to_forgot_password)

        logger.info("Views, controllers, and signal connections initialized")

        try:
            user = refresh_up()

            if user and user.id:
                logger.info("Session restored for user (user_id: ..%s)", user.id[-10:])
                self.openApp(user)
                return

            self._start_login_flow()

        except Exception as e:
            logger.exception("Session refresh failed: %s", e)
            self._start_login_flow()

    def _start_login_flow(self):
        """Show the login screen."""
        logger.info("Login flow started")
        set_active_view("login")
        set_central_widget(self, self.loginWidget)

    def _start_registration_flow(self):
        """Show registration flow starting with personal info."""
        set_central_widget(self, self.registerPersonalWidget)
        set_active_view("register_personal")
        logger.info("Registration flow started")

    def _go_to_forgot_password(self):
        """Navigate to forgot password screen."""
        set_central_widget(self, self.forgotPasswordWidget)
        set_active_view("forgot_password")
        logger.info("Forgot password flow started")

    def _back_to_login(self):
        """Return to the login screen."""
        set_central_widget(self, self.loginWidget)
        set_active_view("login")
        logger.info("Returned to login screen")

    def _back_to_personal(self):
        """Return to personal registration step."""
        set_central_widget(self, self.registerPersonalWidget)
        set_active_view("register_personal")
        logger.info("Returned to personal registration step")

    def _go_to_register_auth(self):
        """Navigate to auth registration step."""
        set_central_widget(self, self.registerAuthWidget)
        set_active_view("register_auth")
        logger.info("Navigated to auth registration step")

    def set_close_button(self):
        """Create and position frameless window close button."""
        self._close_btn = QPushButton("✕", self)
        self._close_btn.setObjectName("closeBtnOverlay")
        self._close_btn.setFixedSize(42, 42)
        self._close_btn.clicked.connect(self.close)
        self._close_btn.raise_()
        self._reposition_close_btn()

    def openApp(self, user: "User"):
        """Open main app view for authenticated user."""
        set_user_context(user.id)
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
        """Handle window resize and update UI scaling."""
        super().resizeEvent(event)
        self._reposition_close_btn()
        
        new_size = (self.width(), self.height())
        if self._last_resize_size is None or \
           abs(new_size[0] - self._last_resize_size[0]) > 50 or \
           abs(new_size[1] - self._last_resize_size[1]) > 50:
            self._last_resize_size = new_size
            self.setStyleSheet(get_full_stylesheet())
            
            app_widget = getattr(self, "appWidget", None)
            if app_widget:
                sidebar = getattr(app_widget, "sidebarWidget", None)
                if sidebar:
                    sidebar.update_icon_sizes()
                games = app_widget._page_instances.get("games")
                if games:
                    games.refresh_leaderboard_layout()

    def _reposition_close_btn(self):
        """Reposition close button in top-right corner."""
        if hasattr(self, "_close_btn"):
            self._close_btn.move(self.width() - 50, 6)
            self._close_btn.raise_()

    def closeEvent(self, event):
        """Clean up controllers and threads on close."""
        logger.info("Application shutdown started")

        for controller in (
            getattr(self, "_registrationController", None),
            getattr(self, "_forgotPasswordController", None),
            getattr(self, "_loginController", None),
            getattr(self, "_logoutController", None),
        ):
            if controller and hasattr(controller, "cleanup"):
                try:
                    controller.cleanup()
                except Exception as e:
                    logger.error("Cleanup error in %s: %s", controller.__class__.__name__, e)

        app_widget = getattr(self, "appWidget", None)
        if app_widget and hasattr(app_widget, "cleanup"):
            try:
                app_widget.cleanup()
            except Exception as e:
                logger.error("Cleanup error in appWidget: %s", e)

        logger.info("Application shutdown completed")
        event.accept()
        super().closeEvent(event)