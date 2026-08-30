import pytest

from app.domain.credits import CreditAccount, InsufficientCredits


def test_failed_export_never_charges() -> None:
    account = CreditAccount()
    account.grant("purchase:1", 2)
    assert not account.charge_successful_export("failed", "project", successful=False)
    assert account.balance == 2


def test_retry_and_same_project_reexport_never_double_charge() -> None:
    account = CreditAccount()
    account.grant("purchase:1", 2)
    assert account.charge_successful_export("export:1", "project:1", successful=True)
    assert not account.charge_successful_export("export:1", "project:1", successful=True)
    assert not account.charge_successful_export("export:2", "project:1", successful=True)
    assert account.balance == 1


def test_paid_export_requires_credit() -> None:
    with pytest.raises(InsufficientCredits):
        CreditAccount().charge_successful_export("export", "project", successful=True)


def test_purchase_callback_and_reconciliation_are_idempotent() -> None:
    account = CreditAccount()
    assert account.grant("purchase:callback", 3)
    assert not account.grant("purchase:callback", 3)
    assert account.reconcile("reconcile:1", -1)
    assert not account.reconcile("reconcile:1", -1)
    assert account.balance == 2
