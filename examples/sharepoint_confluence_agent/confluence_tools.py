"""Confluence API tools for document management."""

import os
import base64
from typing import Literal, Optional
import requests
from langchain_core.tools import tool


def _get_confluence_session():
    """Get authenticated Confluence session."""
    url = os.getenv("CONFLUENCE_URL")
    token = os.getenv("CONFLUENCE_PERSONAL_TOKEN")

    if not url or not token:
        raise ValueError("CONFLUENCE_URL and CONFLUENCE_PERSONAL_TOKEN must be set in environment")

    session = requests.Session()
    # Use Bearer authentication with the personal token
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    return session, url


@tool
def confluence_search_content(
    query: str,
    content_type: Literal["page", "blogpost", "attachment", "all"] = "all",
    max_results: int = 10,
) -> str:
    """
    Search for content in Confluence.

    Args:
        query: Search query string. Can be either:
               - Simple text: "managed database"
               - CQL query: "space=MYSPACE AND title~'database'"
        content_type: Type of content to search for (page, blogpost, attachment, all)
        max_results: Maximum number of results to return (default: 10)

    Returns:
        Search results with titles, IDs, URLs, and excerpts
    """
    try:
        session, base_url = _get_confluence_session()

        # Detect if query is CQL (contains CQL operators) or simple text
        cql_indicators = [" AND ", " OR ", "type=", "space=", "title~", "text~", "creator="]
        is_cql = any(indicator in query for indicator in cql_indicators)

        if is_cql:
            # Use query as-is (it's already CQL)
            # Add type filter if specified and not already in query
            if content_type != "all" and "type=" not in query:
                cql = f"type={content_type} AND ({query})"
            else:
                cql = query
        else:
            # Simple text search - build CQL
            if content_type != "all":
                cql = f"type={content_type} AND text~'{query}'"
            else:
                cql = f"text~'{query}'"

        params = {
            "cql": cql,
            "limit": max_results,
            "expand": "body.view,version,space",
        }

        response = session.get(f"{base_url}/rest/api/content/search", params=params)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("results", []):
            result = {
                "id": item.get("id"),
                "type": item.get("type"),
                "title": item.get("title"),
                "space": item.get("space", {}).get("name"),
                "space_key": item.get("space", {}).get("key"),
                "url": f"{base_url}{item.get('_links', {}).get('webui', '')}",
                "excerpt": item.get("excerpt", "")[:200],  # First 200 chars
            }
            results.append(result)

        if not results:
            return f"No results found for query: {query}"

        return f"Found {len(results)} results:\n" + "\n".join([
            f"- [{r['title']}]({r['url']}) (ID: {r['id']}, Space: {r['space_key']})"
            for r in results
        ])

    except Exception as e:
        return f"Error searching Confluence: {str(e)}"


@tool
def confluence_get_page(
    page_id: str,
    include_body: bool = True,
) -> str:
    """
    Get a Confluence page by ID.

    Args:
        page_id: The ID of the page to retrieve
        include_body: Whether to include the page body content (default: True)

    Returns:
        Page content including title, body, and metadata
    """
    try:
        session, base_url = _get_confluence_session()

        expand_fields = "version,space,history"
        if include_body:
            expand_fields += ",body.storage,body.view"

        response = session.get(
            f"{base_url}/rest/api/content/{page_id}",
            params={"expand": expand_fields}
        )
        response.raise_for_status()

        data = response.json()

        result = f"""# {data.get('title')}

**Space:** {data.get('space', {}).get('name')}
**Type:** {data.get('type')}
**Version:** {data.get('version', {}).get('number')}
**URL:** {base_url}{data.get('_links', {}).get('webui', '')}
**Created:** {data.get('history', {}).get('createdDate')}
**Last Updated:** {data.get('version', {}).get('when')}
"""

        if include_body and "body" in data:
            # Get the storage format (contains the actual content)
            body_content = data.get("body", {}).get("storage", {}).get("value", "")
            result += f"\n## Content\n\n{body_content[:5000]}"  # Limit to first 5000 chars

        return result

    except Exception as e:
        return f"Error retrieving page: {str(e)}"


@tool
def confluence_get_attachments(page_id: str) -> str:
    """
    Get all attachments for a Confluence page.

    Args:
        page_id: The ID of the page

    Returns:
        List of attachments with download URLs
    """
    try:
        session, base_url = _get_confluence_session()

        response = session.get(
            f"{base_url}/rest/api/content/{page_id}/child/attachment",
            params={"expand": "version"}
        )
        response.raise_for_status()

        data = response.json()
        attachments = []

        for item in data.get("results", []):
            attachment = {
                "id": item.get("id"),
                "title": item.get("title"),
                "mediaType": item.get("metadata", {}).get("mediaType"),
                "fileSize": item.get("extensions", {}).get("fileSize"),
                "download_url": f"{base_url}{item.get('_links', {}).get('download', '')}",
            }
            attachments.append(attachment)

        if not attachments:
            return f"No attachments found for page {page_id}"

        return f"Found {len(attachments)} attachments:\n" + "\n".join([
            f"- {a['title']} ({a['mediaType']}, {a['fileSize']} bytes) - Download: {a['download_url']}"
            for a in attachments
        ])

    except Exception as e:
        return f"Error retrieving attachments: {str(e)}"


@tool
def confluence_download_attachment(
    attachment_id: str,
    save_path: Optional[str] = None,
) -> str:
    """
    Download a Confluence attachment.

    Args:
        attachment_id: The ID of the attachment
        save_path: Optional path to save the file. If not provided, returns base64 encoded content

    Returns:
        Success message with file path or base64 content
    """
    try:
        session, base_url = _get_confluence_session()

        # Get attachment metadata first
        response = session.get(f"{base_url}/rest/api/content/{attachment_id}")
        response.raise_for_status()
        metadata = response.json()

        # Download the attachment
        download_url = f"{base_url}{metadata.get('_links', {}).get('download', '')}"
        response = session.get(download_url)
        response.raise_for_status()

        if save_path:
            with open(save_path, "wb") as f:
                f.write(response.content)
            return f"Attachment downloaded successfully to: {save_path}"
        else:
            # Return base64 encoded content for further processing
            content_b64 = base64.b64encode(response.content).decode("utf-8")
            return f"Attachment content (base64, length={len(content_b64)}): {content_b64[:500]}..."

    except Exception as e:
        return f"Error downloading attachment: {str(e)}"


@tool
def confluence_create_page(
    space_key: str,
    title: str,
    content: str,
    parent_id: Optional[str] = None,
) -> str:
    """
    Create a new Confluence page. REQUIRES HUMAN APPROVAL.

    Args:
        space_key: The key of the space to create the page in
        title: The title of the page
        content: The content of the page (in Confluence storage format/HTML)
        parent_id: Optional parent page ID

    Returns:
        Success message with page URL
    """
    try:
        session, base_url = _get_confluence_session()

        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }

        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]

        response = session.post(f"{base_url}/rest/api/content", json=payload)
        response.raise_for_status()

        data = response.json()
        page_url = f"{base_url}{data.get('_links', {}).get('webui', '')}"

        return f"Page created successfully!\nTitle: {data.get('title')}\nID: {data.get('id')}\nURL: {page_url}"

    except Exception as e:
        return f"Error creating page: {str(e)}"


@tool
def confluence_update_page(
    page_id: str,
    new_content: str,
    new_title: Optional[str] = None,
) -> str:
    """
    Update an existing Confluence page. REQUIRES HUMAN APPROVAL.

    Args:
        page_id: The ID of the page to update
        new_content: The new content (in Confluence storage format/HTML)
        new_title: Optional new title for the page

    Returns:
        Success message with updated page URL
    """
    try:
        session, base_url = _get_confluence_session()

        # Get current page version
        response = session.get(f"{base_url}/rest/api/content/{page_id}", params={"expand": "version"})
        response.raise_for_status()
        current_page = response.json()

        current_version = current_page.get("version", {}).get("number", 0)
        current_title = current_page.get("title")

        payload = {
            "version": {"number": current_version + 1},
            "title": new_title if new_title else current_title,
            "type": "page",
            "body": {
                "storage": {
                    "value": new_content,
                    "representation": "storage"
                }
            }
        }

        response = session.put(f"{base_url}/rest/api/content/{page_id}", json=payload)
        response.raise_for_status()

        data = response.json()
        page_url = f"{base_url}{data.get('_links', {}).get('webui', '')}"

        return f"Page updated successfully!\nTitle: {data.get('title')}\nVersion: {data.get('version', {}).get('number')}\nURL: {page_url}"

    except Exception as e:
        return f"Error updating page: {str(e)}"


@tool
def confluence_delete_page(page_id: str) -> str:
    """
    Delete a Confluence page. REQUIRES HUMAN APPROVAL.

    Args:
        page_id: The ID of the page to delete

    Returns:
        Success message
    """
    try:
        session, base_url = _get_confluence_session()

        response = session.delete(f"{base_url}/rest/api/content/{page_id}")
        response.raise_for_status()

        return f"Page {page_id} deleted successfully"

    except Exception as e:
        return f"Error deleting page: {str(e)}"


@tool
def confluence_list_spaces(max_results: int = 25) -> str:
    """
    List all Confluence spaces.

    Args:
        max_results: Maximum number of spaces to return (default: 25)

    Returns:
        List of spaces with keys and names
    """
    try:
        session, base_url = _get_confluence_session()

        response = session.get(
            f"{base_url}/rest/api/space",
            params={"limit": max_results}
        )
        response.raise_for_status()

        data = response.json()
        spaces = []

        for space in data.get("results", []):
            spaces.append({
                "key": space.get("key"),
                "name": space.get("name"),
                "type": space.get("type"),
                "url": f"{base_url}{space.get('_links', {}).get('webui', '')}",
            })

        return f"Found {len(spaces)} spaces:\n" + "\n".join([
            f"- {s['name']} (Key: {s['key']}, Type: {s['type']}) - {s['url']}"
            for s in spaces
        ])

    except Exception as e:
        return f"Error listing spaces: {str(e)}"


# Export all tools
CONFLUENCE_TOOLS = [
    confluence_search_content,
    confluence_get_page,
    confluence_get_attachments,
    confluence_download_attachment,
    confluence_create_page,
    confluence_update_page,
    confluence_delete_page,
    confluence_list_spaces,
]
