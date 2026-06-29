"""Custom exception hierarchy for forge-agent."""

from __future__ import annotations


class ForgeError(Exception):
    """Base exception for all forge-agent errors."""

    def __init__(self, message: str, *, code: str = "FORGE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(ForgeError):
    """Entity not found."""

    def __init__(self, entity_type: str, identifier: str):
        super().__init__(
            f"{entity_type} not found: {identifier}",
            code="NOT_FOUND",
        )
        self.entity_type = entity_type
        self.identifier = identifier


class ConflictError(ForgeError):
    """Entity already exists or state conflict."""

    def __init__(self, message: str):
        super().__init__(message, code="CONFLICT")


class ValidationError(ForgeError):
    """Input validation failed."""

    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION")


class SecurityError(ForgeError):
    """Security policy violation."""

    def __init__(self, message: str):
        super().__init__(message, code="SECURITY")


class RunnerError(ForgeError):
    """Runner execution error."""

    def __init__(self, message: str, *, runner: str = "unknown"):
        super().__init__(message, code="RUNNER_ERROR")
        self.runner = runner


class InterruptError(ForgeError):
    """Session or task was interrupted."""

    def __init__(self, session_id: str):
        super().__init__(
            f"Session interrupted: {session_id}", code="INTERRUPT"
        )
        self.session_id = session_id
