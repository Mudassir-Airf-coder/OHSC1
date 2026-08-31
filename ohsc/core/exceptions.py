"""OHSC exception hierarchy."""


class OHSCError(Exception):
    """Base class for all OHSC errors."""


class PathSafetyError(OHSCError):
    """Raised when a filesystem operation targets a disallowed path."""


class PermissionError(OHSCError):
    """Raised when an operation lacks required authorization."""


class ValidationError(OHSCError):
    """Raised when input/contract validation fails."""


class AgentError(OHSCError):
    """Raised when an agent fails to complete its task."""


class WorkflowError(OHSCError):
    """Raised when a workflow step fails and cannot proceed."""


class TransactionError(OHSCError):
    """Raised when a transaction fails and rollback is not possible."""
