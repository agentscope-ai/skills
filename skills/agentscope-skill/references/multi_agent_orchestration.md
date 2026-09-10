# Multi-Agent Orchestration in AgentScope 2.x

Choose the orchestration mechanism based on who controls execution: application
code, a leader agent, a pipeline, or the service layer.

## Explicit message passing

Use ordinary Python control flow when the application controls the order.
Agents do not automatically observe another agent's replies. Each agent keeps
its own state, so pass the messages that the next agent should see explicitly.

Inside an async function, with two configured `Agent` instances:

```python
from agentscope.message import UserMsg

request = UserMsg(name="user", content="Propose a short implementation plan.")
proposal = await alice.reply(request)
review = await bob.reply(
    [
        proposal,
        UserMsg(name="user", content="Review this plan for missing steps."),
    ],
)
```

This example assumes neither agent is waiting on external input. If agents use
tools requiring confirmation, consume their events and route the response back
to the agent that requested it. Do not share one mutable agent instance across
concurrent independent conversations.

## Worker as a function tool

Use this pattern when a leader model chooses when to delegate. This example
gives the worker no tools, so its reply does not require nested tool
confirmation.

```python
import asyncio
import os

from agentscope.agent import Agent
from agentscope.console import launch_console
from agentscope.credential import DashScopeCredential
from agentscope.message import UserMsg
from agentscope.model import DashScopeChatModel
from agentscope.tool import FunctionTool, Toolkit
from agentscope.types import ReplyFinishedReason


def make_model() -> DashScopeChatModel:
    return DashScopeChatModel(
        credential=DashScopeCredential(
            api_key=os.environ["DASHSCOPE_API_KEY"],
        ),
        model=os.environ.get("DASHSCOPE_MODEL", "qwen3.6-plus"),
    )


async def consult_worker(task: str) -> str:
    """Ask a worker to analyze a self-contained task.

    Args:
        task: The task and all context the worker needs.
    """
    worker = Agent(
        name="Worker",
        system_prompt="Analyze the task and return a concise recommendation.",
        model=make_model(),
    )
    result = await worker.reply(UserMsg(name="leader", content=task))
    if result.finished_reason != ReplyFinishedReason.COMPLETED:
        raise RuntimeError(
            f"Worker did not complete: {result.finished_reason}, {result.error}",
        )
    return result.get_text_content()


async def main() -> None:
    leader = Agent(
        name="Leader",
        system_prompt="Use consult_worker when specialist analysis is useful.",
        model=make_model(),
        toolkit=Toolkit(tools=[FunctionTool(consult_worker)]),
    )
    await launch_console(leader)


if __name__ == "__main__":
    asyncio.run(main())
```

`FunctionTool` normalizes the returned string into tool content. Do not yield
raw agent events or `Msg` objects as tool results. For custom streaming tools,
inspect `ToolChunk` and `FunctionTool.call` in the target source. If a worker
also needs tool confirmation, design explicit event forwarding and resumption;
a simple `await worker.reply(...)` wrapper does not handle that interaction.

## Executor/verifier loop

`GoalPipeline` runs an executor until a verifier accepts the result or the
iteration limit is reached. With existing executor and verifier agents:

```python
from agentscope.console import launch_console
from agentscope.pipeline import GoalPipeline

pipeline = GoalPipeline(executor=executor, verifier=verifier, max_iters=5)
await launch_console(pipeline)
```

The goal arrives as the initial input, not a constructor `goal` argument.
Use `reply_stream()` for a custom frontend and route confirmation events back
to the pipeline. The pipeline tracks the parked agent and iteration budget.
A verifier reviewing generated files needs access to the relevant workspace.
See `examples/pipeline/goal/` for the full implementation; choose permission
settings for the application rather than copying a demo's bypass mode.

## Service teams and remote agents

- **Agent Team:** For persistent leader/worker coordination within the agent
  service, inspect `examples/agent_service/`, `agentscope.app.SubAgentTemplate`,
  and the team implementation under `src/agentscope/app/`. The service manages
  team sessions and tools.
- **A2A:** Use `agentscope.agent.A2AAgent` when communicating with a remote A2A
  agent. Start from `examples/a2a/` and check the target constructor and optional
  dependencies before configuring the remote endpoint.

For service-backed workflows, continue with the
[deployment guide](deployment_guide.md). Source examples:
[GoalPipeline](https://github.com/agentscope-ai/agentscope/tree/main/examples/pipeline/goal),
[agent service](https://github.com/agentscope-ai/agentscope/tree/main/examples/agent_service),
[A2A](https://github.com/agentscope-ai/agentscope/tree/main/examples/a2a).
