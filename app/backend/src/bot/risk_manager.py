"""
Risk Manager Module - Risk Management and Position Sizing.

This module provides stateless risk management calculations and
validations for trading operations.
"""

import logging
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskParameters:
    """Risk management parameters for position sizing."""

    max_position_size: float = 1000.0  # Maximum position size in USD
    max_positions: int = 10  # Maximum number of open positions
    max_portfolio_risk: float = 0.02  # Maximum 2% portfolio risk per trade
    max_daily_loss: float = 0.05  # Maximum 5% daily loss
    risk_reward_ratio: float = 2.0  # Minimum 2:1 risk/reward ratio
    max_leverage: float = 5.0  # Maximum leverage allowed


class RiskManager:
    """Stateless risk manager for trading operations."""

    @staticmethod
    def calculate_position_size(
        account_balance: float,
        risk_percentage: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """Calculate safe position size based on risk management.

        Args:
            account_balance: Total account balance in USD
            risk_percentage: Risk percentage per trade (0.01 = 1%)
            entry_price: Entry price for the position
            stop_loss_price: Stop loss price for risk calculation

        Returns:
            Recommended position size in base currency

        Raises:
            ValueError: If risk parameters are invalid
        """
        try:
            # Validate inputs
            if account_balance <= 0:
                raise ValueError("Account balance must be positive")

            if not 0 < risk_percentage <= 1:
                raise ValueError("Risk percentage must be between 0 and 1")

            if entry_price <= 0 or stop_loss_price <= 0:
                raise ValueError("Prices must be positive")

            # Calculate risk amount in USD
            risk_amount = account_balance * risk_percentage

            # Calculate price difference for risk
            if entry_price > stop_loss_price:
                # Long position
                price_diff = entry_price - stop_loss_price
            else:
                # Short position
                price_diff = stop_loss_price - entry_price

            if price_diff <= 0:
                raise ValueError("Invalid stop loss price for position direction")

            # Calculate position size
            position_size = risk_amount / price_diff

            logger.info(f"Calculated position size: {position_size} (risk: ${risk_amount})")

            return position_size

        except Exception as e:
            logger.error(f"Failed to calculate position size: {e}")
            raise ValueError(f"Position size calculation failed: {str(e)}")

    @staticmethod
    def validate_order_parameters(
        symbol: str,
        side: str,
        size: float,
        price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """Validate order parameters for safety.

        Args:
            symbol: Trading pair symbol
            side: Order side ('BUY' or 'SELL')
            size: Order size
            price: Order price (for limit orders)

        Returns:
            Tuple of (is_valid, error_message)

        Raises:
            ValueError: If validation fails critically
        """
        try:
            # Validate symbol
            if not symbol or len(symbol) < 3:
                return False, "Invalid symbol format"

            if '-' not in symbol:
                return False, "Symbol must contain '-' (e.g., 'BTC-USD')"

            # Validate side
            if side.upper() not in ['BUY', 'SELL']:
                return False, f"Invalid side: {side}. Must be 'BUY' or 'SELL'"

            # Validate size
            if not isinstance(size, (int, float)) or size <= 0:
                return False, "Size must be a positive number"

            # Size limits (very large or very small orders)
            if size > 1000000:  # 1M max size
                return False, "Order size too large"

            if size < 0.000001:  # 1e-6 min size
                return False, "Order size too small"

            # Validate price for limit orders
            if price is not None:
                if not isinstance(price, (int, float)) or price <= 0:
                    return False, "Price must be a positive number"

                if price > 1000000:  # $1M max price
                    return False, "Price too high"

                if price < 0.000001:  # $1e-6 min price
                    return False, "Price too low"

            return True, "Valid order parameters"

        except Exception as e:
            logger.error(f"Order validation error: {e}")
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def calculate_take_profit_price(
        entry_price: float,
        stop_loss_price: float,
        risk_reward_ratio: float
    ) -> float:
        """Calculate take profit price based on risk/reward ratio.

        Args:
            entry_price: Entry price of the position
            stop_loss_price: Stop loss price
            risk_reward_ratio: Desired risk/reward ratio (e.g., 2.0 for 2:1)

        Returns:
            Calculated take profit price

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            # Validate inputs
            if entry_price <= 0 or stop_loss_price <= 0:
                raise ValueError("Prices must be positive")

            if risk_reward_ratio <= 0:
                raise ValueError("Risk/reward ratio must be positive")

            # Calculate price difference for risk
            if entry_price > stop_loss_price:
                # Long position
                risk_distance = entry_price - stop_loss_price
                direction = 1  # Up for long
            else:
                # Short position
                risk_distance = stop_loss_price - entry_price
                direction = -1  # Down for short

            if risk_distance <= 0:
                raise ValueError("Invalid stop loss price for position direction")

            # Calculate reward distance
            reward_distance = risk_distance * risk_reward_ratio

            # Calculate take profit price
            take_profit_price = entry_price + (reward_distance * direction)

            logger.info(f"Calculated TP: {take_profit_price} (R:R {risk_reward_ratio})")

            return take_profit_price

        except Exception as e:
            logger.error(f"Failed to calculate take profit price: {e}")
            raise ValueError(f"Take profit calculation failed: {str(e)}")

    @staticmethod
    def check_position_limits(
        current_positions: List[Dict[str, Any]],
        new_position_size: float,
        max_positions: int = 10
    ) -> Tuple[bool, str]:
        """Check if new position would exceed limits.

        Args:
            current_positions: List of current open positions
            new_position_size: Size of new position in USD
            max_positions: Maximum allowed open positions

        Returns:
            Tuple of (within_limits, reason)
        """
        try:
            # Check position count limit
            if len(current_positions) >= max_positions:
                return False, f"Maximum positions ({max_positions}) exceeded"

            # Calculate total current exposure
            total_exposure = sum(
                float(pos.get('notional_value', 0))
                for pos in current_positions
            )

            # Calculate new total exposure
            new_total_exposure = total_exposure + new_position_size

            # Check total exposure limit (e.g., 10x account balance)
            max_exposure = 100000  # $100k max total exposure
            if new_total_exposure > max_exposure:
                return False, f"Total exposure would exceed ${max_exposure}"

            # Check individual position size limit
            max_single_position = 10000  # $10k max per position
            if new_position_size > max_single_position:
                return False, f"Position size exceeds ${max_single_position} limit"

            return True, "Position within limits"

        except Exception as e:
            logger.error(f"Position limits check error: {e}")
            return False, f"Limits check error: {str(e)}"

    @staticmethod
    def calculate_portfolio_risk(
        account_balance: float,
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall portfolio risk metrics.

        Args:
            account_balance: Total account balance
            positions: List of current positions

        Returns:
            Dictionary with risk metrics
        """
        try:
            if account_balance <= 0:
                return {
                    'total_risk': 0,
                    'risk_percentage': 0,
                    'position_count': len(positions),
                    'diversification_ratio': 0,
                }

            # Calculate total notional exposure
            total_exposure = sum(
                float(pos.get('notional_value', 0))
                for pos in positions
            )

            # Calculate risk percentage
            risk_percentage = total_exposure / account_balance if account_balance > 0 else 0

            # Calculate diversification (simplified)
            diversification_ratio = min(len(positions) / 5.0, 1.0)  # Max 5 positions for full diversification

            return {
                'total_risk': total_exposure,
                'risk_percentage': risk_percentage,
                'position_count': len(positions),
                'diversification_ratio': diversification_ratio,
                'leverage': total_exposure / account_balance,
            }

        except Exception as e:
            logger.error(f"Portfolio risk calculation error: {e}")
            return {
                'total_risk': 0,
                'risk_percentage': 0,
                'position_count': 0,
                'diversification_ratio': 0,
                'error': str(e),
            }

    @staticmethod
    def validate_market_conditions(
        symbol: str,
        current_price: float,
        daily_volume: float,
        price_change_24h: float
    ) -> Tuple[bool, str]:
        """Validate market conditions for trading.

        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            daily_volume: 24h trading volume in USD
            price_change_24h: 24h price change percentage

        Returns:
            Tuple of (conditions_ok, reason)
        """
        try:
            # Check minimum price
            if current_price < 0.000001:
                return False, "Price too low for safe trading"

            # Check maximum price
            if current_price > 1000000:
                return False, "Price too high for safe trading"

            # Check minimum volume (liquidity)
            min_volume = 10000  # $10k minimum daily volume
            if daily_volume < min_volume:
                return False, f"Insufficient liquidity (${daily_volume} < ${min_volume})"

            # Check extreme volatility
            max_volatility = 50  # 50% max 24h change
            if abs(price_change_24h) > max_volatility:
                return False, f"Extreme volatility ({price_change_24h}% in 24h)"

            return True, "Market conditions acceptable"

        except Exception as e:
            logger.error(f"Market conditions validation error: {e}")
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def calculate_max_drawdown(
        balance_history: List[float]
    ) -> float:
        """Calculate maximum drawdown from balance history.

        Args:
            balance_history: List of historical account balances

        Returns:
            Maximum drawdown as percentage (0.0 to 1.0)
        """
        try:
            if len(balance_history) < 2:
                return 0.0

            max_balance = max(balance_history)
            min_balance = min(balance_history)

            if max_balance <= 0:
                return 0.0

            drawdown = (max_balance - min_balance) / max_balance

            return min(drawdown, 1.0)  # Cap at 100%

        except Exception as e:
            logger.error(f"Drawdown calculation error: {e}")
            return 0.0

    @staticmethod
    def should_trigger_emergency_stop(
        current_balance: float,
        initial_balance: float,
        max_positions: int,
        current_positions: List[Dict[str, Any]],
        max_drawdown: float = 0.1  # 10% max drawdown
    ) -> Tuple[bool, str]:
        """Check if emergency stop should be triggered.

        Args:
            current_balance: Current account balance
            initial_balance: Initial account balance
            max_positions: Maximum allowed positions
            current_positions: Current open positions
            max_drawdown: Maximum allowed drawdown (0.1 = 10%)

        Returns:
            Tuple of (should_stop, reason)
        """
        try:
            # Check drawdown
            if initial_balance > 0:
                drawdown = (initial_balance - current_balance) / initial_balance
                if drawdown > max_drawdown:
                    return True, f"Maximum drawdown exceeded ({drawdown:.1%})"

            # Check position count
            if len(current_positions) > max_positions:
                return True, f"Maximum positions exceeded ({len(current_positions)} > {max_positions})"

            # Check for negative balance
            if current_balance < 0:
                return True, "Negative account balance detected"

            return False, "No emergency conditions detected"

        except Exception as e:
            logger.error(f"Emergency stop check error: {e}")
            return True, f"Emergency check error: {str(e)}"