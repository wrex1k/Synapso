"""Controller for handling profile view interactions (edit profile, change password, delete account)."""

from typing import Callable, Optional

from PySide6.QtCore import QObject, Slot

from app.core.registry import registry
from app.service.auth_service import change_password, delete_account
from app.service.activity_service import stop_heartbeat
from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.repository.user_repository import save_user, delete_user, upload_avatar_blob, check_username_exists
from app.repository.supabase_client import get_client
from app.utils.validator import validate_username, validate_birthdate, validate_password, validate_passwords_match
from translations.translation import translate


class ProfileController(QObject):
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
        self._avatar_operation = registry.operation("profile_upload_avatar")

        self.view.save_profile_requested.connect(self.save_profile)
        self.view.change_password_requested.connect(self.change_password)
        self.view.delete_account_requested.connect(self.delete_account)
        self.view.upload_avatar_requested.connect(self.upload_avatar)

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

        old_username = self.user.username
        old_birthday = self.user.birthday_date

        self.user.username = username
        self.user.birthday_date = birthday
        user_dict = self.user.to_dict()

        def _save():
            if username != old_username and check_username_exists(username):
                return (False, "username_taken")
            save_user(user_dict)
            return (True, None)

        def _done(result):
            if isinstance(result, tuple) and not result[0]:
                self.user.username = old_username
                self.user.birthday_date = old_birthday
                _, err_msg = result
                if err_msg == "username_taken":
                    self.view.set_profile_feedback(translate("ProfileView", "Username is already taken"), is_error=True)
                else:
                    self.view.set_profile_feedback(translate("ProfileView", "Failed to save profile"), is_error=True)
                return
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

        stop_heartbeat()
        logger.info("delete_account: heartbeat stopped on main thread (user ..%s)", user_id[-10:])

        def _delete():
            logger.info("delete_account: deleting public rows (user ..%s)", user_id[-10:])
            delete_user(user_id)
            logger.info("delete_account: public rows removed, invoking edge function (user ..%s)", user_id[-10:])
            return delete_account(user_id)

        def _done(result):
            if result is None:
                logger.error("delete_account: worker raised an unexpected exception (user ..%s)", user_id[-10:])
                self.view.set_profile_feedback(translate("ProfileView", "Failed to delete account"), is_error=True)
                return
            ok, err = result
            if ok:
                logger.info("delete_account: account deletion complete, navigating to login (user ..%s)", user_id[-10:])
                if self.on_logout:
                    self.on_logout()
            else:
                logger.error("delete_account failed: %s", err)
                self.view.set_profile_feedback(translate("ProfileView", "Failed to delete account"), is_error=True)

        started = self._delete_operation.start(
            registry.run_thread,
            _delete,
            _done,
            name="profile-delete-account-thread",
        )
        if started:
            logger.info("delete_account: worker thread started (user ..%s)", user_id[-10:])

    @Slot(bytes)
    def upload_avatar(self, image_bytes: bytes):
        user_id = self.user.id

        def _upload():
            path = upload_avatar_blob(user_id, image_bytes)
            if path:
                get_client().table("users").update({"avatar_path": path}).eq("id", user_id).execute()
            return path

        def _done(avatar_path):
            if avatar_path:
                self.user.avatar_path = avatar_path
                self.user.avatar_blob = image_bytes
                self.navbar.set_avatar_bytes(image_bytes)
                self.view.set_profile_feedback(translate("ProfileView", "Profile photo updated"))
                self.view.avatar_upload_succeeded.emit(image_bytes)
                logger.info("Avatar uploaded for user ..%s", user_id[-10:])
            else:
                self.view.set_profile_feedback(translate("ProfileView", "Failed to upload photo"), is_error=True)
                logger.error("Avatar upload failed for user ..%s", user_id[-10:])

        started = self._avatar_operation.start(
            registry.run_thread,
            _upload,
            _done,
            name="profile-avatar-thread",
        )
        if started:
            logger.info("Uploading avatar for user ..%s", user_id[-10:])
