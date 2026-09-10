---
name: agentscope-skill
description: Build and debug Python applications using AgentScope 2.x. Consult this skill for AgentScope APIs, agent tools, multi-agent orchestration, and agent service deployment.
metadata:
  version: "0.2.0"
---

# AgentScope 2.0

AgentScope is an open-source framework for building and serving LLM-powered
agent applications, from a single tool-using agent to coordinated multi-agent
systems. It provides application orchestration and service infrastructure;
model inference comes from configured providers, and tools execute through
configured local or sandbox backends. It consists of two layers:

- **Agent SDK:** Building blocks for agent applications, including agents,
  models, messages, tools, context and state management, middleware, memory,
  RAG, multi-agent orchestration, and workspaces.
- **Service:** A service layer built on the SDK, providing APIs for agent and
  session management, persistence, teams, scheduling, channels, and resource
  management, with a Web UI example.

This skill supports **AgentScope 2.x** and is based on **2.0.8**. API signatures
and behavior should follow the SDK version actually installed in the user's
environment. `agentscope-runtime` and `agentscope-studio` are not compatible
with 2.x; use the built-in service and workspace capabilities instead.

## Installation

Python **3.11 or newer** is required.

```bash
pip install agentscope
# or
uv pip install agentscope
```

## Core Concepts and Basic Example

- `Agent` owns the reasoning/acting loop. Use `reply()` for a final `Msg`, or
  `reply_stream()` for events. `launch_console()` handles terminal interaction,
  tool confirmation, and interruption.
- Construct provider models with a credential object and `model=...`.
  Formatters still exist, but are configured on the model; providers select a
  default formatter. They are not passed to `Agent`.
- `Toolkit` accepts tool objects, MCP clients, and skill paths/loaders. Wrap a
  Python function with `FunctionTool`; use `ToolBase` for custom tool classes.
- `Msg` contains typed content blocks. `UserMsg`, `AssistantMsg`, and `SystemMsg`
  are convenience factories that also accept text strings. Binary media uses
  `DataBlock` with `URLSource` or `Base64Source`, including `media_type`.
- **Event:** Typed events expose agent execution to the application: reply and
  model-call lifecycle, streamed content, tool calls/results, and requests for
  confirmation or external execution. Consume them through `reply_stream()`;
  send interaction result events back to resume the agent. `Msg` represents
  conversation content, while events describe execution and interaction.
- `AgentState` holds conversation and execution state. Agent configuration uses
  `ContextConfig`, `InjectionConfig`, `ModelConfig`, and `ReActConfig`.
  Middleware adds memory, RAG, tracing, and other hooks.

The following example shows how to compose an agent with a model and a Python
function tool:

```python
import asyncio
import os

from agentscope.agent import Agent
from agentscope.console import launch_console
from agentscope.credential import DashScopeCredential
from agentscope.model import DashScopeChatModel
from agentscope.tool import FunctionTool, Toolkit


def add(a: int, b: int) -> str:
    """Add two integers.

    Args:
        a: First integer.
        b: Second integer.
    """
    return str(a + b)


async def main() -> None:
    agent = Agent(
        name="Friday",
        system_prompt="You are a helpful assistant named Friday.",
        model=DashScopeChatModel(
            credential=DashScopeCredential(
                api_key=os.environ["DASHSCOPE_API_KEY"],
            ),
            model=os.environ.get("DASHSCOPE_MODEL", "qwen3.6-plus"),
        ),
        toolkit=Toolkit(tools=[FunctionTool(add)]),
    )
    await launch_console(agent)


if __name__ == "__main__":
    asyncio.run(main())
```

For programmatic interaction, use the following inside an async function with
an existing `agent`:

```python
from agentscope.message import UserMsg

result = await agent.reply(UserMsg(name="user", content="Hello!"))
print(result.get_text_content())
```

`reply()` consumes stream events. If a tool needs confirmation or external
execution, a custom UI should consume `reply_stream()` and feed the appropriate
`UserConfirmResultEvent` or `ExternalExecutionResultEvent` back to resume. The
stream may end while waiting for that input; do not treat every stream end as
successful completion. Use the console implementation and event schemas as the
reference for this lifecycle. `FunctionTool` requests permission by default.

For multimodal input, use a model that supports the supplied media type:

```python
from agentscope.message import DataBlock, TextBlock, URLSource, UserMsg

message = UserMsg(
    name="user",
    content=[
        TextBlock(text="Describe this image."),
        DataBlock(
            source=URLSource(
                url="https://example.com/image.png",
                media_type="image/png",
            ),
        ),
    ],
)
```

## Working with the Repository

Reuse an existing AgentScope checkout or clone the repository to inspect its
examples and implementations before writing application code:

```bash
git clone --branch main https://github.com/agentscope-ai/agentscope.git
# Inspect local changes before updating an existing checkout.
git -C agentscope status --short
git -C agentscope pull --ff-only origin main
```

### Repository Structure

```text
agentscope/
├── src/agentscope/
│   ├── agent/          # Agents and their configuration
│   ├── model/          # Chat model providers
│   ├── credential/     # Provider credentials
│   ├── console/        # Terminal interaction and event rendering
│   ├── formatter/      # Provider-specific message formatting
│   ├── message/        # Messages and typed content blocks
│   ├── tool/           # Toolkit, adapters, and built-in tools
│   ├── mcp/            # MCP clients and configuration
│   ├── skill/          # Skill loading
│   ├── state/          # Agent conversation and execution state
│   ├── middleware/     # Hooks, memory, RAG, tracing, and budgets
│   ├── event/          # Streaming and interaction events
│   ├── permission/     # Tool permissions and human confirmation
│   ├── pipeline/       # Multi-agent workflow abstractions
│   ├── workspace/      # Local and sandboxed execution backends
│   ├── rag/            # Retrieval building blocks
│   ├── embedding/      # Embedding model providers
│   ├── realtime/       # Realtime model interfaces
│   ├── tts/            # Text-to-speech models
│   └── app/            # Service APIs, storage, teams, channels, and hubs
├── examples/
│   ├── console/        # Terminal agent composition
│   ├── agent_service/  # Service configuration
│   ├── web_ui/         # Service frontend
│   ├── pipeline/       # Executor/verifier workflow
│   ├── a2a/            # Remote agent communication
│   ├── long_term_memory/
│   ├── rag/
│   ├── realtime/
│   └── workspace/
├── docs/               # News, roadmap, and changelog
└── tests/              # SDK and service behavior tests
```

Confirm the actual directory layout when browsing a checkout. Start with the
example category matching the task, read its README and code, then follow its
imports into `src/agentscope/`. Search within those directories for the needed
classes or features. Prefer existing framework capabilities over recreating
them; check base classes and inherited methods before adding custom behavior.

## Resources

### Official Documentation

- [AgentScope documentation](https://docs.agentscope.io/): Concepts, API usage,
  and guides for the SDK and service layers.

### GitHub Resources

- [Main repository](https://github.com/agentscope-ai/agentscope): Source code,
  examples, and tests.
- [Examples](https://github.com/agentscope-ai/agentscope/tree/main/examples):
  Reference implementations organized by functionality.
- [Roadmap](https://github.com/agentscope-ai/agentscope/blob/main/docs/roadmap.md):
  Development directions.
- [Project board](https://github.com/orgs/agentscope-ai/projects/2): Development
  task tracking.
- [Discussions](https://github.com/agentscope-ai/agentscope/discussions):
  Community questions, ideas, and framework design discussions.

### References

Read these local references when the task needs more detail:

- [Multi-agent orchestration](references/multi_agent_orchestration.md): Direct
  message passing, a worker as a tool, GoalPipeline, Agent Team, and A2A.
- [Deployment guide](references/deployment_guide.md): Built-in service,
  storage, message buses, workspaces, and sandbox backends.

### Scripts

- `view_module_signature.py`: Inspect modules, classes, and methods in the
  **active Python environment**, including inherited APIs and source locations.
- `view_pypi_latest_version.sh`: Query the latest published AgentScope version.

Example queries:

```bash
python /path/to/agentscope-skill/scripts/view_module_signature.py --module agentscope
python /path/to/agentscope-skill/scripts/view_module_signature.py --module agentscope.agent.Agent
python /path/to/agentscope-skill/scripts/view_module_signature.py --module agentscope.agent.Agent.reply_stream
python /path/to/agentscope-skill/scripts/view_module_signature.py --module agentscope.app.storage
bash /path/to/agentscope-skill/scripts/view_pypi_latest_version.sh
```

Module discovery does not import all optional integrations. Missing optional
imports are reported; install only extras needed for the task, using the target
`pyproject.toml` (for example `service`, `model-gemini`, or `model-ollama`).
The PyPI helper reports release metadata only, not the installed version.

Before delivering code, check public exports, constructor/method signatures,
inherited methods, and cleanup requirements. Validate examples with the target
version; use a fake model for offline behavior checks and distinguish those
checks from actual provider, Redis, container, or deployment runs.
