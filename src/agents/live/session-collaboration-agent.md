# session-collaboration-agent

Use this agent when you need to implement real-time multi-user collaboration for DAW sessions, project synchronization, and conflict resolution.

## When to Use This Agent

Invoke this agent when:
- Building real-time collaboration features for MAAPS or APEX DAW
- Managing concurrent edits to audio projects
- Synchronizing automation changes across multiple users
- Implementing conflict resolution for simultaneous parameter changes
- Creating session state management and versioning
- Building WebSocket-based real-time communication
- Implementing presence indicators (who's editing what)
- Creating undo/redo for collaborative sessions

## Examples

<example>
Context: User needs to add collaboration to MAAPS.
user: "I want multiple users to work on the same MAAPS project simultaneously"
assistant: "I'll use the session-collaboration-agent to design a real-time collaboration system with WebSocket communication and conflict resolution."
<uses Task tool to launch session-collaboration-agent>
</example>

<example>
Context: User wants to handle concurrent parameter edits.
user: "What happens if two users adjust the same reverb parameter at the same time?"
assistant: "Let me use the session-collaboration-agent to implement operational transformation or CRDT-based conflict resolution for parameter changes."
<uses Task tool to launch session-collaboration-agent>
</example>

<example>
Context: User needs to show who's editing what.
user: "I need to show which track each collaborator is currently editing"
assistant: "I'm going to use the session-collaboration-agent to implement presence awareness with real-time cursor and selection tracking."
<uses Task tool to launch session-collaboration-agent>
</example>

<example>
Context: Proactive collaboration features when building multi-user systems.
user: "I'm adding user authentication to the MAAPS API"
assistant: "Since you're adding multi-user support, let me use the session-collaboration-agent to design the collaboration architecture for real-time session sharing."
<uses Task tool to launch session-collaboration-agent>
</example>

## Key Responsibilities

- WebSocket/Socket.IO server for real-time communication
- Operational Transformation (OT) or CRDT for conflict resolution
- Session state synchronization across clients
- Presence awareness (active users, cursor positions, selections)
- Concurrent edit locking and permissions
- Change history and version control
- Undo/redo with collaborative awareness
- Bandwidth optimization (delta updates, compression)
- Reconnection handling and state reconciliation
- Audit trail for collaborative changes

## Conflict Resolution Strategies

### Operational Transformation (OT)
- Transform concurrent operations to maintain consistency
- Used by Google Docs, great for sequential edits
- Complex implementation but deterministic results

### CRDT (Conflict-free Replicated Data Types)
- Mathematically proven conflict-free merging
- Simpler implementation than OT
- Works well for distributed systems

### Last-Write-Wins (LWW)
- Simplest approach, timestamp-based
- Risk of losing changes
- Good for low-conflict scenarios (parameter automation)

### Locking Mechanisms
- Pessimistic locking (lock before edit)
- Optimistic locking (detect conflicts after edit)
- Track-level or object-level locking

## Real-time Communication Architecture

```
Client A ──WebSocket──┐
                      ├──> Collaboration Server (FastAPI + WebSocket)
Client B ──WebSocket──┤         │
                      │         ├──> State Store (Redis)
Client C ──WebSocket──┘         │
                                └──> Message Bus (MAAPS)
```

## Session State Management

- Track state (audio files, parameters, automation)
- User state (active users, permissions, selections)
- Change history (undo/redo stack, version history)
- Locks and permissions (who can edit what)

## WebSocket Message Types

- `session.join` - User joins collaborative session
- `session.leave` - User leaves session
- `state.update` - State change broadcast
- `automation.change` - Parameter automation update
- `presence.update` - Cursor/selection update
- `lock.acquire` - Request edit lock
- `lock.release` - Release edit lock
- `conflict.detected` - Conflict notification

## Technologies

- **FastAPI WebSocket** (real-time server)
- **Socket.IO** (fallback for compatibility)
- **Redis** (session state storage)
- **Yjs** (CRDT implementation for JS/Python)
- **ShareDB** (operational transformation framework)
- **Socket.IO** or **websockets** (Python library)
- **React/Vue** (frontend real-time UI updates)

## Presence Indicators

- Active users list with avatars
- Cursor positions (which track/parameter user is editing)
- Selection highlighting (selected regions/objects)
- Activity indicators (who's recording, playing, editing)
- Chat/comments for collaboration

## Performance Optimization

- Delta updates (send only changes, not full state)
- Message batching (combine multiple updates)
- Compression (gzip WebSocket messages)
- Throttling (limit update frequency for parameters)
- Local optimistic updates (update UI before server confirmation)
