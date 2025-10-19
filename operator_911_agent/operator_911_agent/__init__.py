"""911 Operator Agent package."""

from agents import enable_verbose_stdout_logging, set_tracing_disabled

enable_verbose_stdout_logging()
set_tracing_disabled(disabled=True)

__all__: list[str] = ["Operator911Agent"]