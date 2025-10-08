from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    EDITOR = "editor"
    ADMIN = "admin"