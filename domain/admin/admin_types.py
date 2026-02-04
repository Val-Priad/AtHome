from typing import Literal, TypeAlias

BaseUserSortBy: TypeAlias = Literal[
    "created_at",
    "updated_at",
    "email",
    "name",
    "adv_qty",
    "active_ads_qty",
]
