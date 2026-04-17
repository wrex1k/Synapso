"""Controller for handling profile view interactions (edit profile, change password, delete account)."""

from typing import Callable, Optional

from PySide6.QtCore import QObject, Slot

from app.core.registry import registry
from app.repository.user_repository import save_user, delete_user
from app.service.auth_service import change_password, delete_account
from app.utils.logger import logger
from app.utils.validator import (
    validate_username,
    validate_birthdate,
    validate_password,
    validate_passwords_match,
)
from translations.translation import translate


class ProfileController(QObject):
    """Bridge between ProfileView and domain/services."""

    def __init__(
        self,
        view,
        user,
        navbar,
        on_logout: Optional[Callable[[], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.view = view
        self.user = user
        self.navbar = navbar
        self.on_logout = on_logout

        self._save_operation = registry.operation("profile_save")
        self._password_operation = registry.operation("profile_change_password")
        self._delete_operation = registry.operation("profile_delete_account")

        self.view.save_profile_requested.connect(self.save_profile)
        self.view.change_password_requested.connect(self.change_password)
        self.view.delete_account_requested.connect(self.delete_account)

    @Slot(str, object)
    def save_profile(self, username: str, birthday):
        err = validate_username(username)
        if err:
            self.view.set_profile_feedback(err, is_error=True)
            return
        if birthday:
            err = validate_birthdate(birthday)
            if err:
                self.view.set_profile_feedback(err, is_error=True)
                return

        self.user.username = username
        self.user.birthday_date = birthday
        user_dict = self.user.to_dict()

        def _save():
            save_user(user_dict)

        def _done(_):
            self.navbar.setName(username)
            self.view.set_profile_feedback(translate("ProfileView", "Profile saved successfully"))
            logger.info("Profile updated for user ..%s", self.user.id[-10:])

        started = self._save_operation.start(
            registry.run_thread,
            _save,
            _done,
            name="profile-save-thread",
        )
        if started:
            logger.info("Saving profile for user ..%s", self.user.id[-10:])

    @Slot(str, str, str)
    def change_password(self, current_pw: str, new_pw: str, confirm_pw: str):
        err = validate_passwords_match(new_pw, confirm_pw)
        if err:
            self.view.set_password_feedback(err, is_error=True)
            return
        err = validate_password(new_pw)
        if err:
            self.view.set_password_feedback(err, is_error=True)
            return

        def _change():
            return change_password(current_pw, new_pw)

        def _done(result):
            ok, err_msg = result
            if ok:
                self.view.set_password_feedback(translate("ProfileView", "Password changed successfully"))
                self.view.clear_password_fields()
            elif err_msg == "wrong_current_password":
                self.view.set_password_feedback(translate("ProfileView", "Current password is incorrect"), is_error=True)
            elif err_msg == "password_same_as_old":
                self.view.set_password_feedback(translate("ProfileView", "New password must differ from the current one"), is_error=True)
            else:
                self.view.set_password_feedback(translate("ProfileView", "Failed to change password"), is_error=True)
                logger.error("change_password error: %s", err_msg)

        started = self._password_operation.start(
            registry.run_thread,
            _change,
            _done,
            name="profile-change-password-thread",
        )
        if started:
            logger.info("Changing password for user ..%s", self.user.id[-10:])

    @Slot()
    def delete_account(self):
        user_id = self.user.id

        def _delete():
            delete_user(user_id)
            return delete_account(user_id)

        def _done(result):
            ok, err = result
            if ok:
                logger.info("Account deleted for user ..%s", user_id[-10:])
                if self.on_logout:
                    self.on_logout()
            else:
                logger.error("delete_account failed: %s", err)

        started = self._delete_operation.start(
            registry.run_thread,
            _delete,
            _done,
            name="profile-delete-account-thread",
        )
        if started:
            logger.info("Deleting account for user ..%s", user_id[-10:])
