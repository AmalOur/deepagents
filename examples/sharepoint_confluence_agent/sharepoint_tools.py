"""SharePoint API tools for document management."""

import os
import base64
from typing import Literal, Optional
import requests
from langchain_core.tools import tool


def _get_sharepoint_session():
    """Get authenticated SharePoint session."""
    site_url = os.getenv("SHAREPOINT_SITE_URL")
    client_id = os.getenv("SHAREPOINT_CLIENT_ID")
    client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET")
    tenant_id = os.getenv("SHAREPOINT_TENANT_ID")

    if not all([site_url, client_id, client_secret, tenant_id]):
        raise ValueError(
            "SHAREPOINT_SITE_URL, SHAREPOINT_CLIENT_ID, SHAREPOINT_CLIENT_SECRET, "
            "and SHAREPOINT_TENANT_ID must be set in environment"
        )

    # Get access token using client credentials flow
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    token_response = requests.post(token_url, data=token_data)
    token_response.raise_for_status()
    access_token = token_response.json().get("access_token")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    })

    return session, site_url


@tool
def sharepoint_search_files(
    query: str,
    file_type: Optional[str] = None,
    max_results: int = 10,
) -> str:
    """
    Search for files in SharePoint.

    Args:
        query: Search query string
        file_type: Optional file extension filter (e.g., 'docx', 'pdf', 'xlsx')
        max_results: Maximum number of results to return (default: 10)

    Returns:
        List of matching files with metadata
    """
    try:
        session, site_url = _get_sharepoint_session()

        # Parse site URL to extract site details
        # Format: https://{tenant}.sharepoint.com/sites/{sitename}
        parts = site_url.replace("https://", "").split("/")
        tenant = parts[0]
        site_path = "/".join(parts[1:]) if len(parts) > 1 else ""

        # Build search query
        search_query = query
        if file_type:
            search_query += f" AND FileExtension:{file_type}"

        # Use Microsoft Graph API for search
        graph_url = f"https://graph.microsoft.com/v1.0/search/query"
        payload = {
            "requests": [
                {
                    "entityTypes": ["driveItem"],
                    "query": {"queryString": search_query},
                    "from": 0,
                    "size": max_results,
                }
            ]
        }

        response = session.post(graph_url, json=payload)
        response.raise_for_status()

        data = response.json()
        results = []

        for result_group in data.get("value", []):
            for hit in result_group.get("hitsContainers", [{}])[0].get("hits", []):
                resource = hit.get("resource", {})
                result = {
                    "id": resource.get("id"),
                    "name": resource.get("name"),
                    "webUrl": resource.get("webUrl"),
                    "size": resource.get("size", 0),
                    "createdDateTime": resource.get("createdDateTime"),
                    "lastModifiedDateTime": resource.get("lastModifiedDateTime"),
                    "summary": hit.get("summary", "")[:200],
                }
                results.append(result)

        if not results:
            return f"No files found matching query: {query}"

        return f"Found {len(results)} files:\n" + "\n".join([
            f"- {r['name']} (Size: {r['size']} bytes, Modified: {r['lastModifiedDateTime']})\n  URL: {r['webUrl']}\n  ID: {r['id']}"
            for r in results
        ])

    except Exception as e:
        return f"Error searching SharePoint: {str(e)}"


@tool
def sharepoint_get_file(
    file_id: str,
    include_content: bool = False,
) -> str:
    """
    Get file metadata from SharePoint.

    Args:
        file_id: The ID of the file (drive item ID)
        include_content: Whether to download and include file content (default: False)

    Returns:
        File metadata and optionally content
    """
    try:
        session, _ = _get_sharepoint_session()

        # Get file metadata
        response = session.get(f"https://graph.microsoft.com/v1.0/drives/items/{file_id}")
        response.raise_for_status()
        data = response.json()

        result = f"""# {data.get('name')}

**ID:** {data.get('id')}
**Size:** {data.get('size', 0)} bytes
**Created:** {data.get('createdDateTime')}
**Modified:** {data.get('lastModifiedDateTime')}
**Web URL:** {data.get('webUrl')}
**MIME Type:** {data.get('file', {}).get('mimeType')}
"""

        if include_content:
            # Download file content
            download_url = data.get("@microsoft.graph.downloadUrl")
            if download_url:
                content_response = requests.get(download_url)
                content_response.raise_for_status()

                # For binary files, return base64
                content_b64 = base64.b64encode(content_response.content).decode("utf-8")
                result += f"\n**Content (base64, length={len(content_b64)}):** {content_b64[:500]}...\n"
            else:
                result += "\n**Note:** Download URL not available\n"

        return result

    except Exception as e:
        return f"Error retrieving file: {str(e)}"


@tool
def sharepoint_download_file(
    file_id: str,
    save_path: str,
) -> str:
    """
    Download a file from SharePoint.

    Args:
        file_id: The ID of the file (drive item ID)
        save_path: Path where the file should be saved

    Returns:
        Success message with file path
    """
    try:
        session, _ = _get_sharepoint_session()

        # Get file metadata with download URL
        response = session.get(f"https://graph.microsoft.com/v1.0/drives/items/{file_id}")
        response.raise_for_status()
        data = response.json()

        download_url = data.get("@microsoft.graph.downloadUrl")
        if not download_url:
            return f"Error: Download URL not available for file {file_id}"

        # Download file
        content_response = requests.get(download_url)
        content_response.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(content_response.content)

        return f"File downloaded successfully!\nName: {data.get('name')}\nSize: {data.get('size')} bytes\nSaved to: {save_path}"

    except Exception as e:
        return f"Error downloading file: {str(e)}"


@tool
def sharepoint_list_folder_contents(
    folder_path: str = "/",
    site_relative: bool = True,
) -> str:
    """
    List contents of a SharePoint folder.

    Args:
        folder_path: Path to the folder (default: root "/")
        site_relative: Whether the path is relative to the site (default: True)

    Returns:
        List of files and folders
    """
    try:
        session, site_url = _get_sharepoint_session()

        # For simplicity, use the default document library
        # In production, you'd need to specify the drive ID
        if folder_path == "/":
            response = session.get(f"https://graph.microsoft.com/v1.0/sites/root/drive/root/children")
        else:
            # Remove leading slash if present
            folder_path = folder_path.lstrip("/")
            response = session.get(
                f"https://graph.microsoft.com/v1.0/sites/root/drive/root:/{folder_path}:/children"
            )

        response.raise_for_status()
        data = response.json()

        items = []
        for item in data.get("value", []):
            item_type = "Folder" if "folder" in item else "File"
            items.append({
                "name": item.get("name"),
                "type": item_type,
                "id": item.get("id"),
                "size": item.get("size", 0),
                "webUrl": item.get("webUrl"),
                "lastModified": item.get("lastModifiedDateTime"),
            })

        if not items:
            return f"Folder '{folder_path}' is empty"

        return f"Contents of '{folder_path}' ({len(items)} items):\n" + "\n".join([
            f"- [{i['type']}] {i['name']} (ID: {i['id']}, Size: {i['size']} bytes)"
            for i in items
        ])

    except Exception as e:
        return f"Error listing folder contents: {str(e)}"


@tool
def sharepoint_upload_file(
    file_path: str,
    destination_path: str,
    overwrite: bool = False,
) -> str:
    """
    Upload a file to SharePoint. REQUIRES HUMAN APPROVAL.

    Args:
        file_path: Local path to the file to upload
        destination_path: Destination path in SharePoint (e.g., '/Documents/myfile.docx')
        overwrite: Whether to overwrite if file exists (default: False)

    Returns:
        Success message with file URL
    """
    try:
        session, _ = _get_sharepoint_session()

        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()

        file_name = os.path.basename(file_path)
        destination_path = destination_path.lstrip("/")

        # Upload file (simple upload for files < 4MB, use resumable upload for larger files)
        if len(file_content) < 4 * 1024 * 1024:  # 4MB
            url = f"https://graph.microsoft.com/v1.0/sites/root/drive/root:/{destination_path}:/content"
            session.headers.update({"Content-Type": "application/octet-stream"})

            response = session.put(url, data=file_content)
            response.raise_for_status()

            data = response.json()
            return f"File uploaded successfully!\nName: {data.get('name')}\nID: {data.get('id')}\nURL: {data.get('webUrl')}"
        else:
            return "Error: Large file upload (>4MB) requires resumable upload session (not implemented yet)"

    except Exception as e:
        return f"Error uploading file: {str(e)}"


@tool
def sharepoint_create_folder(
    folder_name: str,
    parent_path: str = "/",
) -> str:
    """
    Create a new folder in SharePoint. REQUIRES HUMAN APPROVAL.

    Args:
        folder_name: Name of the folder to create
        parent_path: Parent folder path (default: root "/")

    Returns:
        Success message with folder details
    """
    try:
        session, _ = _get_sharepoint_session()

        parent_path = parent_path.lstrip("/")

        if parent_path == "" or parent_path == "/":
            url = f"https://graph.microsoft.com/v1.0/sites/root/drive/root/children"
        else:
            url = f"https://graph.microsoft.com/v1.0/sites/root/drive/root:/{parent_path}:/children"

        payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        }

        response = session.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        return f"Folder created successfully!\nName: {data.get('name')}\nID: {data.get('id')}\nURL: {data.get('webUrl')}"

    except Exception as e:
        return f"Error creating folder: {str(e)}"


@tool
def sharepoint_delete_item(item_id: str) -> str:
    """
    Delete a file or folder from SharePoint. REQUIRES HUMAN APPROVAL.

    Args:
        item_id: The ID of the item (file or folder) to delete

    Returns:
        Success message
    """
    try:
        session, _ = _get_sharepoint_session()

        response = session.delete(f"https://graph.microsoft.com/v1.0/drives/items/{item_id}")
        response.raise_for_status()

        return f"Item {item_id} deleted successfully"

    except Exception as e:
        return f"Error deleting item: {str(e)}"


@tool
def sharepoint_update_file(
    file_id: str,
    new_content_path: str,
) -> str:
    """
    Update an existing file in SharePoint. REQUIRES HUMAN APPROVAL.

    Args:
        file_id: The ID of the file to update
        new_content_path: Local path to the new content

    Returns:
        Success message
    """
    try:
        session, _ = _get_sharepoint_session()

        # Read new content
        with open(new_content_path, "rb") as f:
            file_content = f.read()

        session.headers.update({"Content-Type": "application/octet-stream"})
        response = session.put(
            f"https://graph.microsoft.com/v1.0/drives/items/{file_id}/content",
            data=file_content
        )
        response.raise_for_status()

        data = response.json()
        return f"File updated successfully!\nName: {data.get('name')}\nVersion: {data.get('version')}\nModified: {data.get('lastModifiedDateTime')}"

    except Exception as e:
        return f"Error updating file: {str(e)}"


# Export all tools
SHAREPOINT_TOOLS = [
    sharepoint_search_files,
    sharepoint_get_file,
    sharepoint_download_file,
    sharepoint_list_folder_contents,
    sharepoint_upload_file,
    sharepoint_create_folder,
    sharepoint_delete_item,
    sharepoint_update_file,
]
