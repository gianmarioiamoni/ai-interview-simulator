# services/replanning/role_expansion_strategy.py

from domain.contracts.user.role import RoleType


class RoleExpansionStrategy:

    # =====================================================
    # PUBLIC
    # =====================================================

    def expand(
        self,
        role: RoleType,
    ) -> list[RoleType]:

        expansions: dict[
            RoleType,
            list[RoleType],
        ] = {
            RoleType.BACKEND_ENGINEER: [
                RoleType.FULLSTACK_ENGINEER,
                RoleType.DEVOPS_ENGINEER,
            ],
            RoleType.FRONTEND_ENGINEER: [
                RoleType.FULLSTACK_ENGINEER,
            ],
            RoleType.DEVOPS_ENGINEER: [
                RoleType.BACKEND_ENGINEER,
                RoleType.FULLSTACK_ENGINEER,
            ],
        }

        return expansions.get(
            role,
            [],
        )
