from sqlalchemy import select
from .entities import User


class UserRepository:
    def __init__(self, session):
        self.session = session

    async def get(self, user_id):
        return await self.session.get(User, user_id)

    async def by_username(self, username):
        return await self.session.scalar(select(User).where(User.username == username))
