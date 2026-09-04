from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "NOT_AUTHENTICATED")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "INVALID_OR_EXPIRED_TOKEN")
    user = db.query(User).filter(User.business_id == payload["sub"]).first()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "USER_NOT_FOUND")
    return user


def get_current_user_optional(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User | None:
    """dung cho endpoint public co the truy cap ca khi
    chua dang nhap (Job Detail cong khai) NHUNG van can biet actor la ai (neu
    co) de quyet dinh pham vi hien thi (VD Job DRAFT chi HR+ thay duoc, con
    Candidate/anonymous chi thay PUBLISHED) - khac get_current_user() luon
    bat buoc token hop le.
    """
    if token is None:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    return db.query(User).filter(User.business_id == payload["sub"]).first()


def require_roles(*roles: UserRole):
    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_PERMISSION")
        return user

    return _dependency


# Ai co quyen approval Offer (Phan 3 CHANGE 01 - Permission Matrix)
require_offer_approver = require_roles(UserRole.HR_MANAGER, UserRole.ADMIN)
require_hr_or_above = require_roles(UserRole.HR, UserRole.HR_MANAGER, UserRole.ADMIN)
require_hr_manager_or_admin = require_roles(UserRole.HR_MANAGER, UserRole.ADMIN)
# Audit Log: chi ADMIN (BGD) duoc xem - thu hep tu require_hr_manager_or_admin
# theo yeu cau nguoi dung, HR_MANAGER khong con xem duoc nua.
require_admin = require_roles(UserRole.ADMIN)
