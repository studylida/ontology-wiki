"""Shared principal predicates. Resource ownership/protection stays in its domain."""
from .dto import Principal
from ..core.errors import AppError


def is_employee(principal: Principal) -> bool:
    return principal.kind == 'user'


def is_administrator(principal: Principal) -> bool:
    # A service account with a role label must not inherit employee privileges.
    return is_employee(principal) and principal.role == 'admin'


def require_employee(principal: Principal, *, code='employee_required',
                     message='직원 계정으로 이용해 주세요.') -> None:
    if not is_employee(principal):
        raise AppError(403, code, message)


def require_administrator(principal: Principal, *, code='admin_required',
                          message='관리자만 수행할 수 있습니다.') -> None:
    if not is_administrator(principal):
        raise AppError(403, code, message)
