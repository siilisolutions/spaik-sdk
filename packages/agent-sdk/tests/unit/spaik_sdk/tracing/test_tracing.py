"""Unit tests for tracing module - NoOpTraceSink, configure_tracing, get_trace_sink resolution."""

from unittest.mock import MagicMock

import pytest

from spaik_sdk.tracing import (
    LocalTraceSink,
    NoOpTraceSink,
    TraceSink,
    TraceSinkMode,
    configure_tracing,
    get_trace_sink,
)


@pytest.fixture(autouse=True)
def reset_global_sink():
    """Reset global sink before and after each test."""
    configure_tracing(None)
    yield
    configure_tracing(None)


@pytest.fixture
def clean_env(monkeypatch):
    """Remove TRACE_SINK_MODE env var for clean testing."""
    monkeypatch.delenv("TRACE_SINK_MODE", raising=False)
    return monkeypatch


@pytest.mark.unit
class TestNoOpTraceSink:
    """Tests for NoOpTraceSink class."""

    def test_save_trace_does_not_throw(self):
        """Calling save_trace does not throw and has no side effects."""
        sink = NoOpTraceSink()
        # Should not raise any exception
        sink.save_trace("test_name", "trace content", "system prompt")

    def test_save_trace_with_any_parameters(self):
        """Calling save_trace with any combination of parameters succeeds silently."""
        sink = NoOpTraceSink()

        # Empty strings
        sink.save_trace("", "", "")

        # Long strings
        sink.save_trace("a" * 10000, "b" * 10000, "c" * 10000)

        # Unicode
        sink.save_trace("test\u2603", "\U0001f600 emoji", "\u0645\u062b\u0627\u0644")

        # Special characters
        sink.save_trace("test\nwith\nnewlines", "tab\there", "null\x00char")

    def test_implements_trace_sink_interface(self):
        """NoOpTraceSink properly implements the TraceSink interface."""
        sink = NoOpTraceSink()
        assert isinstance(sink, TraceSink)


@pytest.mark.unit
class TestConfigureTracing:
    """Tests for configure_tracing function."""

    def test_configure_with_custom_sink(self, clean_env):
        """After calling configure_tracing with a custom sink, get_trace_sink returns that sink."""
        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)

        result = get_trace_sink()
        assert result is custom_sink

    def test_configure_multiple_times_replaces_sink(self, clean_env):
        """Calling configure_tracing multiple times replaces the previous sink."""
        sink1 = MagicMock(spec=TraceSink)
        sink2 = MagicMock(spec=TraceSink)

        configure_tracing(sink1)
        assert get_trace_sink() is sink1

        configure_tracing(sink2)
        assert get_trace_sink() is sink2

    def test_configure_with_none_clears_global_sink(self, clean_env):
        """Calling configure_tracing with None clears the global sink."""
        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)
        assert get_trace_sink() is custom_sink

        configure_tracing(None)
        result = get_trace_sink()
        assert isinstance(result, NoOpTraceSink)


@pytest.mark.unit
class TestGetTraceSinkResolution:
    """Tests for get_trace_sink resolution logic."""

    def test_env_var_local_returns_local_sink(self, monkeypatch):
        """When TRACE_SINK_MODE=local env var is set, returns LocalTraceSink regardless of global config."""
        monkeypatch.setenv("TRACE_SINK_MODE", "local")

        # Even with a custom global sink configured
        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)

        result = get_trace_sink()
        assert isinstance(result, LocalTraceSink)

    def test_env_var_noop_returns_noop_sink(self, monkeypatch):
        """When TRACE_SINK_MODE=noop env var is set, returns NoOpTraceSink regardless of global config."""
        monkeypatch.setenv("TRACE_SINK_MODE", "noop")

        # Even with a custom global sink configured
        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)

        result = get_trace_sink()
        assert isinstance(result, NoOpTraceSink)

    def test_unset_env_var_with_global_sink_returns_global(self, clean_env):
        """When TRACE_SINK_MODE is unset and global sink is configured, returns the global sink."""
        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)

        result = get_trace_sink()
        assert result is custom_sink

    def test_unset_env_var_no_global_returns_noop(self, clean_env):
        """When TRACE_SINK_MODE is unset and no global sink configured, returns NoOpTraceSink."""
        result = get_trace_sink()
        assert isinstance(result, NoOpTraceSink)

    def test_invalid_env_var_falls_through_to_global(self, monkeypatch):
        """When TRACE_SINK_MODE is set to invalid value, falls through to global/no-op (no error)."""
        monkeypatch.setenv("TRACE_SINK_MODE", "invalid_value")

        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)

        # Should use global sink (not raise error)
        result = get_trace_sink()
        assert result is custom_sink

    def test_invalid_env_var_falls_through_to_noop(self, monkeypatch):
        """When TRACE_SINK_MODE is invalid and no global sink, falls through to NoOpTraceSink."""
        monkeypatch.setenv("TRACE_SINK_MODE", "typo_local")

        result = get_trace_sink()
        assert isinstance(result, NoOpTraceSink)

    def test_env_var_local_takes_precedence_over_configure(self, monkeypatch):
        """Env var LOCAL takes precedence over configure_tracing (escape hatch works)."""
        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)

        monkeypatch.setenv("TRACE_SINK_MODE", "local")

        result = get_trace_sink()
        assert isinstance(result, LocalTraceSink)

    def test_env_var_noop_takes_precedence_over_configure(self, monkeypatch):
        """Env var NOOP takes precedence over configure_tracing."""
        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)

        monkeypatch.setenv("TRACE_SINK_MODE", "noop")

        result = get_trace_sink()
        assert isinstance(result, NoOpTraceSink)

    def test_explicit_mode_parameter_overrides_all(self, monkeypatch):
        """Explicit mode parameter to get_trace_sink overrides everything."""
        # Set up env var
        monkeypatch.setenv("TRACE_SINK_MODE", "local")

        # Set up global sink
        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)

        # Explicit NOOP mode should override
        result = get_trace_sink(mode=TraceSinkMode.NOOP)
        assert isinstance(result, NoOpTraceSink)

        # Explicit LOCAL mode
        result = get_trace_sink(mode=TraceSinkMode.LOCAL)
        assert isinstance(result, LocalTraceSink)

    def test_empty_env_var_treated_as_unset(self, monkeypatch):
        """Empty TRACE_SINK_MODE env var is treated as unset."""
        monkeypatch.setenv("TRACE_SINK_MODE", "")

        custom_sink = MagicMock(spec=TraceSink)
        configure_tracing(custom_sink)

        result = get_trace_sink()
        assert result is custom_sink


@pytest.mark.unit
class TestTraceSinkMode:
    """Tests for TraceSinkMode enum."""

    def test_from_name_returns_local(self):
        """from_name returns LOCAL for 'local' string."""
        result = TraceSinkMode.from_name("local")
        assert result == TraceSinkMode.LOCAL

    def test_from_name_returns_noop(self):
        """from_name returns NOOP for 'noop' string."""
        result = TraceSinkMode.from_name("noop")
        assert result == TraceSinkMode.NOOP

    def test_from_name_returns_none_for_empty_string(self):
        """from_name returns None for empty string."""
        result = TraceSinkMode.from_name("")
        assert result is None

    def test_from_name_returns_none_for_none(self):
        """from_name returns None for None input."""
        result = TraceSinkMode.from_name(None)
        assert result is None

    def test_from_name_case_insensitive(self):
        """from_name is case insensitive."""
        assert TraceSinkMode.from_name("LOCAL") == TraceSinkMode.LOCAL
        assert TraceSinkMode.from_name("Local") == TraceSinkMode.LOCAL
        assert TraceSinkMode.from_name("NOOP") == TraceSinkMode.NOOP
        assert TraceSinkMode.from_name("NoOp") == TraceSinkMode.NOOP

    def test_from_name_invalid_returns_none(self):
        """from_name returns None for invalid values (no error)."""
        result = TraceSinkMode.from_name("invalid")
        assert result is None

        result = TraceSinkMode.from_name("filesystem")
        assert result is None
