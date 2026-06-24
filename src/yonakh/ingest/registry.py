from __future__ import annotations

from yonakh.ingest.base import IngestPlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, IngestPlugin] = {}

    def register(self, plugin: IngestPlugin) -> None:
        self._plugins[plugin.name()] = plugin

    def get(self, name: str) -> IngestPlugin | None:
        return self._plugins.get(name)

    def list(self) -> list[IngestPlugin]:
        return list(self._plugins.values())


def get_default_registry() -> PluginRegistry:
    """Create a registry pre-loaded with built-in plugins."""
    from yonakh.ingest.git import GitIngestPlugin
    from yonakh.ingest.manual import ManualIngestPlugin

    registry = PluginRegistry()
    registry.register(GitIngestPlugin())
    registry.register(ManualIngestPlugin())
    return registry
