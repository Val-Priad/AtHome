from domain.user.user_repository import UserRepository


class MeService:
    def __init__(
        self,
        user_repository: UserRepository,
    ):
        self.user_repository = user_repository
