---
name: agentscope-skill
description: Build, debug, and migrate Python applications using AgentScope 2.x. Consult this skill for AgentScope APIs, agent tools, multi-agent orchestration, and agent service deployment.
metadata:
  version: "0.2.0"
---

# AgentScope 2.0

AgentScope provides a ReAct agent SDK and a FastAPI-based agent service. This
skill targets **AgentScope 2.x**, verified against upstream `main` commit
`033a3613401a3e6cbd39608321579481f6bd0953` (2026-09-09), whose source version is
`2.0.8`. The skill's own version above is independent of the framework version.

## Establish the target version

AgentScope 1.x examples are not compatible with the 2.x API. Check the user's
installed version and source location before choosing examples:

```bash
python -c 'import agentscope; print(agentscope.__version__, agentscope.__file__)'
```

Python **3.11 or newer** is required. For a released 2.x version:

```bash
uv pip install 'agentscope>=2,<3'
```

When the user targets the latest source, reuse an existing checkout or clone
into a working directory chosen for the task:

```bash
git clone --branch main https://github.com/agentscope-ai/agentscope.git
# In an existing checkout, inspect local changes before updating:
git -C agentscope status --short
git -C agentscope pull --ff-only origin main
git -C agentscope rev-parse HEAD
uv pip install -e ./agentscope
```

Record the source revision when validating code. Do not assume PyPI's latest
release, the checked-out source, and the active Python environment are the same
version. Preserve a user's pinned 1.x environment unless migration is requested.

## Core API and a working example

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
- `AgentState` holds conversation and execution state. Agent configuration uses
  `ContextConfig`, `InjectionConfig`, `ModelConfig`, and `ReActConfig`.
  Middleware adds memory, RAG, tracing, and other hooks.

Save this example as `main.py`. Set `DASHSCOPE_API_KEY` and optionally
`DASHSCOPE_MODEL` to a model available to your account, then run `python main.py`:

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

Replace the example URL with an accessible image before sending the message.

## Find the implementation that fits the task

Browse the checked-out examples and relevant source before adapting code; names
and signatures can change after the baseline above. Prefer existing framework
features over recreating them.

| Task | Source / example entry points |
| --- | --- |
| Terminal agent, tools, workspace | `examples/console/`, `src/agentscope/console/`, `tool/`, `workspace/` |
| Model providers and credentials | `src/agentscope/model/`, `src/agentscope/credential/` |
| Messages, event streaming, HITL | `src/agentscope/message/`, `event/`, `permission/` |
| Context and persistent memory | `src/agentscope/agent/`, `state/`, `middleware/`, `examples/long_term_memory/` |
| MCP and agent skills | `src/agentscope/mcp/`, `skill/`, `tool/`, `examples/console/` |
| Multi-agent workflows | `examples/pipeline/`, `examples/a2a/`, `src/agentscope/app/` |
| Agent service and Web UI | `examples/agent_service/`, `examples/web_ui/`, `src/agentscope/app/` |
| Sandboxed tools | `examples/workspace/`, `src/agentscope/workspace/` |
| RAG | `examples/rag/`, `src/agentscope/rag/`, `src/agentscope/app/rag/` |
| Realtime voice | `examples/realtime/`, `src/agentscope/realtime/`, `src/agentscope/agent/_realtime/` |

Source shorthand such as `tool/` above is relative to `src/agentscope/`.
Use the [official documentation](https://docs.agentscope.io/) and
[upstream repository](https://github.com/agentscope-ai/agentscope) for current
concepts and examples. Do not assume the old `docs/tutorial/`,
`examples/functionality/`, `examples/workflows/`, or `examples/deployment/`
directories exist. The checked-in `docs/changelog.md` still describes the 1.0
transition at this baseline; inspect current source and `docs/NEWS.md` too.

Read these references only when relevant:

- [Multi-agent orchestration](references/multi_agent_orchestration.md): direct
  message passing, a worker as a tool, GoalPipeline, Agent Team, and A2A.
- [Deployment guide](references/deployment_guide.md): built-in agent service,
  storage/message bus, workspaces, and migration away from the old examples.

## Avoid mixing 1.x and 2.x

| Old example | 2.x approach |
| --- | --- |
| `ReActAgent`, `UserAgent`, `await agent(msg)` | `Agent`, `launch_console`, `await agent.reply(msg)` |
| `sys_prompt`, agent `memory=` / `formatter=` | `system_prompt`, `state=`, `middlewares=`; formatter on the model |
| `model_name=...`, model `api_key=...` | `model=...`, provider `credential=...` |
| `InMemoryMemory`, `RedisSession` | Agent state / middleware; service storage for sessions |
| `register_tool_function(fn)` | `Toolkit(tools=[FunctionTool(fn)])` |
| `execute_shell_command`, `execute_python_code` | Current built-in tools and workspace backends; inspect available execution tools |
| `ImageBlock`, positional `TextBlock(...)` / `Msg(...)` | `DataBlock`, `TextBlock(text=...)`, message factories or keyword fields |
| `MsgHub`, `stream_printing_messages` | Explicit `reply()` calls, `reply_stream()`, pipeline or service team APIs |

These are migration directions, not one-to-one semantic replacements. Check
return types and lifecycle behavior when porting a real application. Do not
claim evaluation/training APIs from older releases exist in the current SDK
without checking the target source.

## Inspect and validate APIs

The helper reads the **active Python environment**, not an arbitrary checkout:

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
