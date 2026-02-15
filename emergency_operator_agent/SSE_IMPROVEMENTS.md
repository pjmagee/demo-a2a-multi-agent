# Emergency Operator SSE Streaming Improvements

## Overview

Enhanced the emergency operator agent to provide real-time Server-Sent Events (SSE) updates showing detailed progress as emergency services are dispatched.

## What Changed

### 1. **Added Message Callback System**

- **File**: `emergency_operator_agent/agent.py`
- New `MessageCallback` type for sending user-visible text messages during execution
- Tools can now send intermediate messages (not just status updates)

### 2. **Enhanced Agent Tools**

- **`send_message` tool** now sends a confirmation message when each service responds:

  ```
  ✓ Dispatched: Fire Brigade Agent has been notified and is responding
  ```

### 3. **Improved Executor**

- **File**: `emergency_operator_agent/executor.py`
- Added `_on_agent_message()` method that enqueues text messages to the event queue
- Passes both `status_callback` and `message_callback` to the agent

### 4. **Better Instructions**

- Updated agent instructions to dispatch services ONE AT A TIME
- This ensures each dispatch generates a separate SSE event

## How It Works Now

### Message Flow

1. **Initial Message** (\ud83d\udea8 emoji):

   ```
   🚨 Emergency call received. Analyzing situation and dispatching appropriate services...
   ```

2. **Per-Service Dispatch** (✓ checkmark):

   ```
   ✓ Dispatched: Fire Brigade Agent has been notified and is responding
   ✓ Dispatched: Ambulance Agent has been notified and is responding
   ✓ Dispatched: Police Agent has been notified and is responding
   ```

3. **Final Summary**:

   ```
   Emergency help is on the way. Fire, medical, and police services have been notified for 170 London Road, SM6 7AN.
   ```

## Expected SSE Stream

With the test message: "hi, can you help? 170 London road SM6 7AN. Fire, Injuries and a citizen arrested criminal."

```
event: task_status_update
data: {"state": "working", "message": "Emergency operator is processing your call..."}

event: message
data: {"text": "🚨 Emergency call received. Analyzing situation and dispatching appropriate services..."}

event: task_status_update  
data: {"state": "working", "message": "Checking available emergency services..."}

event: task_status_update
data: {"state": "working", "message": "Dispatching to Fire Brigade Agent..."}

event: message
data: {"text": "✓ Dispatched: Fire Brigade Agent has been notified and is responding"}

event: task_status_update
data: {"state": "working", "message": "Dispatching to Ambulance Agent..."}

event: message
data: {"text": "✓ Dispatched: Ambulance Agent has been notified and is responding"}

event: task_status_update
data: {"state": "working", "message": "Dispatching to Police Agent..."}

event: message
data: {"text": "✓ Dispatched: Police Agent has been notified and is responding"}

event: message
data: {"text": "Emergency help is on the way. Fire, medical, and police services have been notified for 170 London Road, SM6 7AN."}

event: task_status_update
data: {"state": "completed", "message": "Call handled successfully", "final": true}
```

## Key Improvements

### ✅ Long-Running Task Feel

- Multiple SSE events streamed over time as agent works
- User sees progress instead of waiting for final response

### ✅ Visibility Into Service Dispatch

- Each emergency service dispatch generates a visible message
- User knows exactly which services are being notified

### ✅ Real-Time Feedback

- Status updates show internal progress ("Checking...", "Dispatching...")
- Message events show user-facing confirmations

## Technical Details

### Status Updates vs. Messages

- **Status Updates** (`task_status_update`): Internal progress, shown in UI status indicators
- **Messages** (`message` events): User-facing text, displayed as conversation messages

### Event Queue

Both types of events go through the `EventQueue` which manages SSE streaming:

```python
# Status update - for progress indicators
await event_queue.enqueue_event(
    event=TaskStatusUpdateEvent(...)
)

# Text message - for conversation
await event_queue.enqueue_event(
    event=new_agent_text_message(...)
)
```

## Testing

### Run Emergency Operator

```bash
cd emergency_operator_agent
uv run python -m emergency_operator_agent.app
```

### Send Test Message via A2A Inspector

Navigate to <http://localhost:8080> and send:

```
hi, can you help? 170 London road SM6 7AN. Fire, Injuries and a citizen arrested criminal.
```

Watch the SSE stream for multiple messages showing each service being dispatched.

## Future Enhancements

### Potential Additions

1. **Parse Service Responses**: Extract actual response text from each service
2. **ETA Information**: Show estimated arrival times if services provide them
3. **Progress Percentages**: Track dispatch progress (1/3, 2/3, 3/3)
4. **Failure Handling**: Show specific errors if a service fails to respond
5. **Parallel Dispatch**: Dispatch multiple services simultaneously while still showing individual confirmations

## Files Modified

- `emergency_operator_agent/emergency_operator_agent/agent.py`
- `emergency_operator_agent/emergency_operator_agent/executor.py`

## Additional Fixes

### Service Unavailability Detection

Added proper handling when no emergency services are registered:

**Problem**: If agents fail to register or are offline, the operator would silently fail without informing the user.

**Solution**:

- Enhanced `list_agents` tool to detect empty agent list
- Sends immediate warning message: "⚠️ WARNING: No emergency services are currently available"
- Updated agent instructions to inform callers about service unavailability
- Suggests alternative help when services are down

### Registration Logging Consistency

Fixed inconsistent registration status logging across agents:

**Files Modified**:

- `greetings_agent/greetings_agent/app.py`
- `counter_agent/counter_agent/app.py`

All agents now consistently log:

- ✅ "Successfully registered with A2A Registry"
- ⚠️ "Failed to register with A2A Registry"

This makes it immediately obvious in console logs if an agent failed to register.

For troubleshooting registration issues, see [TROUBLESHOOTING.md](../TROUBLESHOOTING.md).
