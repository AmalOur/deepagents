"""
SharePoint & Confluence DeepAgent

A specialized DeepAgent for managing documents and content in SharePoint and Confluence.

Example usage:
    from sharepoint_confluence_agent import create_sharepoint_confluence_agent

    # Create the agent
    agent = create_sharepoint_confluence_agent()

    # Run a query
    config = {"configurable": {"thread_id": "my-session"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Search for documentation"}]},
        config,
    )
"""

from .sharepoint_confluence_agent import (
    create_sharepoint_confluence_agent,
    SYSTEM_PROMPT,
)

from .confluence_tools import (
    CONFLUENCE_TOOLS,
    confluence_search_content,
    confluence_get_page,
    confluence_get_attachments,
    confluence_download_attachment,
    confluence_create_page,
    confluence_update_page,
    confluence_delete_page,
    confluence_list_spaces,
)

from .sharepoint_tools import (
    SHAREPOINT_TOOLS,
    sharepoint_search_files,
    sharepoint_get_file,
    sharepoint_download_file,
    sharepoint_list_folder_contents,
    sharepoint_upload_file,
    sharepoint_create_folder,
    sharepoint_delete_item,
    sharepoint_update_file,
)

from .document_parser import (
    DOCUMENT_PARSER_TOOLS,
    parse_document,
    extract_text_from_document,
    get_image_for_llm,
)

from .hitl_middleware import (
    request_approval,
)

from .llm_config import (
    get_custom_llm,
    get_qwen_llm,
    QwenLLMConfig,
)


__all__ = [
    # Main agent
    "create_sharepoint_confluence_agent",
    "SYSTEM_PROMPT",
    # Confluence tools
    "CONFLUENCE_TOOLS",
    "confluence_search_content",
    "confluence_get_page",
    "confluence_get_attachments",
    "confluence_download_attachment",
    "confluence_create_page",
    "confluence_update_page",
    "confluence_delete_page",
    "confluence_list_spaces",
    # SharePoint tools
    "SHAREPOINT_TOOLS",
    "sharepoint_search_files",
    "sharepoint_get_file",
    "sharepoint_download_file",
    "sharepoint_list_folder_contents",
    "sharepoint_upload_file",
    "sharepoint_create_folder",
    "sharepoint_delete_item",
    "sharepoint_update_file",
    # Document parser
    "DOCUMENT_PARSER_TOOLS",
    "parse_document",
    "extract_text_from_document",
    "get_image_for_llm",
    # HITL helpers
    "request_approval",
    # LLM config
    "get_custom_llm",
    "get_qwen_llm",
    "QwenLLMConfig",
]

__version__ = "1.0.0"
__author__ = "DeepAgents Contributors"
__description__ = "SharePoint and Confluence DeepAgent for document management"
