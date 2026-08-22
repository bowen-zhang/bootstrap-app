import uuid

from protos import account_pb


class AccountStorage:
    def __init__(self):
        self._accounts: dict[str, account_pb.Account] = {}

    def create_account(self, account: account_pb.Account) -> account_pb.Account:
        account.id = str(uuid.uuid4())
        self._accounts[account.email] = account
        return account

    def update(self, account: account_pb.Account) -> None:
        if account.email not in self._accounts:
            raise ValueError("Account does not exist")
        self._accounts[account.email] = account

    def get_by_email(self, email: str) -> account_pb.Account | None:
        return self._accounts.get(email)

    def get_by_id(self, account_id: str) -> account_pb.Account | None:
        for account in self._accounts.values():
            if account.id == account_id:
                return account
        return None

    def delete_by_email(self, email: str) -> None:
        self._accounts.pop(email, None)


account_storage = AccountStorage()
