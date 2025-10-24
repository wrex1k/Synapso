from typing import Any, Dict, Optional
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QTimer

from app.views.login_auth import LoginAuth
from app.views.app_widget import AppWidget
from app.views.register_auth import RegisterAuth
from app.views.register_personal import RegisterPersonal
from app.auth.supabase_auth import (sign_in, sign_up, refresh_session, logout as supabase_logout)
from app.store.supabase_store import (upload_avatar_blob, upsert_public_users, fetch_public_user)
from app.store.user_activity import send_heartbeat
from app.utils import show_error, set_central_widget, set_enabled_safe
import datetime


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synapso")

        # hold data for multistep registration
        self.registration_data: Dict[str, Any] = {}
        self.app: Optional[AppWidget] = None
        
        # initialize the views once
        self.login_auth = LoginAuth()
        self.register_personal = RegisterPersonal()
        self.register_auth = RegisterAuth()

        # connect view signals
        self.login_auth.auth_login_data.connect(self.do_login)
        self.login_auth.switch_to_register_signal.connect(self.start_registration_flow)

        self.register_personal.personal_data.connect(self.on_register_personal_data)
        self.register_personal.back_requested.connect(self.back_to_login)

        self.register_auth.auth_data.connect(self.on_register_auth_data)
        self.register_auth.back_requested.connect(self.back_to_personal)

        # try to refresh session on startup and show appropriate view
        session = refresh_session()
        if session:
            user_row = fetch_public_user(session.user.id)
            if user_row:
                self.on_user_authenticated(session.user.id)
            else:
                set_central_widget(self, self.login_auth, 1000, 800)
        else:
            set_central_widget(self, self.login_auth, 1000, 800)

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
            show_error(self.login_auth.ui.signInButton, "Login failed")
            return
        
        # on successful login, call authenticated handler
        self.on_user_authenticated(user.id)

    # start registration flow
    def start_registration_flow(self):
        self.show_view(self.register_personal, 1000, 800)

    # when personal data is ready, show auth page
    def on_register_personal_data(self, username: str, email: str, birthday_date: datetime.date, blob: bytes):
        self.registration_data = {
            'username': username,
            'email': email,
            'birthday_date': birthday_date,
            'blob': blob
        }
        self.show_view(self.register_auth, 1000, 800)

    # when auth data is ready, complete registration
    def on_register_auth_data(self, password: str):
        self.registration_data['password'] = password
        self.do_register()

    # perform registration
    def do_register(self):
        if getattr(self, "_registering", False):
            return
        self._registering = True
        try:
            username = self.registration_data['username']
            email = self.registration_data['email']
            password = self.registration_data['password']
            birthday_date = self.registration_data['birthday_date']
            blob = self.registration_data.get('blob')

            user = sign_up(email, password)

            if not user:
                show_error(self.register_auth.ui.signUpButton, "Registration failed")
                return

            try:
                avatar_path = upload_avatar_blob(user.id, blob, "avatar.png") if blob else None
            except Exception as e:
                print(f"[WARN] Avatar upload failed: {e}")

            try:
                upsert_public_users(user.id, username=username, birthday_date=birthday_date, avatar_path=avatar_path)
            except Exception as e:
                print(f"[WARN] profile upsert failed: {e}")

            # on successful registration, call authenticated handler
            self.on_user_authenticated(user.id)

            # clear registration data
            self.registration_data.clear()

        except Exception as e:
            print(f"Registration error: {e}")
            show_error(self.register_auth.ui.signUpButton, str(e))
        finally:
            self._registering = False
            # safely enable signUpButton if present
            ra_ui = getattr(getattr(self, 'register_auth', None), 'ui', None)
            set_enabled_safe(getattr(ra_ui, 'signUpButton', None), True)

    # handle user authenticated event
    def on_user_authenticated(self, user_id: str):
        self.app = AppWidget(fetch_public_user(user_id))
        set_central_widget(self, self.app, 1400, 900)
        if hasattr(self.app, 'logout_requested'):
            self.app.logout_requested.connect(self.handle_logout)
        self.start_heartbeat_timer(user_id)

    # perform logout
    def do_logout(self):
        if hasattr(self, "heartbeat_timer") and self.heartbeat_timer.isActive():
            self.heartbeat_timer.stop()
            print("[DEBUG] Heartbeat stopped")

        supabase_logout()
        self.registration_data.clear()
        self.show_view(self.login_auth, 1000, 800)

    # show personal information view with prefill
    def show_personal(self, prefill=True):
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

    # show view helper
    def show_view(self, view, width=1000, height=800):
        set_central_widget(self, view, width, height)

    # go back to login page
    def back_to_login(self):
        self.show_login()

    # go back to personal registration page with prefill register data
    def back_to_personal(self):
        self.show_view(self.register_personal, 1000, 800)
        self.show_personal(prefill=True)

    # handle logout request from app widget
    def handle_logout(self):
        self.do_logout()
        if self.app and hasattr(self.app, "ui"):
            set_enabled_safe(self.app.ui.logoutButton, True)

    # send heartbeat timer to update user activity
    def start_heartbeat_timer(self, user_id: str, interval: int = 15000):
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(lambda: send_heartbeat(user_id))
        self.heartbeat_timer.start(interval)
        print(f"[DEBUG] Heartbeat started for {user_id}")