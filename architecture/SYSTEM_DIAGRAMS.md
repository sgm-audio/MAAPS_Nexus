# System Architecture Diagrams

This document contains visual representations of the multi-agent system architecture using Mermaid diagrams.

## System Overview Diagram

```mermaid
graph TB
    subgraph "External Systems"
        DAW[DAW Software<br/>Reaper/Ableton]
        AudioInterface[Audio Interface]
    end

    subgraph "Agent System"
        MessageBus[Message Bus<br/>Event Hub]

        subgraph "Core Agents"
            DAWControl[DAW Control<br/>Interface Agent]
            VSTBridge[VST Bridge<br/>Manager Agent]
            AudioAnalysis[Audio Analysis<br/>Agent]
            ParamOptimization[Parameter<br/>Optimization Agent]
        end

        subgraph "System Agents"
            Orchestrator[System<br/>Orchestrator Agent]
            LoggingMonitor[Logging<br/>Monitor Agent]
        end
    end

    subgraph "Storage"
        DB[(PostgreSQL<br/>Database)]
        MetricsDB[(Time-Series<br/>Database)]
    end

    DAW <--> DAWControl
    AudioInterface --> DAWControl
    DAWControl <--> MessageBus
    VSTBridge <--> MessageBus
    AudioAnalysis <--> MessageBus
    ParamOptimization <--> MessageBus
    Orchestrator <--> MessageBus
    LoggingMonitor <--> MessageBus

    LoggingMonitor --> DB
    LoggingMonitor --> MetricsDB
```

## Data Flow Diagram

```mermaid
flowchart LR
    Input[Audio Input<br/>from DAW] --> DAWControl[DAW Control<br/>Agent]

    DAWControl -->|audio.input.received<br/>AudioBuffer| AudioAnalysis[Audio Analysis<br/>Agent]

    AudioAnalysis -->|audio.features.extracted<br/>AudioFeatures| ParamOptimization[Parameter<br/>Optimization Agent]

    ParamOptimization -->|optimization.suggestion.generated<br/>OptimizationSuggestion| VSTBridge[VST Bridge<br/>Agent]

    VSTBridge -->|vst.parameter.changed<br/>VSTPluginState| DAWControl

    DAWControl --> Output[Audio Output<br/>to DAW]

    DAWControl -.->|system events| Orchestrator[System<br/>Orchestrator]
    AudioAnalysis -.->|system events| Orchestrator
    ParamOptimization -.->|system events| Orchestrator
    VSTBridge -.->|system events| Orchestrator

    Orchestrator -.->|log events| LoggingMonitor[Logging<br/>Monitor]

    LoggingMonitor --> DB[(Database)]

    style Input fill:#e1f5ff
    style Output fill:#e1f5ff
    style DB fill:#ffe1e1
```

## Message Bus Architecture

```mermaid
graph TD
    subgraph "Publishers"
        P1[Agent 1]
        P2[Agent 2]
        P3[Agent 3]
    end

    subgraph "Message Bus"
        Router[Topic Router]

        subgraph "Priority Queues"
            HighQ[High Priority<br/>Queue]
            MediumQ[Medium Priority<br/>Queue]
            LowQ[Low Priority<br/>Queue]
        end

        Dispatcher[Message<br/>Dispatcher]
        DLQ[Dead Letter<br/>Queue]
    end

    subgraph "Subscribers"
        S1[Agent A]
        S2[Agent B]
        S3[Agent C]
    end

    P1 -->|Publish| Router
    P2 -->|Publish| Router
    P3 -->|Publish| Router

    Router -->|Priority: HIGH| HighQ
    Router -->|Priority: MEDIUM| MediumQ
    Router -->|Priority: LOW| LowQ

    HighQ --> Dispatcher
    MediumQ --> Dispatcher
    LowQ --> Dispatcher

    Dispatcher -->|Deliver| S1
    Dispatcher -->|Deliver| S2
    Dispatcher -->|Deliver| S3

    Dispatcher -.->|Failed| DLQ

    style HighQ fill:#ffcccc
    style MediumQ fill:#ffffcc
    style LowQ fill:#ccffcc
    style DLQ fill:#ffccff
```

## Agent Communication Matrix

```mermaid
graph LR
    subgraph "Audio Processing Flow"
        DAW[DAW Control] -->|audio.input.received| AA[Audio Analysis]
        AA -->|audio.features.extracted| PO[Parameter Optimization]
        PO -->|optimization.suggestion.generated| VST[VST Bridge]
        VST -->|vst.parameter.changed| DAW
    end

    subgraph "System Coordination"
        DAW -.->|system.heartbeat| SO[System Orchestrator]
        AA -.->|system.heartbeat| SO
        PO -.->|system.heartbeat| SO
        VST -.->|system.heartbeat| SO
        SO -.->|system.*| DAW
        SO -.->|system.*| AA
        SO -.->|system.*| PO
        SO -.->|system.*| VST
    end

    subgraph "Logging Flow"
        DAW -.->|log.*| LM[Logging Monitor]
        AA -.->|log.*| LM
        PO -.->|log.*| LM
        VST -.->|log.*| LM
        SO -.->|log.*| LM
    end

    style DAW fill:#e1f5ff
    style AA fill:#e1ffe1
    style PO fill:#ffe1ff
    style VST fill:#fff5e1
    style SO fill:#ffe1e1
    style LM fill:#f0f0f0
```

## Agent Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Starting: start()
    Starting --> Running: setup() success
    Starting --> Error: setup() failure

    Running --> Stopping: stop()
    Running --> Error: exception

    Stopping --> Stopped: teardown() success
    Stopping --> Error: teardown() failure

    Error --> Stopping: stop()

    Stopped --> [*]
    Error --> [*]

    note right of Running
        Agent is operational
        Processing messages
        Sending heartbeats
    end note

    note right of Error
        Agent encountered error
        Logged to system
        Requires intervention
    end note
```

## Request-Response Flow

```mermaid
sequenceDiagram
    participant Requester as Requester Agent
    participant Bus as Message Bus
    participant Responder as Responder Agent

    Requester->>Bus: Publish Request<br/>(correlation_id: 123)
    Bus->>Responder: Deliver Request
    Note over Requester: Wait for response<br/>(timeout: 5s)

    Responder->>Responder: Process Request
    Responder->>Bus: Publish Response<br/>(correlation_id: 123)
    Bus->>Requester: Deliver Response

    Note over Requester: Response received<br/>Continue processing

    alt Timeout Scenario
        Note over Requester: No response<br/>after 5 seconds
        Requester->>Requester: Handle timeout<br/>Return None
    end
```

## Audio Processing Pipeline

```mermaid
flowchart TB
    subgraph "Step 1: Audio Capture"
        A1[DAW sends audio buffer]
        A2[DAW Control Agent receives]
        A3[Convert to AudioBuffer format]
        A4[Publish: audio.input.received]

        A1 --> A2 --> A3 --> A4
    end

    subgraph "Step 2: Feature Extraction"
        B1[Audio Analysis receives buffer]
        B2[FFT & Spectral Analysis]
        B3[Temporal Feature Extraction]
        B4[Dynamic Range Analysis]
        B5[Create AudioFeatures object]
        B6[Publish: audio.features.extracted]

        B1 --> B2 --> B3 --> B4 --> B5 --> B6
    end

    subgraph "Step 3: Parameter Optimization"
        C1[Param Optimization receives features]
        C2[Load ML model]
        C3[Generate parameter suggestions]
        C4[Calculate confidence scores]
        C5[Create OptimizationSuggestion]
        C6[Publish: optimization.suggestion.generated]

        C1 --> C2 --> C3 --> C4 --> C5 --> C6
    end

    subgraph "Step 4: VST Parameter Application"
        D1[VST Bridge receives suggestion]
        D2[Validate parameter ranges]
        D3[Apply to VST plugin]
        D4[Capture new VSTPluginState]
        D5[Publish: vst.parameter.changed]

        D1 --> D2 --> D3 --> D4 --> D5
    end

    subgraph "Step 5: DAW Update"
        E1[DAW Control receives state]
        E2[Update DAW project]
        E3[Confirm changes]

        E1 --> E2 --> E3
    end

    A4 --> B1
    B6 --> C1
    C6 --> D1
    D5 --> E1

    style A4 fill:#e1f5ff
    style B6 fill:#e1ffe1
    style C6 fill:#ffe1ff
    style D5 fill:#fff5e1
    style E3 fill:#ffe1e1
```

## Database Schema Diagram

```mermaid
erDiagram
    AUDIO_FEATURES {
        uuid feature_id PK
        uuid buffer_id
        uuid track_id FK
        timestamp timestamp
        jsonb spectral_data
        jsonb temporal_data
        jsonb harmonic_data
        jsonb dynamic_data
        timestamp created_at
    }

    OPTIMIZATION_HISTORY {
        uuid suggestion_id PK
        uuid feature_id FK
        varchar plugin_id
        jsonb parameters
        boolean applied
        boolean user_accepted
        timestamp created_at
    }

    USER_PREFERENCES {
        uuid preference_id PK
        uuid user_id
        uuid feature_id FK
        varchar plugin_id
        varchar parameter_name
        float parameter_value
        timestamp created_at
    }

    SYSTEM_LOGS {
        uuid log_id PK
        varchar agent_id
        varchar level
        text message
        jsonb context
        jsonb metrics
        timestamp created_at
    }

    TRACKS {
        uuid track_id PK
        uuid project_id FK
        varchar track_name
        varchar track_type
        timestamp created_at
    }

    PROJECTS {
        uuid project_id PK
        varchar project_name
        int sample_rate
        float tempo
        timestamp created_at
    }

    AUDIO_FEATURES ||--o{ OPTIMIZATION_HISTORY : "generates"
    AUDIO_FEATURES ||--o{ USER_PREFERENCES : "influences"
    TRACKS ||--o{ AUDIO_FEATURES : "contains"
    PROJECTS ||--o{ TRACKS : "has"
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        Dev[Single Process<br/>All Agents]
        DevBus[Local Message Bus]
        DevDB[(SQLite)]

        Dev --> DevBus
        Dev --> DevDB
    end

    subgraph "Production Environment"
        LB[Load Balancer]

        subgraph "Agent Cluster"
            A1[DAW Control<br/>Container]
            A2[Audio Analysis<br/>Container x3]
            A3[VST Bridge<br/>Container x2]
            A4[Param Optimization<br/>Container x2]
            A5[System Orchestrator<br/>Container]
            A6[Logging Monitor<br/>Container]
        end

        ProdBus[Distributed<br/>Message Bus<br/>Redis/RabbitMQ]

        subgraph "Data Layer"
            ProdDB[(PostgreSQL<br/>Primary)]
            ProdDBReplica[(PostgreSQL<br/>Replica)]
            MetricsDB[(InfluxDB)]
            Cache[(Redis Cache)]
        end

        subgraph "Monitoring"
            Prometheus[Prometheus]
            Grafana[Grafana<br/>Dashboard]
        end

        LB --> A1
        LB --> A2
        LB --> A3
        LB --> A4

        A1 <--> ProdBus
        A2 <--> ProdBus
        A3 <--> ProdBus
        A4 <--> ProdBus
        A5 <--> ProdBus
        A6 <--> ProdBus

        A1 --> Cache
        A2 --> Cache
        A3 --> Cache
        A4 --> Cache

        A6 --> ProdDB
        A6 --> MetricsDB
        ProdDB --> ProdDBReplica

        A6 --> Prometheus
        Prometheus --> Grafana
    end

    style Dev fill:#e1f5ff
    style ProdBus fill:#ffe1e1
```

## Error Handling Flow

```mermaid
flowchart TD
    Start[Agent Processing] --> Error{Error<br/>Occurs?}

    Error -->|No| Success[Continue<br/>Processing]
    Error -->|Yes| Catch[Catch Exception]

    Catch --> Log[Log Error Locally]
    Log --> Publish[Publish to<br/>system.error.critical]

    Publish --> DLQ{Retry<br/>Possible?}

    DLQ -->|Yes| Retry[Add to Retry Queue]
    DLQ -->|No| DeadLetter[Send to<br/>Dead Letter Queue]

    Retry --> Backoff[Exponential Backoff]
    Backoff --> Attempt{Retry<br/>Count < 3?}

    Attempt -->|Yes| Start
    Attempt -->|No| DeadLetter

    DeadLetter --> Alert[Alert System<br/>Orchestrator]
    Alert --> Manual[Manual<br/>Intervention Required]

    Success --> End[Complete]
    Manual --> End

    style Error fill:#ffe1e1
    style DeadLetter fill:#ffcccc
    style Alert fill:#ff9999
    style Success fill:#ccffcc
```

## Monitoring Dashboard Layout

```mermaid
graph TB
    subgraph "System Health Dashboard"
        subgraph "Row 1: Agent Status"
            A1[DAW Control<br/>Status: Running<br/>CPU: 15%]
            A2[Audio Analysis<br/>Status: Running<br/>CPU: 45%]
            A3[VST Bridge<br/>Status: Running<br/>CPU: 25%]
        end

        subgraph "Row 2: Message Flow"
            M1[Messages/sec<br/>▲ 1,247]
            M2[Avg Latency<br/>7.2ms]
            M3[Queue Depth<br/>High: 12<br/>Med: 45<br/>Low: 102]
        end

        subgraph "Row 3: System Metrics"
            S1[Error Rate<br/>0.02%]
            S2[Memory Usage<br/>2.3 GB / 8 GB]
            S3[Active Agents<br/>7 / 7]
        end

        subgraph "Row 4: Performance Graphs"
            G1[Message Throughput<br/>Time Series]
            G2[Latency Distribution<br/>Histogram]
            G3[Agent CPU Usage<br/>Stacked Area]
        end
    end

    style A1 fill:#ccffcc
    style A2 fill:#ccffcc
    style A3 fill:#ccffcc
    style S1 fill:#ccffcc
```
