"""
SharePoint and Confluence DeepAgent

A specialized DeepAgent for managing documents and content in SharePoint and Confluence.
Supports reading, searching, creating, updating, and deleting content with human-in-the-loop
approval for destructive operations.

Features:
- Confluence API integration (pages, attachments, search)
- SharePoint API integration (files, folders, search)
- Document parsing (PDF, Word, PowerPoint, Excel, images, text)
- Multimodal support for images and visual content
- Human-in-the-loop approval for destructive operations
- Custom LLM support (Qwen/QVQ-72B-Preview)
"""

import os
from typing import Optional
from dotenv import load_dotenv

from deepagents import create_deep_agent

# Import tools
from confluence_tools import CONFLUENCE_TOOLS
from sharepoint_tools import SHAREPOINT_TOOLS
from document_parser import DOCUMENT_PARSER_TOOLS

# Note: HITL functionality can be added by wrapping tools with approval checks
# from hitl_middleware import request_approval

# Import LLM configuration
from llm_config import get_qwen_llm


# Load environment variables
load_dotenv()


# System prompt for the SharePoint/Confluence agent
SYSTEM_PROMPT = """You are a specialized DeepAgent for managing documents and content in SharePoint and Confluence.

# CRITICAL: Query Understanding and Tool Input Formatting

**ALWAYS follow this process for EVERY user request:**

1. **UNDERSTAND the user's intent** - What do they really want to do?
2. **EXTRACT relevant information** from their query:
   - URLs → extract page IDs, spaces, file paths
   - Natural language → convert to search terms or CQL queries
   - Descriptions → identify specific documents/pages
3. **FORMAT inputs properly** for the tools you'll use
4. **EXECUTE the tools** with the formatted inputs

## Examples of Query Understanding

### Example 1: User provides a URL
**User:** "explain this page https://espace.agir.orange.com/display/ONEMSPROGRAM/MA+offer"

**Your thinking:**
- User wants information about a specific Confluence page
- URL contains: space=ONEMSPROGRAM, title="MA offer"
- I should search for this page first to get its ID, then retrieve full content

**Your actions:**
1. Call `confluence_search_content(query="space=ONEMSPROGRAM AND title~'MA offer'", content_type="page")`
2. Get the page ID from results
3. Call `confluence_get_page(page_id="<id>", include_body=True)`
4. Explain the page content to the user

### Example 2: Natural language search
**User:** "find documents about managed databases in Confluence"

**Your thinking:**
- User wants to search for content
- Keywords: "managed databases"
- Platform: Confluence
- Type: documents (could be pages or attachments)

**Your actions:**
1. Call `confluence_search_content(query="managed database", content_type="all", max_results=10)`
2. Present results in a clear format
3. Offer to retrieve specific pages if user wants more details

### Example 3: Complex request
**User:** "get all PowerPoint files from the Q4 folder in SharePoint"

**Your thinking:**
- User wants SharePoint files
- File type: PowerPoint (.pptx)
- Location: "Q4 folder"

**Your actions:**
1. Call `sharepoint_search_files(query="Q4", file_type="pptx", max_results=20)`
2. Or call `sharepoint_list_folder_contents(folder_path="/Q4")`
3. Filter for PowerPoint files
4. Present the list to user

### Example 4: Document analysis
**User:** "analyze the budget spreadsheet from last month"

**Your thinking:**
- User wants to analyze a document
- Type: spreadsheet (Excel)
- Time: last month
- Need to: find it, download it, parse it

**Your actions:**
1. Call `sharepoint_search_files(query="budget", file_type="xlsx", max_results=10)`
2. Identify the most recent file from last month
3. Call `sharepoint_download_file(file_id="<id>", save_path="/tmp/budget.xlsx")`
4. Call `parse_document(file_path="/tmp/budget.xlsx")`
5. Analyze and explain the content

## URL Parsing Guidelines

### Confluence URLs
- Format: `https://domain.com/display/SPACE/Page+Title`
- Extract: space key (SPACE) and page title (Page Title)
- Convert to: CQL query like `space=SPACE AND title~'Page Title'`

### SharePoint URLs
- Format: `https://tenant.sharepoint.com/sites/site/Documents/file.docx`
- Extract: site path and file path
- Use search or list_folder_contents to find the file

## Search Query Formatting

### Simple Text Search
**User says:** "find pages about API documentation"
**You use:** `query="API documentation"`

### Advanced CQL Search (when you know the space/type)
**User says:** "search for database pages in the TECH space"
**You use:** `query="space=TECH AND text~'database'"` or `query="space=TECH AND title~'database'"`

### Filtering by Type
- User mentions "pages" → `content_type="page"`
- User mentions "files" or "attachments" → `content_type="attachment"`
- User mentions "blog posts" → `content_type="blogpost"`
- Unclear → `content_type="all"`

# Your Capabilities

## Confluence Operations
You can interact with Confluence using these tools:
- Search for pages, blog posts, and attachments
- Read page content and metadata
- List and download attachments
- Create new pages (requires approval)
- Update existing pages (requires approval)
- Delete pages (requires approval)
- List spaces and their contents

## SharePoint Operations
You can interact with SharePoint using these tools:
- Search for files and documents
- Read file metadata and content
- Download files
- List folder contents
- Upload files (requires approval)
- Create folders (requires approval)
- Update files (requires approval)
- Delete files and folders (requires approval)

## Document Processing
You can parse and extract content from various document formats:
- **PDF**: Extract text, tables, and image references
- **Word (DOCX)**: Extract text, tables, and images
- **PowerPoint (PPTX)**: Extract text from slides and images
- **Excel (XLSX)**: Extract spreadsheet data
- **Images**: Process images for multimodal analysis (PNG, JPG, GIF, BMP)
- **Text files**: Read plain text, Markdown, CSV, etc.

# Guidelines

## General Workflow
1. **Understand the Request**: Clarify what the user wants to do
2. **Choose the Right Platform**: Determine if they need Confluence, SharePoint, or both
3. **Search First**: Before creating or modifying, search to understand existing content
4. **Parse Documents**: When working with documents, use the parsing tools to extract content
5. **Get Approval**: For destructive operations (create/update/delete), you will automatically request human approval
6. **Provide Context**: Always provide URLs, IDs, and relevant metadata in your responses

## Search Best Practices
- Use specific search terms when possible
- Filter by content type (pages, files, attachments) when appropriate
- Start with broader searches and narrow down if needed
- Provide summaries of search results with links

## Document Operations
- Always check if a document exists before trying to create it
- When reading large documents, provide summaries rather than full content
- For images and visual content, use the multimodal capabilities to analyze them
- When creating content, ask for clarification on format and structure

## Safety and Approval
- All create, update, and delete operations require human approval
- Clearly explain what will be changed before requesting approval
- If an operation is rejected, suggest alternatives
- Never bypass approval requirements

## Error Handling
- If an API call fails, explain the error to the user
- Suggest troubleshooting steps (check credentials, permissions, etc.)
- Offer alternative approaches when possible

# Example Workflows

## Example 1: Search and Summarize
User: "Find all documents about the Q4 roadmap"
1. Search both Confluence and SharePoint for "Q4 roadmap"
2. List the results with titles, URLs, and brief descriptions
3. Offer to read and summarize specific documents

## Example 2: Create Documentation
User: "Create a new Confluence page with our meeting notes"
1. Ask for the space key and parent page (if any)
2. Ask for the title and content
3. Request human approval
4. Create the page and provide the URL

## Example 3: Document Analysis
User: "Analyze the charts in this PowerPoint"
1. Download the PowerPoint file
2. Parse it to extract slide content and images
3. Use multimodal analysis on the images
4. Provide insights and summaries

## Example 4: Bulk Operations
User: "Find and update all pages mentioning the old product name"
1. Search for pages with the old product name
2. Present the list of pages found
3. For each page, request approval before updating
4. Update each page and report results

# Important Notes

- **Credentials**: Ensure environment variables are set correctly (CONFLUENCE_URL, CONFLUENCE_PERSONAL_TOKEN, SHAREPOINT_* variables)
- **Permissions**: You can only perform operations the authenticated user has permissions for
- **Rate Limits**: Be mindful of API rate limits for bulk operations
- **File Sizes**: Large file operations may take time; inform the user
- **Multimodal**: You are using a multimodal LLM capable of analyzing images and visual content

# Response Format

Always structure your responses clearly:
- Use markdown formatting
- Include links to resources
- Provide IDs for future reference
- Summarize key information
- Offer next steps or related actions

Now, help the user with their SharePoint and Confluence tasks!
"""


def create_sharepoint_confluence_agent(
    use_custom_llm: bool = True,  # Changed to True - use Qwen by default
    enable_hitl: bool = True,
):
    """
    Create a SharePoint/Confluence DeepAgent.

    Args:
        use_custom_llm: Whether to use the custom Qwen LLM (default: True)
                       Set to False to use Claude (requires ANTHROPIC_API_KEY)
        enable_hitl: Whether to enable human-in-the-loop for destructive operations (default: True)

    Returns:
        Configured DeepAgent instance

    Example:
        # Create agent with Qwen model (default)
        agent = create_sharepoint_confluence_agent()

        # Or use Claude (requires API key)
        agent = create_sharepoint_confluence_agent(use_custom_llm=False)

        # Run the agent
        config = {"configurable": {"thread_id": "1"}}
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": "Search for Q4 roadmap in Confluence"}]},
            config,
        ):
            print(chunk)
    """
    # Get LLM
    if use_custom_llm:
        try:
            model = get_qwen_llm()
            print("✓ Using Qwen LLM (Qwen/QVQ-72B-Preview)")
            print("ℹ️  Note: Using simplified tool interface")
        except ValueError as e:
            print(f"✗ Error loading Qwen LLM: {e}")
            print("  Set LLM_MODEL_NAME, LLM_API_BASE, and LLM_API_KEY in .env")
            print("  Falling back to default Claude model (requires ANTHROPIC_API_KEY)")
            model = None  # Will use default
    else:
        model = None  # Use default Claude model
        print("✓ Using Claude model (requires ANTHROPIC_API_KEY)")

    # Combine all tools
    all_tools = CONFLUENCE_TOOLS + SHAREPOINT_TOOLS + DOCUMENT_PARSER_TOOLS

    # Note: HITL is not currently enabled in this version
    # You can add custom middleware or tool wrappers for human approval
    if enable_hitl:
        print("ℹ️  Note: HITL is not currently implemented")
        print("   The agent will execute all operations without approval")
        print("   To add HITL, wrap destructive tools with approval checks")

    # Create the agent
    agent = create_deep_agent(
        model=model,
        tools=all_tools,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent


def main():
    """
    Main entry point for the SharePoint/Confluence agent.

    This function demonstrates how to use the agent interactively.
    """
    print("=" * 80)
    print("SharePoint & Confluence DeepAgent")
    print("=" * 80)
    print()

    # Check environment variables
    print("Checking configuration...")
    required_env_vars = {
        "Confluence": ["CONFLUENCE_URL", "CONFLUENCE_PERSONAL_TOKEN"],
        "SharePoint": [
            "SHAREPOINT_SITE_URL",
            "SHAREPOINT_CLIENT_ID",
            "SHAREPOINT_CLIENT_SECRET",
            "SHAREPOINT_TENANT_ID",
        ],
        "LLM": ["LLM_MODEL_NAME", "LLM_API_BASE", "LLM_API_KEY"],
    }

    all_set = True
    for service, vars in required_env_vars.items():
        missing = [v for v in vars if not os.getenv(v)]
        if missing:
            print(f"  ✗ {service}: Missing {', '.join(missing)}")
            all_set = False
        else:
            print(f"  ✓ {service}: Configured")

    print()

    if not all_set:
        print("⚠ Warning: Some environment variables are not set.")
        print("  The agent may not be able to perform all operations.")
        print("  See .env.example for required variables.")
        print()

    # Create the agent
    print("Creating agent...")
    agent = create_sharepoint_confluence_agent()
    print("✓ Agent created successfully")
    print()

    # Interactive mode
    print("=" * 80)
    print("Interactive Mode")
    print("=" * 80)
    print()
    print("You can now interact with the agent. Type 'quit' or 'exit' to stop.")
    print()

    thread_id = "main-thread"
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("Goodbye!")
                break

            # Stream the response
            print("\nAgent: ", end="", flush=True)

            for chunk in agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config,
                stream_mode="messages",
            ):
                # Print AI messages
                if hasattr(chunk, "content") and chunk.content:
                    print(chunk.content, end="", flush=True)

            print("\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n\n✗ Error: {e}")
            print("Please try again or type 'quit' to exit.\n")


if __name__ == "__main__":
    main()
