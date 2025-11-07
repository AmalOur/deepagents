# Setup Instructions for SharePoint & Confluence DeepAgent

## Quick Start Guide

### 1. Install Dependencies

```bash
# Navigate to the agent directory
cd examples/sharepoint_confluence_agent

# Install required packages
pip install -r requirements.txt

# Install the DeepAgents framework (from repository root)
cd ../../libs/deepagents
pip install -e .
cd ../../examples/sharepoint_confluence_agent
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual credentials
nano .env  # or use your preferred editor
```

### 3. Set Up Confluence (If Using)

**Required Information:**
- Confluence instance URL
- Personal Access Token

**Update in `.env`:**
```env
CONFLUENCE_URL=https://your-confluence-instance.com
CONFLUENCE_PERSONAL_TOKEN=your-base64-token
```

**How to get Confluence Personal Access Token:**
1. Log in to your Confluence instance
2. Go to **Settings** > **Personal Access Tokens**
3. Create a new token with appropriate permissions
4. The token should be base64 encoded: `echo -n 'email:token' | base64`

### 4. Set Up SharePoint (If Using)

**Required Information:**
- SharePoint site URL
- Azure AD application credentials

**Update in `.env`:**
```env
SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com/sites/yoursite
SHAREPOINT_CLIENT_ID=your-client-id
SHAREPOINT_CLIENT_SECRET=your-client-secret
SHAREPOINT_TENANT_ID=your-tenant-id
```

**How to get SharePoint credentials:**

#### 4.1. Register an Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in:
   - **Name**: SharePoint DeepAgent (or your preferred name)
   - **Supported account types**: Single tenant
   - **Redirect URI**: Leave empty for now
5. Click **Register**

#### 4.2. Get Application IDs

1. In the app overview page, copy:
   - **Application (client) ID** → `SHAREPOINT_CLIENT_ID`
   - **Directory (tenant) ID** → `SHAREPOINT_TENANT_ID`

#### 4.3. Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description and set expiration
4. Click **Add**
5. **IMPORTANT**: Copy the **Value** immediately (not the Secret ID)
   - This is your `SHAREPOINT_CLIENT_SECRET`
   - You won't be able to see it again!

#### 4.4. Grant API Permissions

1. Go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Select **Application permissions**
5. Add these permissions:
   - `Sites.Read.All` (to read SharePoint sites)
   - `Sites.ReadWrite.All` (to write to SharePoint sites)
   - `Files.Read.All` (to read files)
   - `Files.ReadWrite.All` (to write files)
   - `User.Read` (to read user info)
6. Click **Add permissions**
7. **CRITICAL**: Click **Grant admin consent for [your organization]**
   - This must be done by an admin
   - Without this, the app won't work

### 5. Configure Custom LLM (Qwen Model)

**Update in `.env`:**
```env
LLM_MODEL_NAME=Qwen/QVQ-72B-Preview
LLM_API_BASE=https://your-model-endpoint.com/v1
LLM_API_KEY=your-api-key
```

**Notes:**
- The model is OpenAI-compatible
- Supports multimodal input (text + images)
- Replace with your actual model endpoint and API key
- The agent will work with any OpenAI-compatible API

### 6. Test Your Configuration

```bash
# Test environment variables are loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ Confluence URL:', os.getenv('CONFLUENCE_URL')); print('✓ LLM Model:', os.getenv('LLM_MODEL_NAME'))"
```

### 7. Run the Agent

```bash
# Interactive mode
python sharepoint_confluence_agent.py
```

**Example interactions:**
```
You: Search for Q4 roadmap in Confluence
Agent: I found 3 pages matching "Q4 roadmap"...

You: Download the first PDF and summarize it
Agent: [Downloads and analyzes the document]...

You: Create a new page with title "Meeting Notes"
Agent: [Requests approval] 🚨 APPROVAL REQUIRED...
```

## Programmatic Usage

```python
from sharepoint_confluence_agent import create_sharepoint_confluence_agent

# Create the agent
agent = create_sharepoint_confluence_agent()

# Run a query
config = {"configurable": {"thread_id": "my-session"}}
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Search for documentation"}]},
    config,
)

print(result)
```

## Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Confluence 401 Unauthorized

**Solution:**
- Verify `CONFLUENCE_PERSONAL_TOKEN` is correct
- Check token hasn't expired
- Ensure token has proper permissions

### Issue: SharePoint 403 Forbidden

**Solution:**
- Verify all Azure AD credentials are correct
- Check that API permissions are granted
- Ensure admin consent is granted
- Verify the service principal has access to the site

### Issue: LLM connection fails

**Solution:**
- Check `LLM_API_BASE` is correct (should end with `/v1`)
- Verify `LLM_API_KEY` is valid
- Test endpoint manually:
  ```bash
  curl -H "Authorization: Bearer $LLM_API_KEY" \
       -H "X-API-Key: $LLM_API_KEY" \
       $LLM_API_BASE/models
  ```

## Security Notes

1. **Never commit `.env`** to version control
2. Add `.env` to `.gitignore`
3. Rotate secrets regularly
4. Use environment-specific credentials (dev/staging/prod)
5. Grant minimum required permissions
6. Enable human-in-the-loop for production use
7. Review audit logs regularly (if logging enabled)

## Next Steps

1. Read the [README.md](README.md) for detailed documentation
2. Explore example workflows in the README
3. Customize the agent for your specific use case
4. Set up logging and monitoring
5. Configure additional middleware if needed

## Getting Help

- Check [README.md](README.md) for comprehensive documentation
- Review [DeepAgents documentation](../../README.md)
- Open an issue on GitHub for bugs or questions

---

**You're all set! Happy document managing! 🚀**
