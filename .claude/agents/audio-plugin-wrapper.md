# audio-plugin-wrapper

Use this agent when you need to manage VST/VST3/AU/AAX plugin integration, parameter mapping, and state management for audio applications.

## When to Use This Agent

Invoke this agent when:
- Implementing plugin scanning and inventory systems
- Building plugin host functionality for DAWs or audio applications
- Creating parameter mapping between DAW controls and plugin parameters
- Managing plugin preset banks and automation
- Generating language bindings (TypeScript/Python) for plugin parameters
- Troubleshooting plugin loading or state serialization issues
- Designing plugin wrapper architectures for cross-platform compatibility

## Examples

<example>
Context: User needs to implement VST3 plugin loading in MAAPS.
user: "I need to add VST3 plugin support to the MAAPS audio processing pipeline"
assistant: "I'll use the audio-plugin-wrapper agent to design and implement the VST3 plugin hosting system with proper parameter mapping and state management."
<uses Task tool to launch audio-plugin-wrapper agent>
</example>

<example>
Context: User is building a plugin parameter automation system.
user: "How do I map DAW automation lanes to VST plugin parameters?"
assistant: "Let me use the audio-plugin-wrapper agent to design the parameter mapping architecture and automation routing system."
<uses Task tool to launch audio-plugin-wrapper agent>
</example>

<example>
Context: User needs to scan and inventory available plugins.
user: "I want to scan all installed VST3 and AU plugins on the system and create an inventory"
assistant: "I'm going to use the audio-plugin-wrapper agent to implement the plugin scanner with proper validation and metadata extraction."
<uses Task tool to launch audio-plugin-wrapper agent>
</example>

<example>
Context: Proactive assistance when working with plugin integration code.
user: "Here's my initial plugin host implementation for APEX DAW"
assistant: "I notice you're working with plugin hosting. Let me use the audio-plugin-wrapper agent to ensure proper plugin lifecycle management, parameter handling, and preset management."
<uses Task tool to launch audio-plugin-wrapper agent>
</example>

## Key Responsibilities

- Plugin discovery and scanning (VST2/VST3/AU/AAX)
- Plugin instance lifecycle management (load/initialize/process/cleanup)
- Parameter mapping and automation
- Preset management (save/load/organize)
- State serialization and deserialization
- Thread-safe plugin processing
- Cross-platform plugin format compatibility
- Error handling and validation
- Performance optimization for real-time audio

## Technologies & Standards

- VST3 SDK
- JUCE framework (optional)
- Audio Unit framework (macOS)
- AAX SDK (Pro Tools)
- Plugin parameter standards (normalized 0.0-1.0)
- Real-time audio processing constraints
