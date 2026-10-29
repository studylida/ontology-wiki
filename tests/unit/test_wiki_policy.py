"""Domain permissions and advertised UI flags must not diverge."""
from types import SimpleNamespace
import pytest
from knowledge.core.errors import AppError
from knowledge.identity.authorization import is_administrator, is_employee
from knowledge.identity.dto import Principal
from knowledge.wiki.policy import can_edit, can_protect, require_edit, require_protect, require_read, require_version


@pytest.mark.parametrize('kind,role', [('user', 'user'), ('user', 'admin'), ('service', 'user'), ('service', 'admin')])
@pytest.mark.parametrize('locked', [False, True])
def test_flags_and_write_checks_share_policy(kind, role, locked):
    actor = Principal(id='actor', username='actor', kind=kind, role=role)
    page = SimpleNamespace(is_locked=locked, version=3, current_revision_id='r3')
    employee, admin = kind == 'user', kind == 'user' and role == 'admin'
    editable = employee and (not locked or admin)
    assert is_employee(actor) == employee
    assert is_administrator(actor) == admin
    assert can_edit(actor, page) == editable
    assert can_protect(actor) == admin
    for allowed, check in ((employee, lambda: require_read(actor)),
                           (editable, lambda: require_edit(actor, page)),
                           (admin, lambda: require_protect(actor))):
        if allowed:
            check()
        else:
            with pytest.raises(AppError) as error:
                check()
            assert error.value.status_code == 403


def test_content_or_protection_change_invalidates_previous_base():
    page = SimpleNamespace(version=3, current_revision_id='r2')
    require_version(page, 3)
    with pytest.raises(AppError) as error:
        require_version(page, 2)
    assert error.value.status_code == 409
    assert error.value.details == {'currentVersion': 3, 'currentRevisionId': 'r2'}
