from enum import Enum


class UserRole(str, Enum):
	ANONYMOUS = 'anonymous'
	FREE = 'free'
