# Navigation Wireframes & Content Mapping

These wireframes use the recommended PySide6 stack (`GUI_PLAN.md:26-82`) and map each navigation surface (Home, Discover, Spaces, Finance, Account, Upgrade) to existing MAAPS capabilities documented across the repository.

## Shared Layout Structure

```
┌────────────────────────────────────────────┐
│ Top Bar: Logo | Nav Tabs | Upgrade CTA     │
├────────────────────────────────────────────┤
│ Left Rail (Context Pane)                   │
│  - System Status (bus + agents)            │
│  - Notifications / workflow alerts         │
│  - Quick actions (start/stop system)       │
├────────────────────────────────────────────┤
│ Primary Canvas (page-specific)             │
└────────────────────────────────────────────┘
```

*Top bar + left rail reuse the existing workflow/health metadata from `README.md:5-49` and `IMPLEMENTATION_SUMMARY.md:94-179`.*

---

## Home

```
┌────────────────────────────────────────────┐
│ Hero Banner: "Multi-Agent Studio Status"   │
│  - Start/Stop buttons                      │
│  - Current workflow queue count            │
├────────────────────────────────────────────┤
│ Two-column grid                            │
│  L: Active Workflows Timeline (cards)      │
│     • Step list w/ agent badges            │
│     • Progress + retry badges              │
│  R: Resource & Health Stack                │
│     • Agent health tiles                   │
│     • Message bus throughput sparkline     │
│     • Cache usage + alerts                 │
├────────────────────────────────────────────┤
│ Bottom rail: Quick Actions (Enhance audio, │
│ Generate content, New workflow template)   │
└────────────────────────────────────────────┘
```

**Content Sources**
- Workflow metrics from orchestration engine (`IMPLEMENTATION_SUMMARY.md:119-179`).
- Health/resource view from Performance Agent (`README.md:7-40`).

---

## Discover

```
┌────────────────────────────────────────────┐
│ Intro strip: "What makes MAAPS unique"     │
│  - Carousel cards (Emergent Intel, Temporal │
│    Context, etc.)                           │
├────────────────────────────────────────────┤
│ 3x2 Tile Grid                               │
│  - Each tile = concept highlight            │
│     Title + short blurb + CTA to learn more │
│     Badge for related agent(s)              │
│  - Example tiles:                           │
│     Emergent Musical Intelligence           │
│     Temporal Context Awareness              │
│     Adaptive Performance Persona            │
├────────────────────────────────────────────┤
│ Bottom section: "Workflow Recipes"         │
│  - Scrollable list referencing real         │
│    cross-agent flows                        │
└────────────────────────────────────────────┘
```

**Content Sources**
- Concept blurbs from `MAAPS_UNIQUE_CONCEPTS_EXPANDED.md:9-144`.
- Workflow recipes from `IMPLEMENTATION_SUMMARY.md:94-118`.

---

## Spaces

```
┌────────────────────────────────────────────┐
│ Tabs: Projects | Collaborations | Live      │
├────────────────────────────────────────────┤
│ Project Kanban                             │
│  - Columns: Ideas, In Progress, Review,     │
│    Delivered                                │
│  - Cards show client, timeframe, linked     │
│    workflows, metadata tags                 │
├────────────────────────────────────────────┤
│ Collaboration Drawer                        │
│  - Real-time chat / notes                   │
│  - Agent suggestions feed                   │
│  - Context memory toggle                    │
└────────────────────────────────────────────┘
```

**Content Sources**
- Persona collaboration needs (`MAAPS_USER_PERSONAS.md:31-195`).
- Metadata agent features (`IMPLEMENTATION_SUMMARY.md:32-44`).

---

## Finance

```
┌────────────────────────────────────────────┐
│ KPI Header Row                             │
│  - Billable hours saved                    │
│  - Projects delivered                      │
│  - Estimated revenue impact                │
├────────────────────────────────────────────┤
│ Two stacked sections                        │
│ 1) Workflow ROI chart                      │
│    • Plot hours vs. automation level       │
│ 2) Client Accounts table                   │
│    • Project name, fee, status, agent mix  │
├────────────────────────────────────────────┤
│ Persona Tip cards                           │
│  - E.g., "Commercial Producer" revenue     │
│    guidance                                 │
└────────────────────────────────────────────┘
```

**Content Sources**
- Economic framing from `MAAPS_USER_PERSONAS.md:94-139`.
- Automation metrics from workflow engine (reuse data pipeline from Home page).

---

## Account

```
┌────────────────────────────────────────────┐
│ Profile + Studio Setup summary             │
│  - Hardware profile, DAW selection         │
│  - Active agent pack versions              │
├────────────────────────────────────────────┤
│ Preferences Tabs                           │
│  • Emergent Memory settings                │
│  • Workflow defaults                       │
│  • Notification routing                    │
├────────────────────────────────────────────┤
│ Audit Log                                  │
│  - Recent logins, API keys, workspace      │
└────────────────────────────────────────────┘
```

**Content Sources**
- System configuration from `README.md:63-119`.
- Emergent/temporal settings from `MAAPS_UNIQUE_CONCEPTS_EXPANDED.md:9-144`.

---

## Upgrade

```
┌────────────────────────────────────────────┐
│ Tier comparison cards (Free / Studio / Pro)│
│  - Feature checklist per tier              │
│  - CTA buttons                             │
├────────────────────────────────────────────┤
│ Value proof strip                          │
│  - Metrics showing time saved, quality     │
│    gains (pull from Finance KPIs)          │
├────────────────────────────────────────────┤
│ Feature Detail accordion                   │
│  - Emergent intelligence add-ons           │
│  - Temporal context horizon                │
│  - Premium workflow templates              │
└────────────────────────────────────────────┘
```

**Content Sources**
- Differentiators from `MAAPS_UNIQUE_CONCEPTS_EXPANDED.md:56-90`.
- Persona willingness to pay from `MAAPS_USER_PERSONAS.md:166-185`.

---

## Implementation Notes
- Build top-level layout as `QMainWindow` with `QDockWidget` for the left rail and `QStackedWidget` for main pages (per `GUI_PLAN.md:88-101`).
- Each navigation section should expose a data-provider interface that pulls from the coordinator/workflow APIs documented in `README.md:63-119`.
- Use consistent card widgets and typography defined in the UI components library section of the GUI plan for faster implementation.
