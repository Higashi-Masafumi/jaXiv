from enum import Enum


class SubscriptionPlan(str, Enum):
	FREE = 'free'
	PAID = 'paid'
