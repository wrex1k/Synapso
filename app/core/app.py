from shiboken6 import isValid
from typing import Any, Dict, Optional
from PySide6.QtWidgets import QMainWindow

from app.views.login_auth import LoginAuth
from app.views.app_widget import AppWidget
from app.views.register_auth import RegisterAuth
from app.views.register_personal import RegisterPersonal
from app.auth.supabase_auth import (
    sign_in,
    sign_up,
    refresh_session,
    logout as supabase_logout
)
from app.store.supabase_store import (
    upload_avatar_blob,
    upsert_public_users,
    fetch_public_user
)
from app.utils import show_error, window_resize


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synapso")

        # hold data for multistep registration
        self.registration_data: Dict[str, Any] = {}
        self.app: Optional[AppWidget] = None

        # try to refresh session on startup
        session = refresh_session()
        if session:
            user_row = fetch_public_user(session.user.id)
            self.app = AppWidget(user_row)
            self.setCentralWidget(self.app)
            if hasattr(self.app, 'logout_requested'):
                self.app.logout_requested.connect(self.handle_logout)
            window_resize(self, 1400, 900)
        else:
            self._show_login()

    # safely clean up old widget
    def _cleanup_widget(self, widget_name: str):
        if hasattr(self, widget_name):
            widget = getattr(self, widget_name)
            if widget is not None:
                try:
                    widget.deleteLater()
                except:
                    pass
                setattr(self, widget_name, None)


    # check if widget exists and is valid
    def _is_widget_valid(self, widget_name: str) -> bool:
        if not hasattr(self, widget_name):
            return False
        widget = getattr(self, widget_name)
        return widget is not None and isValid(widget)

    def _enable_button_safely(self, widget_path: str, enabled: bool = True):
        try:
            parts = widget_path.split('.')
            current = self
            
            for part in parts:
                if not hasattr(current, part):
                    return False
                current = getattr(current, part)
                if current is None:
                    return False
            
            if hasattr(current, 'setEnabled'):
                current.setEnabled(enabled)
                return True
        except Exception:
            pass
        return False

    # perform login with email and password
    def do_login(self, email: str, password: str):
        email = (email or "").strip()
        password = (password or "").strip()

        try:
            user = sign_in(email, password)
        except Exception as e:
            print(f"[DEBUG] sign_in exception: {e}")
            show_error(self.login_auth.ui.signInButton, "Invalid password or email")
            return
        if not user:
            print("Supabase login failed")
            show_error(self.login_auth.ui.signInButton, "Login failed")
            return

        self.app = AppWidget(fetch_public_user(user.id))
        self.setCentralWidget(self.app)
        if hasattr(self.app, 'logout_requested'):
            self.app.logout_requested.connect(self.handle_logout)
        window_resize(self, 1400, 900)

    # start registration flow
    def start_registration_flow(self):
        self._show_personal()

    # when personal data is ready, show auth page
    def on_register_personal_data(self, username, email, birthday_date, blob):
        self.registration_data = {
            'username': username,
            'email': email,
            'birthday_date': birthday_date,
            'blob': blob
        }
        self._show_auth()

    # when auth data is ready, complete registration
    def on_register_auth_data(self, password):
        self.registration_data['password'] = password
        self.do_register()

    def do_register(self):
        if getattr(self, "_registering", False):
            return
        self._registering = True
        try:
            needed = ['username', 'email', 'password', 'birthday_date']
            missing = [x for x in needed if x not in self.registration_data]
            if missing:
                show_error(self.register_auth.ui.signUpButton, f"Missing: {', '.join(missing)}")
                return

            username = self.registration_data['username']
            email = self.registration_data['email']
            password = self.registration_data['password']
            birthday_date = self.registration_data['birthday_date']
            blob = self.registration_data.get('blob')

            user = sign_up(email, password)

            if not user:
                show_error(self.register_auth.ui.signUpButton, "Registration failed")
                return

            user_id = user.id

            avatar_path = None
            try:
                avatar_path = upload_avatar_blob(user_id, blob, "avatar.png") if blob else None
            except Exception as e:
                print(f"[WARN] Avatar upload failed: {e}")

            try:
                upsert_public_users(
                    user_id,
                    username=username,
                    birthday_date=birthday_date,
                    avatar_path=avatar_path
                )
            except TypeError:
                upsert_public_users(
                    user_id,
                    username=username,
                    birthday_date=birthday_date
                )
            except Exception as e:
                print(f"[WARN] profile upsert failed: {e}")

            self.app = AppWidget(fetch_public_user(user_id))
            self.setCentralWidget(self.app)
            if hasattr(self.app, 'logout_requested'):
                self.app.logout_requested.connect(self.handle_logout)
            window_resize(self, 1400, 900)

            self.registration_data.clear()

        except Exception as e:
            print(f"Registration error: {e}")
            show_error(self.register_auth.ui.signUpButton, "Registration failed")
        finally:
            self._registering = False
            # Re-enable sign up button safely
            self._enable_button_safely('register_auth.ui.signUpButton', True)

    # perform logout
    def do_logout(self):
        supabase_logout()
        self.registration_data.clear()
        self._cleanup_widget('app')
        self._show_login()

    # show login/welcome page
    def _show_login(self):
        if not self._is_widget_valid('login_auth'):
            self._cleanup_widget('login_auth')
            
            self.login_auth = LoginAuth()
            self.login_auth.auth_login_data.connect(self.do_login)
            self.login_auth.switch_to_register_signal.connect(self.start_registration_flow)
        self.setCentralWidget(self.login_auth)
        window_resize(self, 1000, 800)

    # show personal registration page
    def _show_personal(self, prefill=False):
        if not self._is_widget_valid('register_personal'):
            self._cleanup_widget('register_personal')
                    
            self.register_personal = RegisterPersonal()
            if hasattr(self.register_personal, 'personal_data'):
                self.register_personal.personal_data.connect(self.on_register_personal_data)
            if hasattr(self.register_personal, 'back_requested'):
                self.register_personal.back_requested.connect(self.back_to_login)
        self.setCentralWidget(self.register_personal)
        window_resize(self, 1000, 800)

        # if prefill is True, fill in the fields
        if prefill and self.registration_data:
            data = self.registration_data
            try:
                self.register_personal.ui.usernameEdit.setText(data.get('username',''))
                self.register_personal.ui.emailEdit.setText(data.get('email',''))
                bdate = data.get('birthday_date')
                if bdate and hasattr(bdate, 'year'):
                    self.register_personal.ui.yearBox.setCurrentText(str(bdate.year))
                    if hasattr(bdate, 'month'):
                        self.register_personal.ui.birthMonthBox.setCurrentIndex(bdate.month - 1)
                    if hasattr(bdate, 'day'):
                        self.register_personal.ui.dayBox.setCurrentText(str(bdate.day))
            except Exception:
                pass

    # show auth registration page
    def _show_auth(self):
        if not self._is_widget_valid('register_auth'):
            self._cleanup_widget('register_auth')
                    
            self.register_auth = RegisterAuth()
            if hasattr(self.register_auth, 'auth_data'):
                self.register_auth.auth_data.connect(self.on_register_auth_data)
            if hasattr(self.register_auth, 'back_requested'):
                self.register_auth.back_requested.connect(self.back_to_personal)
        self.setCentralWidget(self.register_auth)
        window_resize(self, 1000, 800)

    # go back to login page
    def back_to_login(self):
        self._show_login()

    # go back to personal registration page
    def back_to_personal(self):
        self._show_personal(prefill=True)

    # handle logout request from app widget
    def handle_logout(self):
        try:
            self.do_logout()
        finally:
            # Re-enable logout button safely
            self._enable_button_safely('app.ui.logoutButton', True)

    #TODO: heartbeat timer to update user activity