"""Single owner of wiki access and editing rules, shared by writes and UI flags."""
from ..core.errors import AppError
from ..identity.authorization import is_administrator, is_employee, require_administrator, require_employee
from ..identity.dto import Principal
from .entities import WikiPage


def require_read(principal: Principal) -> None:
    require_employee(principal, code='wiki_employee_required', message='직원 계정으로 위키를 이용해 주세요.')


def can_protect(principal: Principal) -> bool:
    return is_administrator(principal)


def can_edit(principal: Principal, page: WikiPage) -> bool:
    return is_employee(principal) and (not page.is_locked or can_protect(principal))


def require_edit(principal: Principal, page: WikiPage) -> None:
    require_read(principal)
    if not can_edit(principal, page):
        raise AppError(403, 'wiki_locked', '관리자가 보호한 문서입니다. 작성한 내용은 보존하고 관리자에게 문의해 주세요.')


def require_protect(principal: Principal) -> None:
    require_read(principal)
    require_administrator(principal, code='wiki_admin_required', message='문서 보호와 해제는 관리자만 할 수 있습니다.')


def require_version(page: WikiPage, expected: int) -> None:
    if page.version != expected:
        raise AppError(409, 'wiki_version_conflict', '문서 또는 보호 상태가 변경됐습니다. 입력은 유지하고 최신 판본과 비교해 주세요.',
                       details={'currentVersion': page.version, 'currentRevisionId': page.current_revision_id})
