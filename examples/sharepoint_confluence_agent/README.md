# SharePoint & Confluence DeepAgent

A specialized DeepAgent for managing documents and content in SharePoint and Confluence. This agent provides comprehensive document management capabilities with human-in-the-loop approval for destructive operations.

## 🌟 Features

### Confluence Operations
- ✅ Search pages, blog posts, and attachments
- ✅ Read page content and metadata
- ✅ List and download attachments
- ✅ Create new pages (with approval)
- ✅ Update existing pages (with approval)
- ✅ Delete pages (with approval)
- ✅ List spaces and browse content

### SharePoint Operations
- ✅ Search for files and documents
- ✅ Read file metadata and content
- ✅ Download files
- ✅ List folder contents
- ✅ Upload files (with approval)
- ✅ Create folders (with approval)
- ✅ Update files (with approval)
- ✅ Delete files and folders (with approval)

### Document Processing
- 📄 **PDF**: Extract text, tables, and image references
- 📝 **Word (DOCX)**: Extract text, tables, and embedded images
- 📊 **PowerPoint (PPTX)**: Extract slide content and images
- 📈 **Excel (XLSX)**: Extract spreadsheet data
- 🖼️ **Images**: Process images for multimodal LLM analysis (PNG, JPG, GIF, BMP)
- 📃 **Text Files**: Read plain text, Markdown, CSV, and more

### Security & Safety
- 🛡️ **Human-in-the-Loop**: Automatic approval required for all destructive operations
- 📝 **Audit Logging**: Optional logging of all approval requests and responses
- 🔐 **Secure Authentication**: Environment-based credential management
- 🚫 **No Hardcoded Secrets**: All sensitive data in environment variables

### Multimodal LLM Support
- 🤖 **Custom LLM**: Integrated with Qwen/QVQ-72B-Preview (OpenAI-compatible)
- 👁️ **Vision Capabilities**: Can analyze images and visual content
- 🔄 **Flexible Configuration**: Easy to swap LLM models

## 📋 Prerequisites

### For Confluence
- Confluence instance URL
- Personal Access Token with appropriate permissions

### For SharePoint
- SharePoint site URL
- Azure AD application registration with:
  - Client ID
  - Client Secret
  - Tenant ID
  - API permissions: `Sites.Read.All`, `Files.ReadWrite.All`

### For Custom LLM
- Qwen/QVQ-72B-Preview API endpoint
- API key
- Model name

## 🚀 Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd deepagents
   ```

2. **Install the DeepAgents framework**:
   ```bash
   cd libs/deepagents
   pip install -e .
   cd ../..
   ```

3. **Navigate to the agent directory**:
   ```bash
   cd examples/sharepoint_confluence_agent
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   nano .env  # or use your preferred editor
   ```

## ⚙️ Configuration

Edit the `.env` file with your credentials:

### Confluence Configuration
```env
CONFLUENCE_URL=https://your-confluence-instance.com
CONFLUENCE_PERSONAL_TOKEN=your-base64-encoded-token
```

### SharePoint Configuration
```env
SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com/sites/yoursite
SHAREPOINT_CLIENT_ID=your-client-id
SHAREPOINT_CLIENT_SECRET=your-client-secret
SHAREPOINT_TENANT_ID=your-tenant-id
```

### LLM Configuration
```env
LLM_MODEL_NAME=Qwen/QVQ-72B-Preview
LLM_API_BASE=https://model-mlqvq-72b-799001-614977.ai.gcore.dev/v1
LLM_API_KEY=your-api-key
```

### Setting Up SharePoint Permissions

1. **Register an App in Azure AD**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to **Azure Active Directory** > **App registrations**
   - Click **New registration**
   - Name your app and register it

2. **Get Client ID and Tenant ID**:
   - Copy the **Application (client) ID**
   - Copy the **Directory (tenant) ID**

3. **Create Client Secret**:
   - Go to **Certificates & secrets**
   - Click **New client secret**
   - Copy the secret **VALUE** (not the ID)

4. **Grant API Permissions**:
   - Go to **API permissions**
   - Click **Add a permission** > **Microsoft Graph** > **Application permissions**
   - Add these permissions:
     - `Sites.Read.All` or `Sites.ReadWrite.All`
     - `Files.Read.All` or `Files.ReadWrite.All`
     - `User.Read`
   - Click **Grant admin consent**

## 🎯 Usage

### Interactive Mode

Run the agent in interactive mode:

```bash
python sharepoint_confluence_agent.py
```

This will start an interactive session where you can chat with the agent:

```
You: Search for Q4 roadmap in Confluence
Agent: I found 3 pages matching "Q4 roadmap"...

You: Download the first document and summarize it
Agent: [Downloads and analyzes the document]...
```

### Programmatic Usage

```python
from sharepoint_confluence_agent import create_sharepoint_confluence_agent

# Create the agent
agent = create_sharepoint_confluence_agent()

# Run a query
config = {"configurable": {"thread_id": "my-session"}}
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Search for project documentation"}]},
    config,
)

print(result)
```

### Using Individual Tools

You can also use the tools directly:

```python
from confluence_tools import confluence_search_content, confluence_get_page
from sharepoint_tools import sharepoint_search_files
from document_parser import parse_document

# Search Confluence
results = confluence_search_content.invoke({"query": "roadmap", "max_results": 5})
print(results)

# Get a specific page
page = confluence_get_page.invoke({"page_id": "123456"})
print(page)

# Search SharePoint
files = sharepoint_search_files.invoke({"query": "budget", "file_type": "xlsx"})
print(files)

# Parse a document
content = parse_document.invoke({"file_path": "/path/to/document.pdf"})
print(content)
```

## 📚 Example Workflows

### Example 1: Search and Summarize

```
User: Find all documents about the Q4 budget in SharePoint and Confluence

Agent:
1. Searches both platforms for "Q4 budget"
2. Lists all matching documents with links
3. Offers to read and summarize specific documents
```

### Example 2: Create Documentation

```
User: Create a new Confluence page with our meeting notes

Agent:
1. Asks for the space key and parent page
2. Asks for the title and content
3. Requests human approval
4. Creates the page and provides the URL
```

### Example 3: Document Analysis

```
User: Download the PowerPoint from SharePoint and analyze the charts

Agent:
1. Searches for the PowerPoint file
2. Downloads it
3. Parses to extract slides and images
4. Analyzes images using multimodal LLM
5. Provides insights and summaries
```

### Example 4: Bulk Update

```
User: Find all Confluence pages mentioning "old product name" and update them

Agent:
1. Searches for pages with "old product name"
2. Lists all matching pages
3. For each page:
   - Shows the proposed change
   - Requests approval
   - Updates the page if approved
4. Reports results
```

## 🛡️ Human-in-the-Loop (HITL)

All destructive operations require explicit human approval:

- Creating pages/files
- Updating content
- Deleting items

When a destructive operation is requested, the agent will:
1. Display what will be changed
2. Show all parameters
3. Ask for approval: `yes`/`no`

Example approval prompt:
```
🚨 APPROVAL REQUIRED 🚨

Operation: Create a new Confluence page

Tool: confluence_create_page

Parameters:
  - space_key: TECH
  - title: Q4 Roadmap
  - content: <page content>
  - parent_id: 123456

Do you approve this operation?
Type 'yes' to approve or 'no' to reject.
```

### Disabling HITL (Not Recommended)

To disable HITL (for automated workflows):

```python
agent = create_sharepoint_confluence_agent(enable_hitl=False)
```

## 🔧 Architecture

### Project Structure

```
sharepoint_confluence_agent/
├── sharepoint_confluence_agent.py  # Main agent implementation
├── confluence_tools.py             # Confluence API tools
├── sharepoint_tools.py             # SharePoint API tools
├── document_parser.py              # Document parsing utilities
├── hitl_middleware.py              # Human-in-the-loop middleware
├── llm_config.py                   # Custom LLM configuration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

### Components

1. **Tools**: LangChain tools for API interactions
2. **Middleware**: AgentMiddleware for HITL and other behaviors
3. **LLM Config**: Flexible LLM configuration (supports custom models)
4. **Document Parser**: Utilities for parsing various document formats
5. **Main Agent**: Orchestrates everything using `create_deep_agent()`

## 🎨 Customization

### Using a Different LLM

```python
from langchain_anthropic import ChatAnthropic

# Use Claude instead of Qwen
model = ChatAnthropic(model="claude-3-5-sonnet-20241022")
agent = create_sharepoint_confluence_agent(use_custom_llm=False)
```

### Custom HITL Behavior

```python
from hitl_middleware import SelectiveHITLMiddleware

# Only require approval for deletions
custom_middleware = SelectiveHITLMiddleware(
    require_approval=["confluence_delete_page", "sharepoint_delete_item"],
)

agent = create_deep_agent(
    tools=[...],
    middleware=[custom_middleware],
)
```

### Adding Custom Tools

```python
from langchain_core.tools import tool

@tool
def custom_search(query: str) -> str:
    """Custom search implementation."""
    # Your code here
    return results

# Add to agent
agent = create_deep_agent(
    tools=CONFLUENCE_TOOLS + SHAREPOINT_TOOLS + [custom_search],
)
```

## 🐛 Troubleshooting

### Confluence Issues

**Problem**: `401 Unauthorized`
- **Solution**: Check that your `CONFLUENCE_PERSONAL_TOKEN` is correct and not expired

**Problem**: `404 Not Found`
- **Solution**: Verify the `CONFLUENCE_URL` is correct (no trailing slash)

### SharePoint Issues

**Problem**: `401 Unauthorized` or `403 Forbidden`
- **Solution**:
  1. Verify all SharePoint credentials are correct
  2. Check that API permissions are granted in Azure AD
  3. Ensure admin consent is granted for the permissions

**Problem**: `Invalid client secret`
- **Solution**: Generate a new client secret and update `.env`

### LLM Issues

**Problem**: LLM connection fails
- **Solution**:
  1. Check `LLM_API_BASE` is correct (should end with `/v1`)
  2. Verify `LLM_API_KEY` is valid
  3. Test the endpoint with curl:
     ```bash
     curl -H "Authorization: Bearer $LLM_API_KEY" \
          -H "X-API-Key: $LLM_API_KEY" \
          $LLM_API_BASE/models
     ```

### Document Parsing Issues

**Problem**: `Module not found` errors
- **Solution**: Install the required dependencies:
  ```bash
  pip install PyPDF2 python-docx python-pptx openpyxl Pillow
  ```

## 📊 Performance Considerations

- **Large Documents**: Parsing large documents (>10MB) may take time
- **API Rate Limits**: Be mindful of Confluence/SharePoint rate limits for bulk operations
- **Multimodal Processing**: Image analysis uses additional LLM tokens
- **Streaming**: The agent supports streaming for real-time responses

## 🔒 Security Best Practices

1. **Never commit `.env`** to version control
2. **Use environment variables** for all credentials
3. **Enable HITL** for production use
4. **Audit logs**: Enable logging for compliance
5. **Principle of least privilege**: Grant only necessary permissions
6. **Rotate secrets** regularly

## 📝 License

This project is part of the DeepAgents framework. See the main repository for license information.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📞 Support

For issues or questions:
- Check the [troubleshooting section](#-troubleshooting)
- Review the [DeepAgents documentation](../../README.md)
- Open an issue in the GitHub repository

## 🙏 Acknowledgments

- Built on the [DeepAgents](../../README.md) framework
- Uses [LangChain](https://langchain.com) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Integrates with Qwen/QVQ-72B-Preview multimodal LLM

---

**Happy document managing! 🚀**
