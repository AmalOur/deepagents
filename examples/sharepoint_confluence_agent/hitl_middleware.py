"""Human-in-the-loop middleware for destructive operations."""

from typing import Any, Callable
from langgraph.types import Command, interrupt
from langgraph.agent import AgentMiddleware
from langgraph.agent.tool_call import ToolCallRequest, ToolMessage


class HumanInLoopMiddleware(AgentMiddleware):
    """
    Middleware that requires human approval for destructive operations.

    This middleware intercepts tool calls that modify, create, or delete content
    and requires explicit human approval before executing them.
    """

    # Tools that require human approval
    DESTRUCTIVE_TOOLS = {
        # Confluence
        "confluence_create_page",
        "confluence_update_page",
        "confluence_delete_page",
        # SharePoint
        "sharepoint_upload_file",
        "sharepoint_create_folder",
        "sharepoint_delete_item",
        "sharepoint_update_file",
    }

    def wrap_tool_call(
        self, request: ToolCallRequest, handler: Callable[..., Any]
    ) -> ToolMessage | Command:
        """
        Intercept tool calls and require approval for destructive operations.

        Args:
            request: The tool call request
            handler: The next handler in the chain

        Returns:
            ToolMessage or Command
        """
        tool_name = request.tool_name

        # Check if this tool requires approval
        if tool_name in self.DESTRUCTIVE_TOOLS:
            # Get tool arguments for display
            tool_args = request.tool_input

            # Create approval request message
            approval_message = self._format_approval_request(tool_name, tool_args)

            # Interrupt execution and ask for human approval
            approval = interrupt(approval_message)

            # Check approval response
            if not self._is_approved(approval):
                # Return rejection message
                return ToolMessage(
                    content=f"❌ Operation cancelled by user: {tool_name}",
                    tool_call_id=request.tool_call_id,
                    name=tool_name,
                )

            # If approved, continue with the tool execution
            return handler(request)

        # For non-destructive operations, proceed normally
        return handler(request)

    def _format_approval_request(self, tool_name: str, tool_args: dict) -> str:
        """
        Format an approval request message for the user.

        Args:
            tool_name: Name of the tool requiring approval
            tool_args: Arguments passed to the tool

        Returns:
            Formatted approval request message
        """
        operation_descriptions = {
            "confluence_create_page": "Create a new Confluence page",
            "confluence_update_page": "Update an existing Confluence page",
            "confluence_delete_page": "Delete a Confluence page",
            "sharepoint_upload_file": "Upload a file to SharePoint",
            "sharepoint_create_folder": "Create a new SharePoint folder",
            "sharepoint_delete_item": "Delete a SharePoint item",
            "sharepoint_update_file": "Update a SharePoint file",
        }

        description = operation_descriptions.get(tool_name, f"Execute {tool_name}")

        message = f"""
🚨 **APPROVAL REQUIRED** 🚨

**Operation:** {description}

**Tool:** {tool_name}

**Parameters:**
"""
        # Format tool arguments
        for key, value in tool_args.items():
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

    def _is_approved(self, approval_response: Any) -> bool:
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


class SelectiveHITLMiddleware(AgentMiddleware):
    """
    More flexible HITL middleware that allows customization of which tools require approval.

    Example:
        middleware = SelectiveHITLMiddleware(
            require_approval=["confluence_delete_page", "sharepoint_delete_item"],
            skip_approval=["confluence_create_page"]  # Override for specific tools
        )
    """

    def __init__(
        self,
        require_approval: list[str] | None = None,
        skip_approval: list[str] | None = None,
        approval_message_template: str | None = None,
    ):
        """
        Initialize the selective HITL middleware.

        Args:
            require_approval: List of tool names that require approval.
                            If None, uses default destructive tools.
            skip_approval: List of tool names to skip approval for (overrides require_approval)
            approval_message_template: Custom template for approval messages
        """
        super().__init__()

        if require_approval is None:
            # Default to all destructive operations
            self.require_approval = HumanInLoopMiddleware.DESTRUCTIVE_TOOLS.copy()
        else:
            self.require_approval = set(require_approval)

        self.skip_approval = set(skip_approval or [])
        self.approval_message_template = approval_message_template

    def wrap_tool_call(
        self, request: ToolCallRequest, handler: Callable[..., Any]
    ) -> ToolMessage | Command:
        """Intercept tool calls and require approval for specified operations."""
        tool_name = request.tool_name

        # Skip if explicitly excluded
        if tool_name in self.skip_approval:
            return handler(request)

        # Check if this tool requires approval
        if tool_name in self.require_approval:
            tool_args = request.tool_input

            # Create approval request
            if self.approval_message_template:
                approval_message = self.approval_message_template.format(
                    tool_name=tool_name, tool_args=tool_args
                )
            else:
                approval_message = self._format_approval_request(tool_name, tool_args)

            # Interrupt and ask for approval
            approval = interrupt(approval_message)

            # Check approval
            if not self._is_approved(approval):
                return ToolMessage(
                    content=f"❌ Operation cancelled by user: {tool_name}",
                    tool_call_id=request.tool_call_id,
                    name=tool_name,
                )

            # If approved, continue
            return handler(request)

        # For non-required tools, proceed normally
        return handler(request)

    def _format_approval_request(self, tool_name: str, tool_args: dict) -> str:
        """Format approval request message."""
        message = f"""
🚨 **APPROVAL REQUIRED** 🚨

**Tool:** {tool_name}

**Parameters:**
"""
        for key, value in tool_args.items():
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            message += f"  - {key}: {value}\n"

        message += """
**Do you approve this operation?**

Type 'yes' to approve or 'no' to reject.
"""
        return message

    def _is_approved(self, approval_response: Any) -> bool:
        """Check if the user approved the operation."""
        if approval_response is None:
            return False

        response = str(approval_response).lower().strip()
        approval_keywords = {"yes", "y", "approve", "approved", "ok", "confirm", "confirmed"}

        return response in approval_keywords


class LoggingHITLMiddleware(HumanInLoopMiddleware):
    """
    Extended HITL middleware that also logs all approval requests and responses.

    Useful for auditing and compliance purposes.
    """

    def __init__(self, log_file: str = "hitl_approvals.log"):
        """
        Initialize the logging HITL middleware.

        Args:
            log_file: Path to the log file
        """
        super().__init__()
        self.log_file = log_file

    def wrap_tool_call(
        self, request: ToolCallRequest, handler: Callable[..., Any]
    ) -> ToolMessage | Command:
        """Intercept tool calls, require approval, and log the interaction."""
        tool_name = request.tool_name

        if tool_name in self.DESTRUCTIVE_TOOLS:
            import json
            from datetime import datetime

            tool_args = request.tool_input

            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "tool_name": tool_name,
                "tool_args": tool_args,
                "tool_call_id": request.tool_call_id,
            }

            # Request approval
            approval_message = self._format_approval_request(tool_name, tool_args)
            approval = interrupt(approval_message)

            # Check approval
            approved = self._is_approved(approval)
            log_entry["approved"] = approved
            log_entry["response"] = str(approval)

            # Log the interaction
            self._log_approval(log_entry)

            if not approved:
                return ToolMessage(
                    content=f"❌ Operation cancelled by user: {tool_name}",
                    tool_call_id=request.tool_call_id,
                    name=tool_name,
                )

            result = handler(request)
            log_entry["result"] = "success"
            self._log_approval(log_entry)

            return result

        return handler(request)

    def _log_approval(self, log_entry: dict):
        """Log an approval request and response."""
        import json

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
