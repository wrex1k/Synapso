from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import hashlib


@dataclass
class User:
    id: str = ""
    email: str = ""
    username: str = ""
    birthday_date: Optional[date] = None

    avatar_blob: Optional[bytes] = None
    avatar_path: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def auth_email(self) -> str:
        return self.email.strip()

    def diagnostic_id(self) -> str:
        if not self.id:
            return "anonymous"

        return hashlib.sha256(
            self.id.encode("utf-8")
        ).hexdigest()[:8]

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "username": self.username,
            "birthday_date": self.birthday_date.isoformat(),
        }

        if self.avatar_path:
            data["avatar_path"] = self.avatar_path

        return data