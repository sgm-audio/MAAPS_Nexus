# MAAPS Nexus - Multi-Agent Audio Processing System

A cutting-edge multi-agent system for intelligent audio processing using reinforcement learning and hierarchical goal optimization.

## System Overview

MAAPS Nexus implements a sophisticated multi-agent architecture where specialized AI agents collaborate (and sometimes compete) to optimize audio quality:

### Core Components

1. **Ray Cluster** - Distributed computing infrastructure for scalable agent execution
2. **Audio Ontology** - Shared vocabulary for audio concepts (Clarity, Warmth, Mud, etc.)
3. **Critic Agent** - Judges audio quality and provides reward signals
4. **EQ Agent (RL)** - Learns optimal EQ adjustments via reinforcement learning
5. **Dynamics Agent (RL)** - Learns optimal compression/dynamics via reinforcement learning
6. **HGO Coordinator** - Hierarchical Goal Optimization to mediate agent conflicts
7. **VST3 Wrapper** - Ultra-low latency (<10ms) DAW integration via shared memory

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         DAW (Reaper, Ableton, etc.)         │
└───────────────────────────┬─────────────────────────────────┘
                            │ Audio I/O
                    ┌───────▼────────┐
                    │  VST3 Plugin   │ (C++)
                    │  (Shared Mem)  │
                    └───────┬────────┘
                            │ <10ms latency
        ┌───────────────────▼───────────────────┐
        │      Python Audio Engine              │
        │  ┌─────────────────────────────────┐  │
        │  │    HGO Coordinator              │  │
        │  │  (Hierarchical Goal Optimizer)  │  │
        │  └────┬──────────────────────┬─────┘  │
        │       │                      │         │
        │  ┌────▼─────┐          ┌────▼──────┐  │
        │  │ EQ Agent │          │ Dynamics  │  │
        │  │   (RL)   │◄────────►│Agent (RL) │  │
        │  └────┬─────┘          └────┬──────┘  │
        │       │    Cooperation      │         │
        │       │      / Fight        │         │
        │       └──────────┬──────────┘         │
        │                  │                     │
        │            ┌─────▼──────┐             │
        │            │   Critic   │             │
        │            │   Agent    │             │
        │            └─────┬──────┘             │
        │                  │                     │
        │         Reward Signals                │
        │                  │                     │
        │        ┌─────────▼──────────┐         │
        │        │  Audio Ontology    │         │
        │        │  (Concepts & Rules)│         │
        │        └────────────────────┘         │
        └────────────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │  Ray Cluster    │
                │  (Distributed)  │
                └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- C++17 compiler (for VST3 plugin)
- VST3 SDK (for plugin development)
- CMake 3.14+ (for building VST3)

### Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `ray>=2.0.0` - Distributed computing
- `torch>=2.0.0` - Neural networks for RL
- `numpy>=1.24.0` - Numerical computing
- `librosa>=0.10.0` - Audio analysis
- `soundfile>=0.12.0` - Audio I/O
- `scipy>=1.10.0` - Signal processing
- `psutil>=5.9.0` - System monitoring

### VST3 Plugin Build (Optional)

```bash
cd vst3_plugin
mkdir build && cd build
cmake .. -DVST3_SDK_PATH=/path/to/vst3sdk
cmake --build .
cmake --install .
```

## Quick Start

### 1. VST3 Mode (DAW Integration)

Start the Python backend:

```bash
python maaps_nexus_main.py --mode vst3
```

Then load the MAAPS_Nexus VST3 plugin in your DAW.

### 2. Training Mode

Train the agents on your audio:

```bash
python maaps_nexus_main.py \
    --mode train \
    --audio-file my_mix.wav \
    --episodes 50
```

### 3. Inference Mode

Process audio with trained agents:

```bash
python maaps_nexus_main.py \
    --mode inference \
    --audio-file input.wav \
    --output-file output.wav
```

## Audio Ontology

The system uses a comprehensive audio ontology with the following concepts:

### Positive Qualities
- **Clarity** - Clear definition and separation
- **Warmth** - Pleasant fullness in low-mids
- **Brightness** - High-frequency energy and sparkle
- **Punch** - Transient impact and definition
- **Depth** - Perceived spaciousness
- **Airiness** - Open, spacious high frequencies
- **Presence** - Forward, immediate quality
- **Tightness** - Controlled, focused low-end

### Negative Qualities
- **Mud** - Unclear, undefined low-mids
- **Harshness** - Aggressive, unpleasant highs
- **Boominess** - Excessive low-frequency resonance
- **Boxiness** - Narrow, confined midrange
- **Shrillness** - Piercing high frequencies
- **Dullness** - Lack of high-frequency content

## How It Works

### 1. The Critic Agent

The Critic analyzes audio and predicts user satisfaction:

```python
judgment = critic.judge_audio(audio)
# Returns:
# - satisfaction_score: -1.0 to 1.0
# - detected_concepts: ['clarity', 'warmth', 'mud']
# - suggested_corrections: {FrequencyRange: dB_adjustment}
```

### 2. Reinforcement Learning Agents

The EQ and Dynamics agents learn through trial and error:

- **State**: Audio features (spectral, dynamic, temporal)
- **Action**: Parameter adjustments (EQ gains, compression ratios, etc.)
- **Reward**: Critic's satisfaction score
- **Algorithm**: PPO (Proximal Policy Optimization)

### 3. Agent Coordination

The HGO Coordinator prevents destructive interference:

```python
# Set optimization goals
goals = [
    OptimizationGoal(
        name="clarity_and_presence",
        target_concepts=["clarity", "presence"],
        avoid_concepts=["mud", "harshness"],
        priority=GoalPriority.HIGH
    )
]
coordinator.set_goals(goals)
```

The coordinator:
- Detects conflicts between agents
- Resolves conflicts using priority-based strategies
- Orders operations for optimal results
- Provides cooperation bonuses

### 4. The "Fight"

Agents can work against each other:

**Example Conflict:**
- EQ Agent boosts low-mids for warmth
- Dynamics Agent compresses heavily, reducing warmth
- **Resolution**: HGO Coordinator balances both actions based on goals

**Cooperation Example:**
- EQ Agent cuts muddy frequencies
- Dynamics Agent preserves transients
- **Result**: Both agents work synergistically

## VST3 Integration

### Shared Memory Architecture

The VST3 plugin communicates with Python via shared memory:

```
VST3 Plugin (C++)  ←→  Shared Memory  ←→  Python Engine
     │                   (mmap)                  │
     │                                          │
     └──────── <10ms latency ──────────────────┘
```

**Memory Layout:**
```
[Header: 64 bytes]
  - Magic number
  - Write/Read offsets
  - Block size
  - Sample rate
  - Status flags

[Audio Data: Ring Buffer]
  - Float32 samples
  - Interleaved channels
```

### Performance

- **Latency**: <10ms round-trip (target)
- **Throughput**: Real-time processing at 44.1kHz
- **Block Size**: Configurable (default 512 samples)

## Ray Cluster Configuration

### Single Machine

```python
config = RayClusterConfig(
    num_cpus=8,
    num_gpus=1,
    include_dashboard=True
)
cluster = initialize_ray_cluster(config)
```

### Multi-Node Cluster

**Head Node:**
```bash
ray start --head --port=6379 --dashboard-host=0.0.0.0
```

**Worker Nodes:**
```bash
ray start --address='head_node_ip:6379'
```

Then connect:
```python
cluster.connect_to_cluster("ray://head_node_ip:10001")
```

## Training Tips

1. **Start Small**: Train on short audio clips (5-10 seconds)
2. **Use Diverse Audio**: Train on various genres and content
3. **Monitor Cooperation**: Watch the cooperation score - aim for >0.7
4. **Adjust Goals**: Customize optimization goals for your use case
5. **Patience**: RL takes time - 50-100 episodes for good results

## Advanced Usage

### Custom Optimization Goals

```python
from src.agents.hgo_coordinator import OptimizationGoal, GoalPriority

custom_goal = OptimizationGoal(
    name="podcast_voice_optimization",
    description="Optimize for podcast voice clarity",
    target_concepts=["clarity", "presence", "warmth"],
    avoid_concepts=["mud", "harshness", "shrillness"],
    priority=GoalPriority.CRITICAL,
    weight=1.0
)

coordinator.set_goals([custom_goal])
```

### Direct Agent Access

```python
# Get judgment from Critic
judgment = critic_agent.judge_audio(audio, sr=44100)

# Train EQ agent
eq_stats = eq_agent.train_episode(audio, max_steps=10)

# Apply best learned EQ
processed = eq_agent.apply_eq(audio, eq_agent.best_eq_state)
```

### Distributed Training

```python
# Create agent pool with replicas
agent_pool = DistributedAgentPool(cluster_manager)

agent_pool.create_agent_pool(
    agent_class=EQRLAgent,
    agent_type="eq_rl",
    num_replicas=4,  # 4 parallel agents
    num_cpus=2.0,
    num_gpus=0.25
)

# Submit parallel training tasks
results = [
    agent_pool.submit_task("eq_rl", {
        'audio': audio_sample,
        'mode': 'training'
    })
    for audio_sample in training_data
]
```

## Troubleshooting

### VST3 Plugin Not Connecting

1. Check Python backend is running:
   ```bash
   ps aux | grep maaps_nexus_main
   ```

2. Verify shared memory exists:
   ```bash
   ls -la /dev/shm/maaps_nexus_audio
   ```

3. Check socket connection:
   ```bash
   ls -la /tmp/maaps_nexus_vst.sock
   ```

### High Latency

- Reduce `max_steps` in HGO coordinator (set to 1 for VST3)
- Decrease audio block size
- Use inference mode (not training) in VST3
- Check Ray dashboard for resource bottlenecks

### Training Not Converging

- Increase number of episodes
- Adjust learning rate in agent configs
- Use more diverse training audio
- Check Critic agent is providing meaningful rewards

## Performance Metrics

Monitor system performance:

```python
# Ray Dashboard
http://localhost:8265

# VST3 Statistics
backend.blocks_processed  # Total blocks
backend.total_latency     # Cumulative latency
backend.max_latency       # Peak latency

# Agent Statistics
eq_agent.episodes_trained
eq_agent.best_reward
dynamics_agent.cooperation_score
```

## Contributing

This is a research system. Key areas for contribution:

1. **New Agents**: Implement additional processing agents (reverb, stereo width, etc.)
2. **Better RL Algorithms**: Experiment with SAC, TD3, etc.
3. **Ontology Expansion**: Add more audio concepts
4. **VST3 GUI**: Create plugin UI
5. **Windows Support**: Port shared memory to named pipes

## Citation

If you use this system in research:

```bibtex
@software{maaps_nexus_2024,
  title={MAAPS Nexus: Multi-Agent Audio Processing System},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/MAAPS_Nexus}
}
```

## License

[Add your license here]

## Acknowledgments

- Ray Team (distributed computing)
- Steinberg (VST3 SDK)
- librosa contributors
- PyTorch team

---

**Status**: Research prototype - Use at your own risk in production environments.

**Requirements**: High-performance computing for training, real-time requirements for VST3 mode.
