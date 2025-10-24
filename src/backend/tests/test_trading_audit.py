"""Unit Tests for Trading Audit Module.

Tests for order validation, position lifecycle, and best practices compliance.
"""

import pytest
from src.bot.trading_audit import (
    TradingAudit,
    OrderStatus,
    TimeInForce,
    AuditLogger,
)


class TestOrderParameterValidation:
    """Test order parameter validation."""

    def test_valid_order_parameters(self):
        """Test valid order parameters."""
        is_valid, errors = TradingAudit.validate_order_parameters(
            symbol="BTC-USD",
            side="BUY",
            size=1.0,
            price=50000,
            time_in_force="GTT",
        )
        assert is_valid
        assert len(errors) == 0

    def test_invalid_symbol(self):
        """Test invalid symbol format."""
        is_valid, errors = TradingAudit.validate_order_parameters(
            symbol="BTCUSD",
            side="BUY",
            size=1.0,
            price=50000,
        )
        assert not is_valid
        assert any("symbol" in e.lower() for e in errors)

    def test_invalid_side(self):
        """Test invalid order side."""
        is_valid, errors = TradingAudit.validate_order_parameters(
            symbol="BTC-USD",
            side="INVALID",
            size=1.0,
            price=50000,
        )
        assert not is_valid
        assert any("side" in e.lower() for e in errors)

    def test_invalid_size(self):
        """Test invalid order size."""
        is_valid, errors = TradingAudit.validate_order_parameters(
            symbol="BTC-USD",
            side="BUY",
            size=-1.0,
            price=50000,
        )
        assert not is_valid
        assert any("size" in e.lower() for e in errors)

    def test_invalid_time_in_force(self):
        """Test invalid time in force."""
        is_valid, errors = TradingAudit.validate_order_parameters(
            symbol="BTC-USD",
            side="BUY",
            size=1.0,
            price=50000,
            time_in_force="INVALID",
        )
        assert not is_valid
        assert any("time_in_force" in e.lower() for e in errors)


class TestOrderLifecycle:
    """Test order lifecycle validation."""

    def test_valid_status_transition_pending_to_open(self):
        """Test valid transition: PENDING → OPEN."""
        is_valid, errors = TradingAudit.validate_order_lifecycle(
            order_id="order1",
            current_status="OPEN",
            previous_status="PENDING",
        )
        assert is_valid
        assert len(errors) == 0

    def test_valid_status_transition_open_to_filled(self):
        """Test valid transition: OPEN → FILLED."""
        is_valid, errors = TradingAudit.validate_order_lifecycle(
            order_id="order1",
            current_status="FILLED",
            previous_status="OPEN",
        )
        assert is_valid
        assert len(errors) == 0

    def test_invalid_status_transition(self):
        """Test invalid status transition."""
        is_valid, errors = TradingAudit.validate_order_lifecycle(
            order_id="order1",
            current_status="PENDING",
            previous_status="FILLED",
        )
        assert not is_valid
        assert any("transition" in e.lower() for e in errors)

    def test_invalid_status(self):
        """Test invalid order status."""
        is_valid, errors = TradingAudit.validate_order_lifecycle(
            order_id="order1",
            current_status="INVALID_STATUS",
        )
        assert not is_valid
        assert any("invalid" in e.lower() for e in errors)


class TestPositionLifecycle:
    """Test position lifecycle validation."""

    def test_valid_position_lifecycle(self):
        """Test valid position lifecycle."""
        is_valid, errors = TradingAudit.validate_position_lifecycle(
            position_id="pos1",
            entry_order_status="FILLED",
            tp_order_status="OPEN",
            sl_order_status="OPEN",
        )
        assert is_valid
        assert len(errors) == 0

    def test_missing_tp_order(self):
        """Test missing take profit order."""
        is_valid, errors = TradingAudit.validate_position_lifecycle(
            position_id="pos1",
            entry_order_status="FILLED",
            tp_order_status=None,
            sl_order_status="OPEN",
        )
        assert not is_valid
        assert any("take profit" in e.lower() for e in errors)

    def test_missing_sl_order(self):
        """Test missing stop loss order."""
        is_valid, errors = TradingAudit.validate_position_lifecycle(
            position_id="pos1",
            entry_order_status="FILLED",
            tp_order_status="OPEN",
            sl_order_status=None,
        )
        assert not is_valid
        assert any("stop loss" in e.lower() for e in errors)


class TestTPSLValidation:
    """Test take profit and stop loss validation."""

    def test_valid_tp_sl_long_position(self):
        """Test valid TP/SL for LONG position."""
        is_valid, errors = TradingAudit.validate_tp_sl_orders(
            entry_price=50000,
            tp_price=52000,
            sl_price=48000,
            side="BUY",
        )
        assert is_valid
        assert len(errors) == 0

    def test_valid_tp_sl_short_position(self):
        """Test valid TP/SL for SHORT position."""
        is_valid, errors = TradingAudit.validate_tp_sl_orders(
            entry_price=50000,
            tp_price=48000,
            sl_price=52000,
            side="SELL",
        )
        assert is_valid
        assert len(errors) == 0

    def test_invalid_tp_long_position(self):
        """Test invalid TP for LONG position (below entry)."""
        is_valid, errors = TradingAudit.validate_tp_sl_orders(
            entry_price=50000,
            tp_price=49000,
            sl_price=48000,
            side="BUY",
        )
        assert not is_valid
        assert any("tp" in e.lower() and "above" in e.lower() for e in errors)

    def test_invalid_sl_long_position(self):
        """Test invalid SL for LONG position (above entry)."""
        is_valid, errors = TradingAudit.validate_tp_sl_orders(
            entry_price=50000,
            tp_price=52000,
            sl_price=51000,
            side="BUY",
        )
        assert not is_valid
        assert any("sl" in e.lower() and "below" in e.lower() for e in errors)


class TestPartialFillHandling:
    """Test partial fill validation."""

    def test_valid_partial_fill(self):
        """Test valid partial fill."""
        is_valid, errors = TradingAudit.validate_partial_fill_handling(
            original_size=1.0,
            filled_size=0.6,
            remaining_size=0.4,
        )
        assert is_valid
        assert len(errors) == 0

    def test_size_mismatch(self):
        """Test size mismatch."""
        is_valid, errors = TradingAudit.validate_partial_fill_handling(
            original_size=1.0,
            filled_size=0.6,
            remaining_size=0.3,
        )
        assert not is_valid
        assert any("mismatch" in e.lower() for e in errors)

    def test_negative_filled_size(self):
        """Test negative filled size."""
        is_valid, errors = TradingAudit.validate_partial_fill_handling(
            original_size=1.0,
            filled_size=-0.1,
            remaining_size=1.1,
        )
        assert not is_valid
        assert any("negative" in e.lower() for e in errors)

    def test_filled_exceeds_original(self):
        """Test filled size exceeds original."""
        is_valid, errors = TradingAudit.validate_partial_fill_handling(
            original_size=1.0,
            filled_size=1.5,
            remaining_size=-0.5,
        )
        assert not is_valid
        assert any("exceeds" in e.lower() for e in errors)


class TestOrderCancellation:
    """Test order cancellation validation."""

    def test_valid_cancellation_open_order(self):
        """Test valid cancellation of OPEN order."""
        is_valid, errors = TradingAudit.validate_order_cancellation(
            order_status="OPEN",
            reason="Manual cancellation",
        )
        assert is_valid
        assert len(errors) == 0

    def test_valid_cancellation_partial_fill(self):
        """Test valid cancellation of PARTIALLY_FILLED order."""
        is_valid, errors = TradingAudit.validate_order_cancellation(
            order_status="PARTIALLY_FILLED",
            reason="Manual cancellation",
        )
        assert is_valid
        assert len(errors) == 0

    def test_invalid_cancellation_filled_order(self):
        """Test invalid cancellation of FILLED order."""
        is_valid, errors = TradingAudit.validate_order_cancellation(
            order_status="FILLED",
            reason="Manual cancellation",
        )
        assert not is_valid
        assert any("cannot cancel" in e.lower() for e in errors)

    def test_missing_cancellation_reason(self):
        """Test missing cancellation reason."""
        is_valid, errors = TradingAudit.validate_order_cancellation(
            order_status="OPEN",
            reason=None,
        )
        assert not is_valid
        assert any("reason" in e.lower() for e in errors)


class TestPositionClosure:
    """Test position closure validation."""

    def test_valid_position_closure(self):
        """Test valid position closure."""
        is_valid, errors = TradingAudit.validate_position_closure(
            position_status="OPEN",
            entry_order_status="FILLED",
            tp_order_status="FILLED",
            sl_order_status="OPEN",
        )
        assert is_valid
        assert len(errors) == 0

    def test_invalid_position_status(self):
        """Test invalid position status for closure."""
        is_valid, errors = TradingAudit.validate_position_closure(
            position_status="CLOSED",
            entry_order_status="FILLED",
            tp_order_status="FILLED",
        )
        assert not is_valid
        assert any("cannot close" in e.lower() for e in errors)

    def test_entry_order_not_filled(self):
        """Test entry order not filled."""
        is_valid, errors = TradingAudit.validate_position_closure(
            position_status="OPEN",
            entry_order_status="OPEN",
            tp_order_status="OPEN",
        )
        assert not is_valid
        assert any("entry order" in e.lower() for e in errors)


class TestAuditReport:
    """Test audit report generation."""

    def test_generate_audit_report(self):
        """Test audit report generation."""
        positions = [
            {
                "id": "pos1",
                "status": "open",
                "tp_order_id": "tp1",
                "sl_order_id": "sl1",
            },
            {
                "id": "pos2",
                "status": "closed",
                "tp_order_id": "tp2",
                "sl_order_id": "sl2",
            },
        ]
        orders = [
            {"id": "order1", "status": "FILLED"},
            {"id": "order2", "status": "OPEN"},
            {"id": "order3", "status": "PARTIALLY_FILLED"},
        ]

        report = TradingAudit.generate_audit_report(positions, orders)

        assert report["total_positions"] == 2
        assert report["total_orders"] == 3
        assert report["statistics"]["positions_by_status"]["open"] == 1
        assert report["statistics"]["positions_by_status"]["closed"] == 1
        assert report["statistics"]["orders_by_status"]["FILLED"] == 1
        assert report["statistics"]["partial_fill_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
