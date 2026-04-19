from pydantic import BaseModel, ConfigDict

from domain.value_objects.user_id import UserId
from domain.value_objects.user_role import UserRole


class AuthUser(BaseModel):
	model_config = ConfigDict(frozen=True)

	user_id: UserId
	role: UserRole
