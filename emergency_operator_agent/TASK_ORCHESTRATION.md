# Task-Based Orchestration Architecture

## Overview

Implemented a **task-based orchestration pattern** for the emergency operator that provides explicit workflow management with step-by-step execution and progress tracking through SSE.

## Architecture Comparison

### Current Implementation (executor.py)

**Pattern**: Agent-driven with callbacks

- OpenAI Agent decides what to do on-the-fly
- Tools (list_agents, send_message) called by agent
- SSE updates sent via callbacks
- No explicit task plan or step tracking

**Pros**:

- Flexible - agent can adapt to different scenarios
- Natural language understanding
- Can handle non-standard requests

**Cons**:

- No visibility into planned steps before execution
- Hard to track progress (where are we in the workflow?)
- Difficult to resume/retry failed steps
- Task store underutilized

### New Implementation (task_executor.py + task_orchestrator.py)

**Pattern**: Explicit workflow orchestration

1. **Plan**: Analyze emergency → Create task with steps
2. **Store**: Task plan stored in memory (can persist to task_store)
3. **Execute**: Loop through steps sequentially
4. **Track**: Each step has status (pending/working/completed/failed)
5. **Stream**: SSE update after each step

**Pros**:

- **Explicit plan** visible before execution
- **Progress tracking**: "Step 2 of 3 dispatching..."
- **Resumability**: Can save/restore task state
- **Visibility**: See which services will be contacted upfront
- **Failure handling**: Know exactly which step failed
- **Testing**: Can mock individual steps

**Cons**:

- Less flexible - predefined workflow
- Keyword-based analysis (would need LLM for production)
- More code to maintain

## New Components

### 1. EmergencyTask (Dataclass)

```python
@dataclass
class EmergencyTask:
    task_id: str
    context_id: str
    location: str
    description: str
    steps: list[DispatchStep]
    current_step: int = 0
    state: TaskState = TaskState.pending
```

Represents the complete dispatch workflow with:

- Task metadata (id, location, description)
- List of dispatch steps
- Current progress tracker
- Overall task state

### 2. DispatchStep (Dataclass)

```python
@dataclass
class DispatchStep:
    step_id: str
    service_type: ServiceType  # FIRE, POLICE, AMBULANCE
    agent_name: str
    message: str
    status: TaskState  # pending/working/completed/failed
    response: str | None
    error: str | None
```

Each step represents contacting one emergency service.

### 3. EmergencyTaskOrchestrator

Main orchestration engine that:

- **Analyzes** emergency calls to create task plans
- **Executes** tasks step-by-step
- **Tracks** active tasks
- **Streams** SSE updates at each step

Key methods:

```python
async def create_task_plan(...) -> EmergencyTask
    # Analyze request, identify needed services, create plan

async def execute_task(task: EmergencyTask, event_queue: EventQueue)
    # Execute all steps sequentially with SSE updates
```

### 4. TaskOrchestratedExecutor

Replaces `OperatorAgentExecutor`, implements `AgentExecutor` interface:

```python
async def execute(context: RequestContext, event_queue: EventQueue):
    # Phase 1: Create plan
    task = await orchestrator.create_task_plan(...)
    
    # Phase 2: Execute plan
    await orchestrator.execute_task(task, event_queue)
```

## SSE Message Flow Example

### Input

```
"hi, can you help? 170 London road SM6 7AN. Fire, Injuries and a citizen arrested criminal."
```

### SSE Stream Output

```
event: task_status_update
data: {"state": "working", "message": "Emergency operator analyzing call..."}

event: message
data: {"text": "🚨 Emergency call received. Analyzing situation..."}

event: message
data: {"text": "📋 Dispatch plan created: Fire Brigade Agent, Police Agent, Ambulance Agent"}

event: message
data: {"text": "[1/3] Dispatching Fire Brigade Agent..."}

event: message
data: {"text": "✅ [1/3] Fire Brigade Agent dispatched successfully"}

event: message
data: {"text": "[2/3] Dispatching Police Agent..."}

event: message
data: {"text": "✅ [2/3] Police Agent dispatched successfully"}

event: message
data: {"text": "[3/3] Dispatching Ambulance Agent..."}

event: message
data: {"text": "✅ [3/3] Ambulance Agent dispatched successfully"}

event: message
data: {"text": "✅ All emergency services dispatched successfully (3/3)"}

event: task_status_update
data: {"state": "completed", "message": "Emergency dispatch completed", "final": true}
```

## Key Improvements

### 1. Explicit Task Plan

**Before**: Agent decides on-the-fly, user doesn't know what will happen

```
"Emergency help is on the way..."
[internal: agent calls tools, user waits]
```

**After**: User sees the plan immediately

```
"📋 Dispatch plan created: Fire Brigade Agent, Police Agent, Ambulance Agent"
[then executes step by step]
```

### 2. Progress Tracking

**Before**: No indication of progress

```
"Dispatching to Fire Brigade Agent..."
"Received response from Fire Brigade Agent"
```

**After**: Clear progress indicators

```
"[1/3] Dispatching Fire Brigade Agent..."
"✅ [1/3] Fire Brigade Agent dispatched successfully"
"[2/3] Dispatching Police Agent..."
```

### 3. Structured Failure Handling

**Before**: Generic error, unclear what failed

```
"Error processing call: connection timeout"
```

**After**: Step-specific failure tracking

```
"❌ [2/3] Failed to dispatch Police Agent"
"⚠️ Dispatch completed with issues: 2 successful, 1 failed"
```

### 4. Task Store Integration (Future)

The task orchestrator is designed to persist state:

```python
# Save task plan before execution
await task_store.save(task_to_a2a_task(task))

# After each step
await task_store.save(update_task_with_step_status(task, step))

# Can resume failed tasks
failed_task = await task_store.get(task_id)
await orchestrator.resume_task(failed_task, event_queue)
```

## Switching Between Implementations

### Current Setup (Agent-Driven)

```python
# emergency_operator_agent/app.py
from emergency_operator_agent.executor import OperatorAgentExecutor

request_handler = DefaultRequestHandler(
    agent_executor=OperatorAgentExecutor(task_store=task_store),
    ...
)
```

### New Setup (Task-Orchestrated)

```python
# emergency_operator_agent/app.py
from emergency_operator_agent.task_executor import TaskOrchestratedExecutor

request_handler = DefaultRequestHandler(
    agent_executor=TaskOrchestratedExecutor(task_store=task_store),
    ...
)
```

Just change the import and executor class!

## Production Enhancements

### 1. LLM-Based Task Planning

Replace keyword matching with LLM analysis:

```python
async def create_task_plan(...):
    # Use OpenAI to analyze the emergency
    completion = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": "Analyze emergency and return JSON: {services: [...], location: ...}"
        }, {
            "role": "user",
            "content": user_message
        }]
    )
    
    # Parse response and create task steps
    ...
```

### 2. Parallel Dispatch

Execute multiple steps concurrently:

```python
async def execute_task(task, event_queue):
    # Group steps that can run in parallel
    await asyncio.gather(
        *[dispatch_step(step) for step in task.steps]
    )
```

### 3. Task Store Persistence

```python
# Convert EmergencyTask → a2a.types.Task
def task_to_a2a_task(emergency_task: EmergencyTask) -> Task:
    return Task(
        id=emergency_task.task_id,
        context_id=emergency_task.context_id,
        state=emergency_task.state,
        artifacts=[...],  # Store steps as artifacts
    )

# Save to task store
await task_store.save(task_to_a2a_task(task))
```

### 4. Retry Logic

```python
async def execute_step_with_retry(step, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await dispatch_to_agent(...)
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # exponential backoff
```

### 5. Agent Response Parsing

Extract actual responses from agents:

```python
# In _dispatch_to_agent
if response and hasattr(response.root, 'result'):
    if response.root.result.parts:
        first_part = response.root.result.parts[0]
        if hasattr(first_part.root, 'text'):
            step.response = first_part.root.text
```

## Testing

### Unit Test Example

```python
async def test_task_plan_creation():
    orchestrator = EmergencyTaskOrchestrator()
    task = await orchestrator.create_task_plan(
        task_id="test-123",
        context_id="ctx-456",
        user_message="Fire at 123 Main St, someone is hurt",
        event_queue=MockEventQueue(),
    )
    
    assert len(task.steps) == 2
    assert task.steps[0].service_type == ServiceType.FIRE
    assert task.steps[1].service_type == ServiceType.AMBULANCE
```

### Integration Test

```python
async def test_full_dispatch_workflow():
    orchestrator = EmergencyTaskOrchestrator()
    event_queue = TestEventQueue()
    
    task = await orchestrator.create_task_plan(...)
    await orchestrator.execute_task(task, event_queue)
    
    # Verify SSE messages sent
    messages = event_queue.get_all_messages()
    assert "📋 Dispatch plan created" in messages[0]
    assert "[1/2] Dispatching" in messages[1]
    assert "✅" in messages[2]
```

## Files

- `emergency_operator_agent/task_orchestrator.py` - Core orchestration logic
- `emergency_operator_agent/task_executor.py` - AgentExecutor implementation
- `emergency_operator_agent/executor.py` - Original agent-driven implementation

## Recommendations

1. **Start with task-orchestrated** for emergency dispatch - it's more appropriate for this workflow
2. **Keep agent-driven** as backup for complex/unusual scenarios
3. **Add configuration** to switch implementations dynamically
4. **Enhance task planning** with LLM instead of keywords
5. **Persist task state** to task_store for resumability
6. **Add metrics** to track dispatch success rates per service

## Next Steps

1. Update `app.py` to use `TaskOrchestratedExecutor`
2. Test with various emergency scenarios
3. Add LLM-based task planning
4. Implement task store persistence
5. Add retry logic and error recovery
6. Create monitoring dashboard showing active tasks
