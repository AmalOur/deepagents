"""Human-in-the-loop helper functions for destructive operations."""

from typing import Any
from langgraph.types import interrupt


def request_approval(operation_name: str, operation_details: dict) -> bool:
    """
    Request human approval for a destructive operation.

    Args:
        operation_name: Name of the operation (e.g., "Create Confluence page")
        operation_details: Dictionary of operation parameters

    Returns:
        True if approved, False otherwise
    """
    approval_message = _format_approval_request(operation_name, operation_details)
    approval = interrupt(approval_message)
    return _is_approved(approval)


def _format_approval_request(operation_name: str, operation_details: dict) -> str:
    """
    Format an approval request message for the user.

    Args:
        operation_name: Name of the operation
        operation_details: Operation parameters

    Returns:
        Formatted approval request message
    """
    message = f"""
🚨 **APPROVAL REQUIRED** 🚨

**Operation:** {operation_name}

**Parameters:**
"""
    # Format operation details
    for key, value in operation_details.items():
        # Truncate long values
        if isinstance(value, str) and len(value) > 200:
            value = value[:200] + "..."
        message += f"  - {key}: {value}\n"

    message += """
**Do you approve this operation?**

Type 'yes', 'y', or 'approve' to approve.
Type 'no', 'n', or 'reject' to reject.
"""
    return message


def _is_approved(approval_response: Any) -> bool:
    """
    Check if the user approved the operation.

    Args:
        approval_response: The response from the interrupt

    Returns:
        True if approved, False otherwise
    """
    if approval_response is None:
        return False

    # Convert to string and normalize
    response = str(approval_response).lower().strip()

    # Check for approval keywords
    approval_keywords = {"yes", "y", "approve", "approved", "ok", "confirm", "confirmed"}

    return response in approval_keywords
