"""Various guard rails to ensure tester agent is only used for testing A2A agents under different scenarios."""

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    RunResult,
    Runner,
    TResponseInputItem,
    input_guardrail,
)
from openai import BaseModel


class EvaluationOutput(BaseModel):
    is_testing_agents: bool
    reasoning: str

guardrail_agent: Agent[None] = Agent(
    name="Guardrail check",
    instructions="Check that the user is indeed conversing with the testing agent for testing other A2A agents in various scenarios.",
    output_type=EvaluationOutput,
)

@input_guardrail
async def testing_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """"""

    result: RunResult = await Runner.run(
        starting_agent=guardrail_agent,
        input=input,
        context=ctx.context)

    output: EvaluationOutput = result.final_output_as(
        cls=EvaluationOutput,
        raise_if_incorrect_type=True,
    )

    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=output.is_testing_agents,
    )
