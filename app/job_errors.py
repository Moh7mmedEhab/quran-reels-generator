"""Exceptions shared by cancellable render-job components."""


class JobCancelled(Exception):
    """Raised when a user cancels a queued or running render."""
