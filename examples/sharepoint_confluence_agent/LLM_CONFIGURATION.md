# LLM Configuration Guide

## Default Configuration (Recommended)

By default, the SharePoint/Confluence DeepAgent uses **Claude** (via Anthropic API) as the LLM. This is the recommended configuration because:

- ✅ Full tool calling support
- ✅ Native integration with DeepAgents
- ✅ Excellent reasoning capabilities
- ✅ Reliable and well-tested

**No additional configuration needed** - just run the agent!

## Using Custom LLMs (Advanced)

### Requirements for Custom LLMs

To use a custom LLM with this agent, your model **must support**:

1. **Tool Calling / Function Calling** - The agent uses tools extensively
2. **OpenAI-Compatible API** - Must support the OpenAI API format
3. **Proper Tool Call Format** - Must return tool calls in the expected format

### Qwen/QVQ-72B-Preview Configuration

The Qwen/QVQ-72B-Preview model is currently **not fully compatible** with the agent due to tool calling limitations.

**Issue**: The Qwen endpoint returns this error:
```
"auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set
```

**Workaround Options**:

1. **Use Claude (Recommended)**
   - No configuration needed
   - Works out of the box

2. **Configure Qwen endpoint to support tool calling**
   - Contact your model provider to enable:
     - `--enable-auto-tool-choice`
     - `--tool-call-parser`
   - Update your endpoint configuration

3. **Use a different OpenAI-compatible model** that supports tool calling:
   - OpenAI GPT-4
   - Azure OpenAI
   - Together AI
   - Groq
   - Any other provider with tool calling support

### How to Enable Custom LLM

If you have a compatible custom LLM, configure it in `.env`:

```env
# LLM Configuration
LLM_MODEL_NAME=your-model-name
LLM_API_BASE=https://your-endpoint.com/v1
LLM_API_KEY=your-api-key
```

Then enable it when creating the agent:

```python
# In sharepoint_confluence_agent.py, change line 158:
use_custom_llm: bool = True  # Enable custom LLM
```

Or programmatically:

```python
from sharepoint_confluence_agent import create_sharepoint_confluence_agent

# Use custom LLM
agent = create_sharepoint_confluence_agent(use_custom_llm=True)

# Use default Claude (recommended)
agent = create_sharepoint_confluence_agent(use_custom_llm=False)
```

### Testing Your Custom LLM

To test if your custom LLM supports tool calling:

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# Define a test tool
@tool
def test_tool(input: str) -> str:
    """A test tool."""
    return f"Received: {input}"

# Test the LLM
llm = ChatOpenAI(
    model="your-model",
    openai_api_base="your-endpoint",
    openai_api_key="your-key",
)

# Bind tools and test
llm_with_tools = llm.bind_tools([test_tool])
response = llm_with_tools.invoke("Use the test tool with input 'hello'")

print(response)
# Should return tool calls, not just text
```

## Anthropic API Key Setup (For Default Claude)

To use the default Claude model, you need an Anthropic API key:

1. **Get API Key**:
   - Sign up at https://console.anthropic.com
   - Navigate to API Keys
   - Create a new key

2. **Set Environment Variable**:
   ```bash
   # Linux/Mac
   export ANTHROPIC_API_KEY=your-key-here

   # Windows
   set ANTHROPIC_API_KEY=your-key-here

   # Or add to .env file
   echo "ANTHROPIC_API_KEY=your-key-here" >> .env
   ```

3. **Run the Agent**:
   ```bash
   python sharepoint_confluence_agent.py
   ```

## Model Comparison

| Model | Tool Support | Multimodal | Setup Complexity | Cost |
|-------|--------------|------------|------------------|------|
| Claude (Default) | ✅ Excellent | ✅ Yes | ⭐ Easy | $$ |
| OpenAI GPT-4 | ✅ Excellent | ✅ Yes | ⭐ Easy | $$$ |
| Qwen/QVQ-72B | ❌ Limited* | ✅ Yes | ⭐⭐⭐ Complex | $ |
| Together AI | ✅ Good | ✅ Yes | ⭐⭐ Medium | $ |
| Groq | ✅ Good | ❌ No | ⭐⭐ Medium | $ |

*Requires endpoint configuration

## Troubleshooting

### Error: "auto" tool choice requires...

**Problem**: Your custom LLM doesn't support tool calling properly.

**Solution**: Use Claude (default) or switch to a compatible model.

### Error: No API key found

**Problem**: Missing `ANTHROPIC_API_KEY` for default Claude model.

**Solution**: Set the environment variable:
```bash
export ANTHROPIC_API_KEY=your-key
```

### Error: Module 'langchain_anthropic' not found

**Problem**: Missing dependency.

**Solution**: Install it:
```bash
pip install langchain-anthropic
```

## Recommendations

1. **Start with Claude** - It just works
2. **Test custom LLMs** - Verify tool calling support before deploying
3. **Monitor costs** - Different models have different pricing
4. **Check context limits** - Ensure your model supports enough tokens for complex operations

---

**Need help?** Check the main [README.md](README.md) or open an issue.
