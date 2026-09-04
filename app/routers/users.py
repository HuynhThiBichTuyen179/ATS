from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.id_generator import generate_business_id
from app.core.security import hash_password
from app.deps.rbac import require_hr_manager_or_admin, require_hr_or_above
from app.models.department import Department
from app.models.enums import UserRole, UserStatus
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserOut, UserUpdateRequest
from app.services import audit_service

router = APIRouter(prefix="/users", tags=["users"])

# UC-A01 (v2 Phan 21.5) - Admin quan ly toan bo user; HR Manager chi tao/xem
# duoc HR (khop RBAC 4.1 "User & HR Management": HR Manager "Xem & phan cong
# HR", Admin "Full quyen User"). v2.2: ap dung lai dung ranh gioi nay cho
# Sua/Xoa (deactivate) - HR Manager KHONG duoc dong voi HR_MANAGER/ADMIN khac.
_ROLES_HR_MANAGER_CAN_CREATE = {UserRole.HR}
_ROLES_ADMIN_CAN_CREATE = {UserRole.HR, UserRole.HR_MANAGER, UserRole.ADMIN}


def _to_out(db: Session, user: User) -> UserOut:
    department = db.get(Department, user.department_id) if user.department_id else None
    return UserOut(
        business_id=user.business_id,
        full_name=user.full_name,
        email=user.email,
        role=user.role.value,
        status=user.status.value,
        department_business_id=department.business_id if department else None,
    )


def _check_manage_scope(actor: User, target_role: UserRole, error_code: str = "NOT_ALLOWED_TO_MANAGE_THIS_ROLE") -> None:
    allowed = _ROLES_ADMIN_CAN_CREATE if actor.role == UserRole.ADMIN else _ROLES_HR_MANAGER_CAN_CREATE
    if target_role not in allowed:
        raise HTTPException(status.HTTP_403_FORBIDDEN, error_code)


@router.post("", response_model=UserOut)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    try:
        role = UserRole(payload.role)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_ROLE")

    _check_manage_scope(current_user, role, error_code="NOT_ALLOWED_TO_CREATE_THIS_ROLE")

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "EMAIL_ALREADY_REGISTERED")

    department_id = None
    if payload.department_business_id:
        department = db.query(Department).filter(Department.business_id == payload.department_business_id).first()
        if not department:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "DEPARTMENT_NOT_FOUND")
        department_id = department.id

    user = User(
        business_id=generate_business_id(db, "user"),
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=role,
        department_id=department_id,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    audit_service.log(
        db, actor=current_user, action="HR_USER_CREATED",
        entity_type="user", entity_business_id=user.business_id,
        after={"email": user.email, "role": user.role.value},
    )
    db.commit()
    db.refresh(user)
    return _to_out(db, user)


@router.get("/interviewers", response_model=list[UserOut])
def list_interviewers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    """Danh sach noi bo co the duoc chon lam nguoi phong van (HR/HR_MANAGER/
    ADMIN deu duoc chon - khop interview_service cho phep bat ky role khac
    CANDIDATE lam interviewer). Rieng biet voi GET /users (chi HR_MANAGER/
    ADMIN, mang y nghia "quan ly tai khoan noi bo") de KHONG mo rong quyen
    quan ly cho HR - day chi la 1 danh sach xem de chon, khong lam duoc gi
    khac voi ket qua tra ve. BUG FIX: truoc day form 'Them lich phong van'
    goi thang GET /users (chi HR_MANAGER/ADMIN) de do dropdown nguoi phong
    van - HR mo modal nay bi 403 ngam (frontend nuot loi), dropdown luon rong,
    khong chon duoc ai ca dai voi vai tro HR bat ke ho co quyen tao Interview.
    Phai khai bao TRUOC route "/{user_business_id}" ben duoi, neu khong
    FastAPI se hieu "interviewers" la 1 gia tri user_business_id.
    """
    users = db.query(User).filter(User.role != UserRole.CANDIDATE, User.status == UserStatus.ACTIVE).order_by(User.full_name).all()
    return [_to_out(db, u) for u in users]


@router.get("", response_model=list[UserOut])
def list_users(
    role: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    query = db.query(User).filter(User.role != UserRole.CANDIDATE)
    if role:
        try:
            query = query.filter(User.role == UserRole(role))
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_ROLE")
    return [_to_out(db, u) for u in query.order_by(User.id).all()]


@router.get("/{user_business_id}", response_model=UserOut)
def get_user(
    user_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    user = db.query(User).filter(User.business_id == user_business_id, User.role != UserRole.CANDIDATE).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND")
    return _to_out(db, user)


@router.put("/{user_business_id}", response_model=UserOut)
def update_user(
    user_business_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    user = db.query(User).filter(User.business_id == user_business_id, User.role != UserRole.CANDIDATE).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND")
    _check_manage_scope(current_user, user.role)

    before = {"full_name": user.full_name, "phone": user.phone, "status": user.status.value}
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.department_business_id is not None:
        department = db.query(Department).filter(Department.business_id == payload.department_business_id).first()
        if not department:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "DEPARTMENT_NOT_FOUND")
        user.department_id = department.id
    if payload.status is not None:
        try:
            user.status = UserStatus(payload.status)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_STATUS")

    db.flush()
    audit_service.log(
        db, actor=current_user, action="HR_USER_UPDATED",
        entity_type="user", entity_business_id=user.business_id,
        before=before, after={"full_name": user.full_name, "phone": user.phone, "status": user.status.value},
    )
    db.commit()
    db.refresh(user)
    return _to_out(db, user)


@router.delete("/{user_business_id}")
def deactivate_user(
    user_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    """Section 14: uu tien Deactivate (status=INACTIVE) thay vi hard delete -
    khong bao gio xoa vat ly de khong mat Audit/Application/Job/Interview/
    Offer/Email history da gan voi user nay."""
    user = db.query(User).filter(User.business_id == user_business_id, User.role != UserRole.CANDIDATE).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND")
    _check_manage_scope(current_user, user.role)
    if user.id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CANNOT_DEACTIVATE_SELF")

    before = {"status": user.status.value}
    user.status = UserStatus.INACTIVE
    db.flush()
    audit_service.log(
        db, actor=current_user, action="HR_USER_DELETED",
        entity_type="user", entity_business_id=user.business_id,
        before=before, after={"status": user.status.value},
        reason="Soft-delete (INACTIVE)",
    )
    db.commit()
    return {"business_id": user.business_id, "status": user.status.value}
