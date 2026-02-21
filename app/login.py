from __future__ import annotations
from .extensions import login_manager
from .models import User

@login_manager.user_loader
def load_user(user_id: str):
    if not user_id or not user_id.isdigit():
        return None
    return User.query.get(int(user_id))
