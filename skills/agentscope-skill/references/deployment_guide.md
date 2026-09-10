# Deployment in AgentScope 2.x

Use the version baseline in [SKILL.md](../SKILL.md). AgentScope 2.x includes a
FastAPI app factory, service storage, message buses, and workspace backends.
Start with these built-in APIs for a new 2.x application. The old guide's
`agentscope_runtime.AgentApp`, `RedisSession`, and `BaseSandbox` snippets are
not examples for this SDK. Projects using the separate AgentScope Runtime
package need their own compatibility check; do not infer that it is deprecated.

## Built-in agent service

Install the service extra in the target environment:

```bash
uv pip install 'agentscope[service,storage-redis]>=2,<3'
# If targeting a source checkout instead:
# uv pip install -e './agentscope[service,storage-redis]'
```

Save this as `main.py`. It requires a running Redis server at localhost:6379.
Start it with `uvicorn main:app --host 127.0.0.1 --port 8000`:

```python
from agentscope.app import create_app
from agentscope.app.message_bus import InMemoryMessageBus
from agentscope.app.storage import RedisStorage
from agentscope.app.workspace_manager import LocalWorkspaceManager

app = create_app(
    storage=RedisStorage(host="localhost", port=6379),
    message_bus=InMemoryMessageBus(),
    workspace_manager=LocalWorkspaceManager(basedir="./workspaces"),
)
```

This assembles the service; it does not provision a user, model credential, or
configured agent. Follow `examples/agent_service/README.md` and
`examples/web_ui/` for those steps and the frontend. The FastAPI lifespan manages
storage, message bus, and workspace manager resources.

- **Storage** persists service records and sessions. `RedisStorage` is one
  backend; inspect `AsyncSQLAlchemyStorage` and its optional dependencies if
  using SQL. SDK `AgentState` is not a service session database.
- **Message bus** carries live messages independently of storage.
  `InMemoryMessageBus` is for a single process. Use a shared transport such as
  `RedisMessageBus` for multi-process service coordination.
- **Workspace manager** provisions tool environments and workspace isolation.
  Configure it according to the intended user/agent/session lifetime.
- **Resource access** is configurable via `resource_access_policy`; inspect
  `agentscope.app.access` when adding application authorization. The default
  sharing policy is not a substitute for the host application's authentication.

Read the upstream service example before adding team templates, scheduling,
channels, RAG indexing, MCP hubs, or skill hubs. Install the additional extras
needed by those integrations rather than copying every optional integration
into a minimal service.

## Workspace-backed coding tools

Use a workspace to provide tools and an offloader with a shared execution
backend. This runnable terminal example uses a local working directory:

```python
import asyncio
import os

from agentscope.agent import Agent
from agentscope.console import launch_console
from agentscope.credential import DashScopeCredential
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit
from agentscope.workspace import LocalWorkspace


async def main() -> None:
    async with LocalWorkspace(workdir="./workspace") as workspace:
        agent = Agent(
            name="Coder",
            system_prompt="Help with coding tasks in the workspace.",
            model=DashScopeChatModel(
                credential=DashScopeCredential(
                    api_key=os.environ["DASHSCOPE_API_KEY"],
                ),
                model=os.environ.get("DASHSCOPE_MODEL", "qwen3.6-plus"),
            ),
            toolkit=Toolkit(tools=await workspace.list_tools()),
            offloader=workspace,
        )
        await launch_console(agent)


if __name__ == "__main__":
    asyncio.run(main())
```

`LocalWorkspace` executes on the host; it is not a container security boundary.
For isolated execution, inspect `examples/workspace/` for `DockerWorkspace`,
`BubblewrapWorkspace`, `AppleContainerWorkspace`, or a remote workspace backend
such as E2B, OpenSandbox, Daytona, or Kubernetes. Check each backend's runtime
and dependency requirements and keep its context manager open while tools run.

For file-backed long-term memory, see `AgenticMemoryMiddleware` and
`examples/console/`. Bind its backend and working directory to the selected
workspace. MCP clients and skill loaders can be supplied through `Toolkit`;
use the workspace APIs if skills need to be installed and persisted there.

## Validation boundaries

Validate import and app construction separately from service startup, Redis
connectivity, provider calls, and container execution. A no-network smoke test
does not prove those external dependencies work. For a custom frontend, use the
current event API to implement tool confirmation, interruption, and resumption;
`stream_printing_messages` is not a 2.x streaming interface.

References: [official docs](https://docs.agentscope.io/),
[service example](https://github.com/agentscope-ai/agentscope/tree/main/examples/agent_service),
[workspace examples](https://github.com/agentscope-ai/agentscope/tree/main/examples/workspace).
