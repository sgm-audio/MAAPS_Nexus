"""
PySide6 navigation scaffolding.

Provides the first pass at wiring GUI sections (Home, Discover, etc.)
to the MultiAgentSystem data providers. The UI layer is intentionally
minimal so it can run before PySide6 is installed; widgets will only
render when the dependency is available.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget
except Exception:  # pragma: no cover - PySide6 not available in CI
    QLabel = QStackedWidget = QVBoxLayout = QWidget = object  # type: ignore


class NavigationDataProvider:
    """Collects data for each navigation tab."""

    def __init__(self, system: "MultiAgentSystem"):
        self.system = system

    def home_cards(self) -> Dict[str, Any]:
        """Summaries for Home tab."""
        return {
            "health": self.system.get_health(),
            "finance": self.system.get_finance_metrics(),
            "agents": self.system.get_all_agents() if self.system.initialized else [],
        }

    def discover_content(self) -> List[Dict[str, Any]]:
        """Highlight MAAPS concepts for Discover tab."""
        return [
            {
                "title": "Emergent Musical Intelligence",
                "description": "Cross-agent learning and context memory.",
                "cta": "Read Concept Brief",
            },
            {
                "title": "Temporal Context Awareness",
                "description": "Past-present-future processing for every workflow.",
                "cta": "View Demo",
            },
        ]

    def spaces_projects(self) -> Dict[str, Any]:
        """Placeholder project summaries for Spaces tab."""
        return {
            "projects": [],
            "collaborations": [],
        }

    def finance_metrics(self, hourly_rate: float = 75.0) -> Dict[str, Any]:
        return self.system.get_finance_metrics(hourly_rate)

    def upgrade_metrics(
        self, account_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self.system.get_upgrade_metrics(account_context or {})


class NavigationViewport(QWidget):  # type: ignore[misc]
    """
    Simplified stacked widget that renders navigation cards when PySide6
    is available. In headless mode this acts as a lightweight shim so
    downstream code can still instantiate the class for tests.
    """

    def __init__(
        self, provider: NavigationDataProvider, parent: Optional[QWidget] = None
    ):
        if QWidget is object:  # PySide6 unavailable
            self.provider = provider
            self._stack = None
            return

        super().__init__(parent)
        self.provider = provider
        self._stack = QStackedWidget(self)
        self._build_ui()

    def _build_ui(self):
        if QWidget is object:
            return

        layout = QVBoxLayout()
        layout.addWidget(self._stack)
        self.setLayout(layout)

        cards = self.provider.home_cards()
        health = cards.get("health", {})
        label = QLabel(f"System Status: {health.get('status', 'unknown')}")
        self._stack.addWidget(label)


# Late import to avoid circular dependency during typing
try:  # pragma: no cover
    from ..system import MultiAgentSystem  # noqa: E402
except Exception:
    MultiAgentSystem = None  # type: ignore
