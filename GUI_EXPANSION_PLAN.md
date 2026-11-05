# GUI Expansion Roadmap

This checklist extends the navigation wireframes and telemetry work into a full PySide6 application.

## Sprint 1 – Data Plumbing
- [ ] Expose workflow + agent events via async queues so GUI updates without polling.
- [ ] Persist telemetry snapshots to `metadata.db` for long-term Finance history.
- [ ] Implement account preference schema (hourly rate, collaborator limits, tier).

## Sprint 2 – UI Composition
- [ ] Build `HomeView`, `DiscoverView`, `SpacesView`, `FinanceView`, `AccountView`, `UpgradeView` widgets using the layouts in `GUI_NAVIGATION_WIREFRAMES.md`.
- [ ] Create shared component kit (cards, KPI tiles, utilization bars).
- [ ] Hook `NavigationViewport` to actual tabs and add `QStackedWidget` transitions.

## Sprint 3 – Advanced Metrics
- [ ] Track revision turnaround explicitly via metadata agent callbacks.
- [ ] Pipe performance agent alerts into Finance ROI graphs for “support load” metrics.
- [ ] Display automation-vs-manual ratio per workflow and surface manual intervention feeds in Upgrade view.

## Sprint 4 – Integrations
- [ ] Add import/export for Music.ai / Kits.ai / Suno stems with metadata tagging.
- [ ] Embed account linking (OAuth or API tokens) for those services inside Account → Integrations.
- [ ] Offer Upgrade tier upsell bundles that include voice packs or Suno pipeline connectors.

## Sprint 5 – Collaboration & Monetization
- [ ] Implement Spaces live presence indicators + chat.
- [ ] Introduce billing view tying Finance KPIs to Stripe/PayPal invoicing.
- [ ] Launch upgrade paywall flows with ROI projection banner + one-click upgrade.
