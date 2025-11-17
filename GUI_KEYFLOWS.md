# Key Flow Prototypes – MAAPS Windows 11 GUI

These textual prototypes capture end-to-end interactions for the most critical live-performance flows. Each step references the widgets described in `GUI_PLAN.md` and `GUI_MOCKUPS.md`, noting screen transitions, state changes, and backend messages. Use these scripts to drive clickable prototypes (Figma/Qt) or usability tests.

---

## Flow 1 – Launch, Connect, and Load Session

**Goal**: Musician opens MAAPS, verifies backend agents, and loads a prepared performance session.

1. **Launcher Splash**
   - User double-clicks desktop shortcut.
   - Splash card shows logo + loading spinner + "Checking Agents…".
   - Backend ping: GUI sends `system.health.check`; waits for `status=ready`.
2. **Connection Modal** (if agents offline)
   - Modal overlay with status list and "Start Services" button.
   - Clicking "Start Services" runs bundled script; progress log fills right column.
   - Success auto-dismisses modal; failure surfaces retry/help links.
3. **Dashboard Ready State**
   - Dashboard view auto-loads; top status pill "Connected ●".
   - Recent Messages panel shows last 10 events streamed from bus.
4. **Session Picker Drawer**
   - User clicks "Load Session" quick action.
   - Drawer slides from right listing starred sessions + search + last-opened.
   - Selecting "Festival_Set_A" previews metadata (tempo map, last saved date).
5. **Confirmation Dialog**
   - Dialog warns if current session unsaved; offers Save/Discard/Cancel.
   - On confirmation, GUI publishes `session.load` with session_id.
6. **Progress & Ready**
   - Toast: "Loading stems…" with determinate bar fed by backend progress events.
   - When `session.load.complete` arrives, toast updates to success and Dashboard cards refresh (agent counts, BPM).

---

## Flow 2 – Record & Manipulate Live Loop

**Goal**: Capture a loop, overdub, and remap footswitch in the Live Looping view.

1. **Navigate to Live Looping**
   - User taps "Live Loop" tab; transition animates into loop tracks grid.
   - Track 3 is empty with "Tap ● to record" CTA.
2. **Arm & Record**
   - User clicks the red circular record button on Track 3.
   - GUI publishes `loop.track.arm` and `loop.track.record_start`.
   - Waveform area displays live input waveform plus metronome overlay showing bars.
3. **Stop & Review**
   - After 4 bars, user hits ■ stop in track toolbar.
   - `loop.track.record_stop` message updates UI to show filled waveform; status badge "Synced".
4. **Overdub Action**
   - User presses `Overdub`; button glows cyan and countdown overlay appears.
   - Additional audio captured merges with existing waveform; color-coded overlays display layered passes.
5. **Manipulate**
   - User clicks "Reverse"; timeline animates reversing; publishes `loop.track.reverse`.
   - Pitch slider dragged to +3 semitones; HUD shows numeric delta.
6. **Footswitch Mapping**
   - User opens mapping overlay; selects Slot 2.
   - Prompt says "Press footswitch"; incoming MIDI CC 64 binds to "Track 3 Record".
   - Confirmation toast: "Slot 2 mapped to CC64".
7. **Exit Overlay**
   - Overlay closes; Track 3 toolbar displays footswitch icon indicating mapping active.

---

## Flow 3 – Modify Effects Chain During Performance

**Goal**: Insert a shimmer module, tweak parameters, automate mix, and save preset mid-set.

1. **Open Effects View**
   - Performer clicks "Effects" tab; Chain A is active.
   - Signal Path row shows existing modules.
2. **Add Module**
   - User hits "+" between Tape Echo and Output.
   - Module gallery popover appears with categorized list; search "shimmer".
   - Selecting "Shimmer Verb" publishes `effects.module.add` with slot=3.
   - Tile animates into chain with default settings.
3. **Parameter Adjustment**
   - Inspector auto-focuses on Shimmer Verb; user drags Mix knob to 60% (knob halo reflects value).
   - Freeze toggle set to ON; GUI emits `effects.param.set` events.
4. **Automation Lane**
   - User clicks automation icon next to Mix; mini-lane expands under inspector.
   - Drawing pencil creates rising ramp; nodes snap to beat grid (bars 1–4).
   - Backend receives `automation.update` describing curve; timeline preview pulses.
5. **Preset Save**
   - In preset bar, user clicks "Save"; dialog prompts name, e.g., "Festival_Shimmer_A" and storage scope (Global/Session).
   - Choosing Session scope writes to `%AppData%\MAAPS\presets` and sends `preset.save` event.
6. **Feedback**
   - Toast "Preset saved" with undo shortcut; module tile displays star icon showing customized state.

---

## Flow 4 – Trigger Sync Automation Scene

**Goal**: Launch a pre-built automation macro while monitoring tempo changes.

1. **Open Sync & Automation**
   - User selects tab; BPM panel shows 120, Ableton Link unchecked.
2. **Scene Preparation**
   - Macro list shows Scene A/B/C; Scene B is armed (indicator amber).
   - User reviews timeline preview for Scene B (tempo ramp + filter sweep).
3. **Launch Scene**
   - Click "Launch" on Scene B; button pulses blue.
   - GUI publishes `automation.scene.launch` with id.
4. **Tempo Feedback**
   - Tempo panel transitions from 120→128 BPM over 8 bars; numeric readout animates smoothly; CPU badge stays visible.
   - Automation timeline highlights active curve and scrubbing playhead.
5. **In-flight Controls**
   - User hits "Nudge -" to drop 0.5 BPM; change is queued and displayed as overlay.
   - Option to "Abort" scene via inline button; if pressed, sends `automation.scene.abort` and rolls back to previous state.
6. **Completion**
   - On completion event, timeline glows green; log entry added to Dashboard feed.

---

## Flow 5 – Import Media and Drag to Chain

1. **Open Media Library**
   - Tab reveals filters column + asset grid.
2. **Search & Preview**
   - Type "glass"; grid filters instantly.
   - Select "Glass Chords"; preview pane shows waveform with play controls.
3. **Drag Operation**
   - User drags asset chip to Effects chain's AUX send slot (app supports cross-view drag).
   - Visual ghost follows cursor; destination highlights; releasing triggers `media.asset.assign`.
4. **Confirmation**
   - Chain view opens automatically, showing new sample player module inserted.
   - Toast confirms import; metadata (BPM/Key) autopopulates module settings.

---

### Usage Notes
- Each flow should be mocked interactively in design tool with hotspots, transitions, and microcopy identical to these steps.
- Backend message names provided as references; adjust to actual API naming conventions.
- Incorporate haptic/lighting cues for hardware controllers in future iterations.
