"""
Monitoring Manager Module - System Monitoring and Alerting.

This module provides comprehensive monitoring, metrics collection, and
alerting capabilities for the position monitoring system.
"""

import asyncio
import logging
import json
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Cycle metrics
    cycle_count: int = 0
    average_cycle_time: float = 0.0
    min_cycle_time: float = 0.0
    max_cycle_time: float = 0.0

    # Position metrics
    positions_processed: int = 0
    positions_closed: int = 0
    positions_failed: int = 0

    # Error metrics
    errors_total: int = 0
    consecutive_errors: int = 0

    # Performance metrics
    operations_per_second: float = 0.0
    success_rate: float = 0.0

    # Resource metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: str  # 'error_rate', 'cycle_time', 'success_rate', etc.
    threshold: float
    comparison: str  # 'gt', 'lt', 'gte', 'lte', 'eq'
    window_minutes: int = 5
    cooldown_minutes: int = 15
    severity: str = 'warning'  # 'info', 'warning', 'error', 'critical'


class MetricsCollector:
    """Collects and stores system metrics."""

    def __init__(self, max_history: int = 1000):
        """Initialize metrics collector.

        Args:
            max_history: Maximum number of metric records to keep
        """
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def record_metrics(self, metrics: SystemMetrics) -> None:
        """Record new system metrics."""
        async with self._lock:
            self.metrics_history.append(metrics)

            # Check alert rules
            await self._check_alert_rules(metrics)

    async def _check_alert_rules(self, current_metrics: SystemMetrics) -> None:
        """Check if any alert rules are triggered."""
        try:
            # Get recent metrics for window-based calculations
            window_start = datetime.utcnow() - timedelta(minutes=5)
            recent_metrics = [
                m for m in self.metrics_history
                if m.timestamp > window_start
            ]

            if not recent_metrics:
                return

            for rule in self.alert_rules:
                if await self._evaluate_alert_rule(rule, recent_metrics):
                    await self._trigger_alert(rule, current_metrics)

        except Exception as e:
            logger.error(f"Error checking alert rules: {e}")

    async def _evaluate_alert_rule(self, rule: AlertRule, metrics: List[SystemMetrics]) -> bool:
        """Evaluate if an alert rule condition is met."""
        try:
            if rule.name in self.active_alerts:
                # Check cooldown period
                last_trigger = self.active_alerts[rule.name]
                cooldown_end = last_trigger + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    return False

            # Calculate metrics based on rule condition
            if rule.condition == 'error_rate':
                error_rate = sum(m.errors_total for m in metrics) / len(metrics) if metrics else 0
                return self._compare_values(error_rate, rule.threshold, rule.comparison)

            elif rule.condition == 'cycle_time':
                cycle_times = [m.average_cycle_time for m in metrics if m.average_cycle_time > 0]
                if not cycle_times:
                    return False
                avg_cycle_time = statistics.mean(cycle_times)
                return self._compare_values(avg_cycle_time, rule.threshold, rule.comparison)

            elif rule.condition == 'success_rate':
                success_rates = [m.success_rate for m in metrics if m.success_rate > 0]
                if not success_rates:
                    return False
                avg_success_rate = statistics.mean(success_rates)
                return self._compare_values(avg_success_rate, rule.threshold, rule.comparison)

            elif rule.condition == 'consecutive_errors':
                # Check current metrics for consecutive errors
                return self._compare_values(
                    current_metrics.consecutive_errors,
                    rule.threshold,
                    rule.comparison
                )

            return False

        except Exception as e:
            logger.error(f"Error evaluating alert rule {rule.name}: {e}")
            return False

    def _compare_values(self, actual: float, threshold: float, comparison: str) -> bool:
        """Compare actual value with threshold using specified comparison."""
        if comparison == 'gt':
            return actual > threshold
        elif comparison == 'gte':
            return actual >= threshold
        elif comparison == 'lt':
            return actual < threshold
        elif comparison == 'lte':
            return actual <= threshold
        elif comparison == 'eq':
            return abs(actual - threshold) < 0.001  # Floating point comparison
        else:
            logger.error(f"Unknown comparison operator: {comparison}")
            return False

    async def _trigger_alert(self, rule: AlertRule, metrics: SystemMetrics) -> None:
        """Trigger an alert for a rule."""
        try:
            self.active_alerts[rule.name] = datetime.utcnow()

            alert_data = {
                'rule_name': rule.name,
                'condition': rule.condition,
                'threshold': rule.threshold,
                'comparison': rule.comparison,
                'severity': rule.severity,
                'timestamp': metrics.timestamp.isoformat(),
                'current_value': self._get_current_value(rule.condition, metrics),
                'message': self._format_alert_message(rule, metrics)
            }

            logger.warning(f"Alert triggered: {alert_data}")

            # In a real system, you would send this to an alerting system
            # For now, we'll just log it

        except Exception as e:
            logger.error(f"Error triggering alert for rule {rule.name}: {e}")

    def _get_current_value(self, condition: str, metrics: SystemMetrics) -> float:
        """Get current value for a condition."""
        if condition == 'error_rate':
            return metrics.errors_total
        elif condition == 'cycle_time':
            return metrics.average_cycle_time
        elif condition == 'success_rate':
            return metrics.success_rate
        elif condition == 'consecutive_errors':
            return metrics.consecutive_errors
        else:
            return 0.0

    def _format_alert_message(self, rule: AlertRule, metrics: SystemMetrics) -> str:
        """Format alert message."""
        current_value = self._get_current_value(rule.condition, metrics)

        if rule.condition == 'error_rate':
            return f"Error rate {current_value:.2f} exceeds threshold {rule.threshold}"
        elif rule.condition == 'cycle_time':
            return f"Average cycle time {current_value:.2f}s exceeds threshold {rule.threshold}s"
        elif rule.condition == 'success_rate':
            return f"Success rate {current_value:.2%} below threshold {rule.threshold:.2%}"
        elif rule.condition == 'consecutive_errors':
            return f"Consecutive errors {current_value} exceeds threshold {rule.threshold}"
        else:
            return f"Alert condition '{rule.condition}' met"

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_name: str) -> bool:
        """Remove an alert rule."""
        for i, rule in enumerate(self.alert_rules):
            if rule.name == rule_name:
                del self.alert_rules[i]
                logger.info(f"Removed alert rule: {rule_name}")
                return True
        return False

    def get_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get metrics summary for the specified time window."""
        try:
            window_start = datetime.utcnow() - timedelta(minutes=minutes)
            recent_metrics = [
                m for m in self.metrics_history
                if m.timestamp > window_start
            ]

            if not recent_metrics:
                return {'error': 'No metrics available for the specified window'}

            # Calculate summary statistics
            cycle_times = [m.average_cycle_time for m in recent_metrics if m.average_cycle_time > 0]
            success_rates = [m.success_rate for m in recent_metrics if m.success_rate > 0]

            summary = {
                'time_window_minutes': minutes,
                'total_cycles': len(recent_metrics),
                'cycle_time_stats': {
                    'average': statistics.mean(cycle_times) if cycle_times else 0,
                    'min': min(cycle_times) if cycle_times else 0,
                    'max': max(cycle_times) if cycle_times else 0,
                    'median': statistics.median(cycle_times) if cycle_times else 0,
                },
                'success_rate_stats': {
                    'average': statistics.mean(success_rates) if success_rates else 0,
                    'min': min(success_rates) if success_rates else 0,
                    'max': max(success_rates) if success_rates else 0,
                },
                'total_positions_processed': sum(m.positions_processed for m in recent_metrics),
                'total_positions_closed': sum(m.positions_closed for m in recent_metrics),
                'total_errors': sum(m.errors_total for m in recent_metrics),
                'active_alerts': len(self.active_alerts),
                'alert_rules_count': len(self.alert_rules),
            }

            return summary

        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {'error': str(e)}

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            if not self.metrics_history:
                return {
                    'status': 'unknown',
                    'message': 'No metrics available'
                }

            # Get the most recent metrics
            latest = self.metrics_history[-1]

            # Determine health based on recent performance
            health_score = 100

            # Penalize for errors
            if latest.consecutive_errors > 0:
                health_score -= min(latest.consecutive_errors * 10, 50)

            # Penalize for slow cycle times
            if latest.average_cycle_time > 60:  # More than 1 minute
                health_score -= 20
            elif latest.average_cycle_time > 30:  # More than 30 seconds
                health_score -= 10

            # Penalize for low success rate
            if latest.success_rate > 0:
                if latest.success_rate < 0.8:  # Less than 80%
                    health_score -= 20
                elif latest.success_rate < 0.9:  # Less than 90%
                    health_score -= 10

            # Determine status
            if health_score >= 90:
                status = 'healthy'
            elif health_score >= 70:
                status = 'warning'
            elif health_score >= 50:
                status = 'degraded'
            else:
                status = 'critical'

            return {
                'status': status,
                'health_score': health_score,
                'timestamp': latest.timestamp.isoformat(),
                'consecutive_errors': latest.consecutive_errors,
                'average_cycle_time': latest.average_cycle_time,
                'success_rate': latest.success_rate,
                'active_alerts': len(self.active_alerts),
            }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }


class MonitoringManager:
    """Main monitoring manager for the position monitoring system."""

    def __init__(self):
        """Initialize monitoring manager."""
        self.metrics_collector = MetricsCollector()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False

        # Setup default alert rules
        self._setup_default_alert_rules()

    def _setup_default_alert_rules(self) -> None:
        """Setup default alert rules for the system."""
        default_rules = [
            AlertRule(
                name='high_error_rate',
                condition='error_rate',
                threshold=0.1,  # 10% error rate
                comparison='gt',
                window_minutes=5,
                severity='warning'
            ),
            AlertRule(
                name='consecutive_errors',
                condition='consecutive_errors',
                threshold=3,
                comparison='gte',
                severity='error'
            ),
            AlertRule(
                name='slow_cycle_time',
                condition='cycle_time',
                threshold=60.0,  # 60 seconds
                comparison='gt',
                window_minutes=5,
                severity='warning'
            ),
            AlertRule(
                name='low_success_rate',
                condition='success_rate',
                threshold=0.8,  # 80% success rate
                comparison='lt',
                window_minutes=10,
                severity='error'
            ),
        ]

        for rule in default_rules:
            self.metrics_collector.add_alert_rule(rule)

    async def start_monitoring(self) -> None:
        """Start the monitoring system."""
        if self._is_running:
            logger.warning("Monitoring is already running")
            return

        self._is_running = True
        logger.info("Starting monitoring system...")

        # Start periodic metrics collection if needed
        # For now, metrics are collected when explicitly recorded

        logger.info("Monitoring system started")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        if not self._is_running:
            logger.warning("Monitoring is not running")
            return

        self._is_running = False
        logger.info("Monitoring system stopped")

    async def track_monitoring_metrics(
        self,
        cycle_time: float,
        positions_processed: int,
        positions_closed: int,
        errors: List[str]
    ) -> None:
        """Track monitoring performance metrics.

        Args:
            cycle_time: Time taken for the monitoring cycle
            positions_processed: Number of positions processed
            positions_closed: Number of positions closed
            errors: List of error messages
        """
        try:
            # Create metrics object
            metrics = SystemMetrics()

            # Update with current values
            if self.metrics_collector.metrics_history:
                latest = self.metrics_collector.metrics_history[-1]

                metrics.cycle_count = latest.cycle_count + 1
                metrics.positions_processed = latest.positions_processed + positions_processed
                metrics.positions_closed = latest.positions_closed + positions_closed
                metrics.positions_failed = latest.positions_failed + len(errors)
                metrics.errors_total = latest.errors_total + len(errors)
                metrics.consecutive_errors = len(errors) if errors else 0

                # Update cycle time statistics
                all_cycle_times = [m.average_cycle_time for m in self.metrics_collector.metrics_history]
                all_cycle_times.append(cycle_time)

                metrics.average_cycle_time = statistics.mean(all_cycle_times)
                metrics.min_cycle_time = min(all_cycle_times)
                metrics.max_cycle_time = max(all_cycle_times)

                # Calculate performance metrics
                if cycle_time > 0:
                    metrics.operations_per_second = positions_processed / cycle_time

                total_operations = metrics.positions_processed + metrics.positions_failed
                if total_operations > 0:
                    metrics.success_rate = metrics.positions_processed / total_operations
            else:
                # First metrics record
                metrics.cycle_count = 1
                metrics.positions_processed = positions_processed
                metrics.positions_closed = positions_closed
                metrics.positions_failed = len(errors)
                metrics.errors_total = len(errors)
                metrics.consecutive_errors = len(errors) if errors else 0
                metrics.average_cycle_time = cycle_time
                metrics.min_cycle_time = cycle_time
                metrics.max_cycle_time = cycle_time

                if cycle_time > 0:
                    metrics.operations_per_second = positions_processed / cycle_time

                total_operations = positions_processed + len(errors)
                if total_operations > 0:
                    metrics.success_rate = positions_processed / total_operations

            # Record the metrics
            await self.metrics_collector.record_metrics(metrics)

        except Exception as e:
            logger.error(f"Error tracking monitoring metrics: {e}")

    async def detect_anomalies(
        self,
        current_cycle: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Detect unusual patterns in position monitoring.

        Args:
            current_cycle: Current monitoring cycle data
            historical_data: Historical monitoring data

        Returns:
            List of detected anomalies
        """
        anomalies = []

        try:
            if not historical_data:
                return anomalies

            # Extract metrics for comparison
            current_cycle_time = current_cycle.get('cycle_time', 0)
            current_positions = current_cycle.get('positions_processed', 0)
            current_errors = len(current_cycle.get('errors', []))

            # Get historical averages
            cycle_times = [h.get('cycle_time', 0) for h in historical_data if h.get('cycle_time', 0) > 0]
            position_counts = [h.get('positions_processed', 0) for h in historical_data]
            error_counts = [len(h.get('errors', [])) for h in historical_data]

            if not cycle_times or not position_counts:
                return anomalies

            # Calculate historical averages
            avg_cycle_time = statistics.mean(cycle_times)
            avg_positions = statistics.mean(position_counts)
            avg_errors = statistics.mean(error_counts)

            # Detect anomalies
            if cycle_times:
                cycle_time_threshold = avg_cycle_time * 2  # 2x slower than average
                if current_cycle_time > cycle_time_threshold:
                    anomalies.append(
                        f"Cycle time {current_cycle_time:.2f}s is significantly slower than average {avg_cycle_time:.2f}s"
                    )

            if position_counts:
                position_threshold = max(avg_positions * 0.5, 1)  # Less than 50% of average or less than 1
                if current_positions < position_threshold:
                    anomalies.append(
                        f"Positions processed {current_positions} is significantly less than average {avg_positions:.1f}"
                    )

            if error_counts:
                error_threshold = avg_errors * 3  # 3x more errors than average
                if current_errors > error_threshold:
                    anomalies.append(
                        f"Error count {current_errors} is significantly higher than average {avg_errors:.1f}"
                    )

            # Detect if we're processing way more positions than usual
            if position_counts:
                position_threshold = avg_positions * 3  # 3x more than average
                if current_positions > position_threshold:
                    anomalies.append(
                        f"Positions processed {current_positions} is significantly more than average {avg_positions:.1f}"
                    )

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            anomalies.append(f"Anomaly detection error: {str(e)}")

        return anomalies

    async def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive system health report.

        Returns:
            Comprehensive health report
        """
        try:
            # Get metrics summary for different time windows
            summary_1h = self.metrics_collector.get_metrics_summary(60)  # 1 hour
            summary_24h = self.metrics_collector.get_metrics_summary(1440)  # 24 hours

            # Get current health status
            health_status = self.metrics_collector.get_health_status()

            # Generate report
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'system_status': health_status,
                'metrics_summary_1h': summary_1h,
                'metrics_summary_24h': summary_24h,
                'active_alerts': list(self.metrics_collector.active_alerts.keys()),
                'alert_rules': [
                    {
                        'name': rule.name,
                        'condition': rule.condition,
                        'threshold': rule.threshold,
                        'severity': rule.severity,
                    }
                    for rule in self.metrics_collector.alert_rules
                ],
                'recommendations': self._generate_recommendations(health_status, summary_1h),
            }

            return report

        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat(),
            }

    def _generate_recommendations(self, health_status: Dict[str, Any], summary_1h: Dict[str, Any]) -> List[str]:
        """Generate system improvement recommendations."""
        recommendations = []

        try:
            status = health_status.get('status', 'unknown')
            health_score = health_status.get('health_score', 0)

            if status == 'critical':
                recommendations.append("Immediate attention required - system is in critical state")
                recommendations.append("Check for persistent errors and fix them")
                recommendations.append("Consider reducing monitoring frequency temporarily")

            elif status == 'degraded':
                recommendations.append("System performance is degraded")
                recommendations.append("Review recent errors and cycle times")
                recommendations.append("Check system resources (CPU, memory)")

            elif status == 'warning':
                recommendations.append("System is operating but with warnings")
                recommendations.append("Monitor error rates and cycle times")
                recommendations.append("Consider optimizing database queries if cycle times are high")

            if health_score < 80:
                recommendations.append("Review and optimize position processing logic")

            # Check for specific issues
            if summary_1h.get('total_errors', 0) > 10:
                recommendations.append("High error count detected - review error logs")

            cycle_time_stats = summary_1h.get('cycle_time_stats', {})
            avg_cycle_time = cycle_time_stats.get('average', 0)

            if avg_cycle_time > 30:
                recommendations.append("Cycle times are high - consider batch size optimization")

            success_rate_stats = summary_1h.get('success_rate_stats', {})
            avg_success_rate = success_rate_stats.get('average', 1.0)

            if avg_success_rate < 0.9:
                recommendations.append("Success rate is below 90% - review processing logic")

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append(f"Error generating recommendations: {str(e)}")

        return recommendations

    def add_custom_alert_rule(self, rule: AlertRule) -> None:
        """Add a custom alert rule."""
        self.metrics_collector.add_alert_rule(rule)
        logger.info(f"Added custom alert rule: {rule.name}")

    def remove_custom_alert_rule(self, rule_name: str) -> bool:
        """Remove a custom alert rule."""
        return self.metrics_collector.remove_alert_rule(rule_name)

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status."""
        return {
            'is_running': self._is_running,
            'metrics_history_size': len(self.metrics_collector.metrics_history),
            'active_alerts': len(self.metrics_collector.active_alerts),
            'alert_rules_count': len(self.metrics_collector.alert_rules),
            'last_metrics': self.metrics_collector.metrics_history[-1].timestamp.isoformat() if self.metrics_collector.metrics_history else None,
        }