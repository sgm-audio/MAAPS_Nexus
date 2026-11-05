# Finance & Upgrade KPI Definitions

Metrics are derived from existing telemetry already captured by MAAPS components (workflow engine, message bus, performance agent) and surfaced via the GUI Finance + Upgrade pages. Each KPI lists data sources, transformation logic, and display recommendations.

---

## Finance Page KPIs

### 1. Billable Hours Saved
- **Purpose:** Demonstrate efficiency gains the system delivers versus manual work.
- **Data Sources:**
  - Workflow engine step metadata (`IMPLEMENTATION_SUMMARY.md:119-179`) provides `estimated_manual_hours` and `actual_execution_seconds` per workflow.
  - User billing rate pulled from persona/account profile (Account page settings).
- **Calculation:**
  ```
  hours_saved = sum(estimated_manual_hours) - sum(actual_execution_seconds / 3600)
  dollar_savings = hours_saved * user_hourly_rate
  ```
- **UI Placement:** Finance header KPI card + Upgrade page proof strip.

### 2. Projects Delivered
- **Purpose:** Track throughput for reporting and future upgrade justification.
- **Data Sources:**
  - Workflow completion events (status `success`) from workflow engine.
  - Metadata agent project tags to group workflows by client/project.
- **Calculation:** Count of unique project IDs with at least one completed workflow in selected timeframe.
- **UI Placement:** Finance header KPI card and Projects column chart.

### 3. Automation Rate
- **Purpose:** Quantify percentage of steps handled autonomously vs. manually triggered interventions.
- **Data Sources:**
  - Workflow step logs expose `execution_mode` (auto/manual) and retry data.
  - Message bus dead-letter entries note manual overrides.
- **Calculation:** `automation_rate = automated_steps / total_steps` (weighted by duration if needed).
- **UI Placement:** Finance page ROI section, used to benchmark against RLI automation stats.

### 4. Revenue Impact Tracker
- **Purpose:** Tie system output to income targets from personas (`MAAPS_USER_PERSONAS.md:100-139`).
- **Data Sources:**
  - Projects table (client fee metadata) maintained by metadata agent.
  - Billable hours saved metric.
- **Calculation:** `estimated_revenue = sum(project_fee) + (hours_saved * hourly_rate)` to show both realized and potential gains.
- **UI Placement:** Finance KPI row + breakdown table.

### 5. Revision Turnaround Time
- **Purpose:** Reflect persona pain point of revision loops, highlighting improvement.
- **Data Sources:**
  - Metadata agent revision logs (timestamps for client feedback vs. workflow completion).
- **Calculation:** median duration between revision request and delivered workflow.
- **UI Placement:** Finance analytics section and anecdotal callouts in Upgrade page.

---

## Upgrade Page Metrics

### 1. Tiered Feature Utilization
- **Purpose:** Show what features users rely on, nudging them toward higher tiers when usage brushes limits.
- **Data Sources:**
  - Coordinator tracks feature flags per account (Emergent Intelligence, Temporal Context, etc.).
  - Agent request logs capture counts per premium feature.
- **Calculation:** For each tier-limited feature, compute utilization percentage vs. quota.
- **UI Placement:** Tier comparison cards with progress bars.

### 2. Quality Assurance Score
- **Purpose:** Highlight improvements from advanced packs (e.g., emergent intelligence) compared to baseline.
- **Data Sources:**
  - Metadata agent stores quality metrics (loudness, clarity) per workflow.
  - Performance agent logs before/after stats.
- **Calculation:** Compare average quality score for workflows using premium features vs. basic; surface delta.
- **UI Placement:** Feature detail accordion and testimonial strip.

### 3. Support Load Reduction
- **Purpose:** Show how higher tiers reduce manual oversight (less downtime, fewer failures).
- **Data Sources:**
  - Message bus dead-letter queue counts.
  - Agent retry metrics.
- **Calculation:** `manual_interventions / total_workflows` before vs. after upgrade.
- **UI Placement:** Upgrade proof strip to emphasize reliability gains.

### 4. Collaboration Capacity
- **Purpose:** Tie Spaces usage to tier offerings (e.g., number of concurrent collaborators).
- **Data Sources:**
  - Metadata agent tracks collaborators per project.
  - Workflow engine records simultaneous sessions.
- **Calculation:** Current collaborators vs. tier limit; highlight overflow potential.
- **UI Placement:** Tier comparison cards and CTA modals.

### 5. ROI Projection
- **Purpose:** Forecast payback period for upgrading using Finance KPIs.
- **Data Sources:**
  - Billable hours saved + revenue impact metrics.
  - Upgrade tier pricing.
- **Calculation:** `payback_days = upgrade_cost / (dollar_savings_per_day)`.
- **UI Placement:** Upgrade CTA strip with dynamic text (e.g., "Upgrade pays for itself in 9 days").

---

## Data Pipeline Notes
1. Extend workflow engine telemetry endpoint to expose aggregated stats (per time window) for GUI consumption.
2. Cache computed KPIs in the metadata agent for fast dashboard loads; recompute on workflow completion.
3. Ensure Account page captures hourly rate, tier, and collaborator limits to parameterize Finance/Upgrade calculations.
4. Align terminology with Remote Labor Index narrative to contextualize automation rate figures during messaging.
