"""Event bus implementation using blinker."""

from typing import Any, Callable

from blinker import signal

from docforge.core.interfaces.adapters import EventBusAdapter


class BlinkerEventBusAdapter(EventBusAdapter):
    """Event bus implementation using blinker signal library.
    
    Features:
    - Signal-based pub/sub
    - Type-safe event publishing
    - Named signals for lifecycle events
    """

    def __init__(self) -> None:
        """Initialize event bus with common DocForge lifecycle events."""
        # Pre-define common signals to avoid typos
        self._signals: dict[str, signal] = {}
        self._register_signal("pipeline.start")
        self._register_signal("pipeline.stage.begin")
        self._register_signal("pipeline.stage.end")
        self._register_signal("pipeline.stage.error")
        self._register_signal("pipeline.complete")
        self._register_signal("artifact.saved")
        self._register_signal("artifact.loaded")

    def _register_signal(self, event_type: str) -> signal:
        """Register or get a signal by type name.
        
        Args:
            event_type: Unique signal name
            
        Returns:
            Blinker signal object
        """
        if event_type not in self._signals:
            self._signals[event_type] = signal(event_type)
        return self._signals[event_type]

    def subscribe(self, event_type: str, handler: Callable[..., Any]) -> None:
        """Subscribe to event type.
        
        Args:
            event_type: Signal name to subscribe to
            handler: Callable that will be invoked when signal fires
        """
        sig = self._register_signal(event_type)
        sig.connect(handler)

    def unsubscribe(self, event_type: str, handler: Callable[..., Any]) -> None:
        """Unsubscribe from event type.
        
        Args:
            event_type: Signal name to unsubscribe from
            handler: Callable to disconnect
        """
        sig = self._register_signal(event_type)
        sig.disconnect(handler)

    def publish(self, event_type: str, **data: Any) -> None:
        """Publish event to all subscribers.
        
        Args:
            event_type: Signal name to fire
            **data: Keyword arguments passed to all handlers
        """
        sig = self._register_signal(event_type)
        sig.send(self, **data)
