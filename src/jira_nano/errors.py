"""Exception hierarchy for jira_nano."""
from __future__ import annotations


class JiraNanoError(Exception):
    """Base class for all jira_nano errors."""


class ValidationError(JiraNanoError):
    """A ticket or field failed schema/consistency validation (JN-1 / JN-D3)."""


class TicketNotFoundError(JiraNanoError):
    """The requested ticket id does not exist."""


class UnknownHandleError(ValidationError):
    """A referenced handle is not present in the user directory (JN-28)."""


class TransitionError(JiraNanoError):
    """An illegal workflow transition was attempted (Phase 2 / JN-10 / JN-D1)."""
