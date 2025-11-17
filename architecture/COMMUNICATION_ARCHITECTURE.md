# Communication Architecture

## Overview
The multi-agent system uses an event-driven architecture with a central message bus for asynchronous communication between agents. This design ensures loose coupling, scalability, and maintainability.

## Architecture Pattern: Event-Driven Message Bus

### Core Components

#### 1. Message Bus
- **Purpose**: Central hub for all inter-agent communication
- **Pattern**: Publish-Subscribe with Topic-based routing
- **Implementation**: Thread-safe queue-based message dispatcher

#### 2. Message Types
All messages follow a standardized structure:
```python
{
    "message_id": "uuid",
    "timestamp": "ISO-8601",
    "topic": "string",
    "sender": "agent_id",
    "priority": "high|medium|low",
    "payload": {},
    "correlation_id": "uuid"  # For request-response tracking
}
```

### Communication Patterns

#### 1. Publish-Subscribe
- Agents subscribe to topics of interest
- Publishers broadcast events without knowing subscribers
- Many-to-many communication

#### 2. Request-Response
- Synchronous-style communication using correlation IDs
- Timeout mechanism for handling non-responsive agents
- Used for critical operations requiring acknowledgment

#### 3. Event Streaming
- Real-time audio data streaming
- High-frequency, low-latency communication
- Separate channel from control messages

## Topic Hierarchy

### Audio Processing Topics
- `audio.input.received` - Raw audio data available
- `audio.analysis.started` - Analysis process initiated
- `audio.analysis.complete` - Analysis results ready
- `audio.features.extracted` - Feature extraction complete

### VST Plugin Topics
- `vst.plugin.loaded` - VST plugin initialized
- `vst.parameter.changed` - Plugin parameter modified
- `vst.parameter.optimized` - Optimization suggestion available
- `vst.state.saved` - Plugin state persisted
- `vst.error.occurred` - VST-related error

### DAW Control Topics
- `daw.transport.play` - Playback started
- `daw.transport.stop` - Playback stopped
- `daw.transport.record` - Recording started
- `daw.project.loaded` - DAW project loaded
- `daw.track.created` - New track created

### Optimization Topics
- `optimization.suggestion.generated` - New parameter suggestion
- `optimization.preference.learned` - User preference recorded
- `optimization.model.updated` - ML model updated

### System Topics
- `system.agent.started` - Agent initialized
- `system.agent.stopped` - Agent shutdown
- `system.error.critical` - Critical error occurred
- `system.heartbeat` - Agent health check
- `system.metrics.collected` - Performance metrics available

### Logging Topics
- `log.event.info` - Informational log
- `log.event.warning` - Warning log
- `log.event.error` - Error log
- `log.metrics.performance` - Performance metric
- `log.audit.action` - Audit trail entry

## Agent Communication Matrix

| From Agent | To Agent(s) | Topic | Pattern |
|------------|-------------|-------|---------|
| DAW Control | Audio Analysis | `audio.input.received` | Pub-Sub |
| Audio Analysis | Parameter Optimization | `audio.features.extracted` | Pub-Sub |
| Parameter Optimization | VST Bridge | `vst.parameter.optimized` | Request-Response |
| VST Bridge | DAW Control | `vst.parameter.changed` | Pub-Sub |
| All Agents | System Orchestrator | `system.heartbeat` | Pub-Sub |
| All Agents | Logging Monitor | `log.*` | Pub-Sub |
| System Orchestrator | All Agents | `system.*` | Pub-Sub |

## Message Flow Examples

### Example 1: Audio Analysis Flow
```
1. DAW Control → audio.input.received
   └─> Audio Analysis Agent subscribes

2. Audio Analysis → audio.analysis.complete
   └─> Parameter Optimization subscribes
   └─> Logging Monitor subscribes

3. Parameter Optimization → optimization.suggestion.generated
   └─> VST Bridge subscribes
```

### Example 2: Error Handling Flow
```
1. VST Bridge → vst.error.occurred
   └─> System Orchestrator subscribes
   └─> Logging Monitor subscribes

2. System Orchestrator → system.error.critical
   └─> All agents subscribe for shutdown coordination
```

## Quality of Service (QoS)

### Priority Levels
- **High**: Critical errors, transport control, parameter changes
- **Medium**: Analysis results, optimization suggestions
- **Low**: Metrics, heartbeats, informational logs

### Message Guarantees
- **At-least-once delivery**: For critical messages (errors, state changes)
- **Best-effort delivery**: For high-frequency data (metrics, heartbeats)

### Timeout Configuration
- Request-response: 5 seconds default
- Critical operations: 30 seconds
- Health checks: 2 seconds

## Scalability Considerations

### Threading Model
- Message bus runs in dedicated thread
- Each agent processes messages in its own thread pool
- Non-blocking message dispatch

### Backpressure Handling
- Queue size limits per topic
- Drop low-priority messages when queue full
- Alert system when backpressure detected

### Performance Targets
- Message dispatch latency: < 1ms
- End-to-end latency (agent-to-agent): < 10ms
- Throughput: 10,000+ messages/second

## Security & Validation

### Message Validation
- Schema validation for all message payloads
- Sender authentication via agent registry
- Topic permission matrix

### Error Handling
- Dead letter queue for failed messages
- Retry mechanism with exponential backoff
- Circuit breaker pattern for failing agents

## Monitoring & Observability

### Metrics Collected
- Message throughput per topic
- Average message latency
- Queue depths
- Failed message count
- Agent subscription counts

### Health Checks
- Heartbeat monitoring (every 1 second)
- Message processing lag detection
- Queue overflow detection
