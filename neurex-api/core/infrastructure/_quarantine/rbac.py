"""
core/infrastructure/rbac.py
Implements Role-Based Access Control (RBAC) for the Neurex Mesh.
Defines permissions for local and remote entities.
"""

from __future__ import annotations

import enum

import structlog

log = structlog.get_logger()


class Role(enum.Enum):
    OWNER = "owner"
    CONTRIBUTOR = "contributor"
    GUEST = "guest"
    REMOTE_PEER = "remote_peer"


class Permission(enum.Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE_TERMINAL = "execute_terminal"
    MUTATE_WORKSPACE = "mutate_workspace"
    INITIATE_SWARM = "initiate_swarm"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.OWNER: {
        Permission.READ,
        Permission.WRITE,
        Permission.EXECUTE_TERMINAL,
        Permission.MUTATE_WORKSPACE,
        Permission.INITIATE_SWARM,
    },
    Role.CONTRIBUTOR: {Permission.READ, Permission.WRITE, Permission.EXECUTE_TERMINAL},
    Role.REMOTE_PEER: {
        Permission.READ,
        Permission.EXECUTE_TERMINAL,  # Peers can read code and run in sandbox
    },
    Role.GUEST: {Permission.READ},
}


class RBACManager:
    def __init__(self):
        self.user_roles: dict[str, Role] = {}  # token_hash -> Role
        self.path_rules: dict[str, set[Permission]] = {}  # glob_pattern -> AllowedPermissions

    def register_token(self, token_hash: str, role: Role):
        self.user_roles[token_hash] = role
        log.info("rbac.token_registered", role=role.value)

    def set_path_rule(self, glob_pattern: str, permissions: set[Permission]):
        self.path_rules[glob_pattern] = permissions
        log.info("rbac.path_rule_set", pattern=glob_pattern, perms=[p.value for p in permissions])

    def has_permission(
        self, token_hash: str, permission: Permission, path: str | None = None
    ) -> bool:
        """Checks if a token holder has a specific permission, optionally scoped to a path."""
        # Default to OWNER for local dev if no tokens registered yet
        if not self.user_roles:
            return True

        role = self.user_roles.get(token_hash, Role.GUEST)
        base_allowed = permission in ROLE_PERMISSIONS.get(role, set())

        if not base_allowed:
            return False

        if path:
            import fnmatch

            # Check path-specific overrides
            for pattern, allowed_perms in self.path_rules.items():
                if fnmatch.fnmatch(path, pattern):
                    return permission in allowed_perms

        return True

    def validate_request(self, token: str, permission: Permission, path: str | None = None) -> bool:
        """Helper to validate a raw token string."""
        import hashlib

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return self.has_permission(token_hash, permission, path=path)


rbac_manager = RBACManager()
