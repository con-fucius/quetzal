# Running agents

You can run agents via the [`Runner`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.Runner "Runner") class. You have 3 options:

1. [`Runner.run()`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.Runner.run "run            async       classmethod   "), which runs async and returns a [`RunResult`](https://openai.github.io/openai-agents-python/ref/result/#agents.result.RunResult "RunResult            dataclass   ").
2. [`Runner.run_sync()`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.Runner.run_sync "run_sync            classmethod   "), which is a sync method and just runs `.run()` under the hood.
3. [`Runner.run_streamed()`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.Runner.run_streamed "run_streamed            classmethod   "), which runs async and returns a [`RunResultStreaming`](https://openai.github.io/openai-agents-python/ref/result/#agents.result.RunResultStreaming "RunResultStreaming            dataclass   "). It calls the LLM in streaming mode, and streams those events to you as they are received.

```python
from agents import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")

    result = await Runner.run(agent, "Write a haiku about recursion in programming.")
    print(result.final_output)
    # Code within the code,
    # Functions calling themselves,
    # Infinite loop's dance.
```

Read more in the [results guide](https://openai.github.io/openai-agents-python/results/).

## The agent loop

When you use the run method in `Runner`, you pass in a starting agent and input. The input can either be a string (which is considered a user message), or a list of input items, which are the items in the OpenAI Responses API.

The runner then runs a loop:

1. We call the LLM for the current agent, with the current input.
2. The LLM produces its output.
   1. If the LLM returns a `final_output`, the loop ends and we return the result.
   2. If the LLM does a handoff, we update the current agent and input, and re-run the loop.
   3. If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop.
3. If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`](https://openai.github.io/openai-agents-python/ref/exceptions/#agents.exceptions.MaxTurnsExceeded "MaxTurnsExceeded") exception.

## Streaming

Streaming allows you to additionally receive streaming events as the LLM runs. Once the stream is done, the [`RunResultStreaming`](https://openai.github.io/openai-agents-python/ref/result/#agents.result.RunResultStreaming "RunResultStreaming            dataclass   ") will contain the complete information about the run, including all the new outputs produces. You can call `.stream_events()` for the streaming events. Read more in the [streaming guide](https://openai.github.io/openai-agents-python/streaming/). 