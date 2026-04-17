from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

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

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "username": self.username,
        }
        
        if self.birthday_date:
            data["birthday_date"] = self.birthday_date.isoformat()

        if self.avatar_path:
            data["avatar_path"] = self.avatar_path

        return data