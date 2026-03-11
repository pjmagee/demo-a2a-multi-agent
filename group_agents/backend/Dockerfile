FROM python:3.13-slim
WORKDIR /app

RUN pip install uv

COPY group_agents/backend /app/group_agents/backend

WORKDIR /app/group_agents/backend

RUN uv sync --no-cache --no-dev

EXPOSE 8050

CMD ["uv", "run", "python", "-m", "group_chat_backend.app"]
