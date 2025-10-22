"""Various guard rails to ensure tester agent is only used for testing A2A agents under different scenarios."""

from agents import (
    Agent,
    AgentOutputSchema,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    RunResult,
    TResponseInputItem,
    input_guardrail,
)
from openai import BaseModel


class EvaluationOutput(BaseModel):
    is_about_weather: bool
    reasoning: str

guardrail_agent: Agent[None] = Agent(
    name="Guardrail check",
    instructions="Check that the user is indeed conversing about weather and/or air quality",
    output_type=AgentOutputSchema(output_type=EvaluationOutput, strict_json_schema=False),
)

@input_guardrail
async def weather_only_guardrail(
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
        tripwire_triggered=not output.is_about_weather,
    )
