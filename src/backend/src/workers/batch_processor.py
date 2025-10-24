"""
Batch Processing Module - Concurrent Position Processing Optimization.

This module provides efficient batch processing capabilities for handling
multiple positions concurrently with proper error handling and retry logic.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
import random

from ..db.models import Position

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Handles efficient batch processing of positions with concurrency control."""

    @staticmethod
    async def process_positions_batch(
        positions: List[Position],
        credentials_map: Dict[str, Dict[str, str]],
        max_concurrent: int = 10
    ) -> List[Dict[str, Any]]:
        """Process multiple positions concurrently for efficiency.

        Args:
            positions: List of positions to process
            credentials_map: Map of user addresses to their credentials
            max_concurrent: Maximum concurrent operations

        Returns:
            List of processing results
        """
        if not positions:
            return []

        logger.info(f"Processing batch of {len(positions)} positions with max concurrency: {max_concurrent}")

        # Group positions by user for efficient credential usage
        positions_by_user = BatchProcessor._group_positions_by_user(positions)

        # Process each user's positions
        all_results = []

        for user_address, user_positions in positions_by_user.items():
            if user_address not in credentials_map:
                logger.warning(f"No credentials found for user {user_address}")
                # Create error results for all positions of this user
                for position in user_positions:
                    all_results.append({
                        'position_id': position.id,
                        'success': False,
                        'error': f"No credentials found for user {user_address}",
                        'user_address': user_address,
                    })
                continue

            credentials = credentials_map[user_address]

            # Process this user's positions in batches
            user_results = await BatchProcessor._process_user_batch(
                user_positions, credentials, max_concurrent
            )

            all_results.extend(user_results)

        logger.info(f"Batch processing completed: {len(all_results)} results")
        return all_results

    @staticmethod
    def _group_positions_by_user(positions: List[Position]) -> Dict[str, List[Position]]:
        """Group positions by user address."""
        groups = {}
        for position in positions:
            user_address = position.user_address
            if user_address not in groups:
                groups[user_address] = []
            groups[user_address].append(position)
        return groups

    @staticmethod
    async def _process_user_batch(
        positions: List[Position],
        credentials: Dict[str, str],
        max_concurrent: int
    ) -> List[Dict[str, Any]]:
        """Process positions for a single user with concurrency control."""
        if not positions:
            return []

        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(position: Position) -> Dict[str, Any]:
            async with semaphore:
                try:
                    # This is where you'd call the actual position processing logic
                    # For now, we'll simulate it
                    result = await BatchProcessor._simulate_position_processing(position, credentials)

                    if result['success']:
                        logger.debug(f"Successfully processed position {position.id}")
                    else:
                        logger.warning(f"Failed to process position {position.id}: {result.get('error')}")

                    return result

                except Exception as e:
                    logger.error(f"Error processing position {position.id}: {e}")
                    return {
                        'position_id': position.id,
                        'success': False,
                        'error': str(e),
                        'user_address': position.user_address,
                    }

        # Process all positions concurrently
        tasks = [process_with_semaphore(position) for position in positions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions from gather
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                # This shouldn't happen since we handle exceptions above, but just in case
                logger.error(f"Unexpected error in batch processing: {result}")
                continue
            processed_results.append(result)

        return processed_results

    @staticmethod
    async def _simulate_position_processing(position: Position, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Simulate position processing (replace with actual logic)."""
        # Simulate processing time
        processing_time = random.uniform(0.1, 0.5)
        await asyncio.sleep(processing_time)

        # Simulate occasional failures
        if random.random() < 0.05:  # 5% failure rate
            return {
                'position_id': position.id,
                'success': False,
                'error': 'Simulated processing failure',
                'user_address': position.user_address,
            }

        return {
            'position_id': position.id,
            'success': True,
            'processing_time': processing_time,
            'user_address': position.user_address,
            'symbol': position.symbol,
            'status': position.status,
        }

    @staticmethod
    async def handle_partial_failures(
        results: List[Dict[str, Any]],
        original_positions: List[Position]
    ) -> List[Position]:
        """Handle cases where some positions fail processing.

        Args:
            results: Processing results
            original_positions: Original positions that were processed

        Returns:
            List of positions that failed processing
        """
        failed_positions = []

        # Create a map of position_id to result for quick lookup
        results_map = {result['position_id']: result for result in results}

        for position in original_positions:
            position_id = position.id
            if position_id in results_map:
                result = results_map[position_id]
                if not result['success']:
                    failed_positions.append(position)
            else:
                # Position not in results at all
                failed_positions.append(position)

        logger.info(f"Found {len(failed_positions)} failed positions out of {len(original_positions)}")

        return failed_positions

    @staticmethod
    async def retry_failed_positions(
        failed_positions: List[Position],
        retry_count: int = 3,
        backoff_seconds: int = 60
    ) -> List[Dict[str, Any]]:
        """Retry failed position processing with exponential backoff.

        Args:
            failed_positions: Positions that failed initial processing
            retry_count: Number of retry attempts
            backoff_seconds: Base backoff time in seconds

        Returns:
            Retry results
        """
        if not failed_positions:
            return []

        logger.info(f"Retrying {len(failed_positions)} failed positions with {retry_count} attempts")

        retry_results = []

        for attempt in range(retry_count):
            if not failed_positions:
                break

            logger.info(f"Retry attempt {attempt + 1}/{retry_count} for {len(failed_positions)} positions")

            # Exponential backoff
            if attempt > 0:
                sleep_time = backoff_seconds * (2 ** (attempt - 1))
                logger.info(f"Waiting {sleep_time}s before retry attempt {attempt + 1}")
                await asyncio.sleep(sleep_time)

            # Process remaining failed positions
            # In a real implementation, you'd need credentials for these positions
            # For now, we'll simulate the retry
            current_attempt_results = []

            for position in failed_positions[:]:  # Copy the list to avoid modification during iteration
                try:
                    # Simulate retry processing
                    retry_result = await BatchProcessor._simulate_retry_processing(position, attempt)

                    current_attempt_results.append(retry_result)

                    if retry_result['success']:
                        # Remove from failed positions if successful
                        failed_positions.remove(position)
                        logger.debug(f"Position {position.id} succeeded on retry attempt {attempt + 1}")

                except Exception as e:
                    logger.error(f"Retry attempt {attempt + 1} failed for position {position.id}: {e}")

            retry_results.extend(current_attempt_results)

        # Mark remaining failed positions as permanent failures
        for position in failed_positions:
            retry_results.append({
                'position_id': position.id,
                'success': False,
                'error': f'Failed after {retry_count} retry attempts',
                'user_address': position.user_address,
                'permanent_failure': True,
            })

        logger.info(f"Retry process completed. {len(failed_positions)} positions still failed")
        return retry_results

    @staticmethod
    async def _simulate_retry_processing(position: Position, attempt: int) -> Dict[str, Any]:
        """Simulate retry processing with decreasing failure probability."""
        # Simulate processing time
        processing_time = random.uniform(0.2, 0.8)
        await asyncio.sleep(processing_time)

        # Higher success probability on retries
        base_success_rate = 0.7  # 70% base success rate
        attempt_bonus = attempt * 0.1  # 10% bonus per retry attempt
        success_rate = min(base_success_rate + attempt_bonus, 0.95)  # Cap at 95%

        if random.random() < success_rate:
            return {
                'position_id': position.id,
                'success': True,
                'retry_attempt': attempt + 1,
                'processing_time': processing_time,
                'user_address': position.user_address,
            }
        else:
            return {
                'position_id': position.id,
                'success': False,
                'retry_attempt': attempt + 1,
                'error': f'Failed on retry attempt {attempt + 1}',
                'processing_time': processing_time,
                'user_address': position.user_address,
            }

    @staticmethod
    async def process_with_circuit_breaker(
        positions: List[Position],
        credentials_map: Dict[str, Dict[str, str]],
        failure_threshold: float = 0.5,
        recovery_timeout: int = 300
    ) -> List[Dict[str, Any]]:
        """Process positions with circuit breaker pattern for fault tolerance.

        Args:
            positions: Positions to process
            credentials_map: User credentials
            failure_threshold: Failure rate threshold to open circuit (0.5 = 50%)
            recovery_timeout: Seconds to wait before trying again

        Returns:
            Processing results
        """
        circuit_breaker = {
            'failures': 0,
            'total_requests': 0,
            'state': 'CLOSED',  # CLOSED, OPEN, HALF_OPEN
            'last_failure_time': None
        }

        def is_circuit_open() -> bool:
            """Check if circuit breaker is open."""
            if circuit_breaker['state'] == 'OPEN':
                if circuit_breaker['last_failure_time']:
                    time_since_failure = datetime.utcnow() - circuit_breaker['last_failure_time']
                    if time_since_failure.total_seconds() > recovery_timeout:
                        circuit_breaker['state'] = 'HALF_OPEN'
                        logger.info("Circuit breaker moved to HALF_OPEN state")
                        return False
                return True
            return False

        def record_success():
            """Record a successful operation."""
            circuit_breaker['total_requests'] += 1
            if circuit_breaker['state'] == 'HALF_OPEN':
                circuit_breaker['state'] = 'CLOSED'
                circuit_breaker['failures'] = 0
                logger.info("Circuit breaker reset to CLOSED state")

        def record_failure():
            """Record a failed operation."""
            circuit_breaker['failures'] += 1
            circuit_breaker['total_requests'] += 1
            circuit_breaker['last_failure_time'] = datetime.utcnow()

            failure_rate = circuit_breaker['failures'] / circuit_breaker['total_requests']

            if failure_rate >= failure_threshold:
                circuit_breaker['state'] = 'OPEN'
                logger.warning(f"Circuit breaker opened due to {failure_rate:.2%} failure rate")

        # Process positions with circuit breaker
        results = []

        for position in positions:
            if is_circuit_open():
                # Circuit is open, fail fast
                results.append({
                    'position_id': position.id,
                    'success': False,
                    'error': 'Circuit breaker is OPEN',
                    'user_address': position.user_address,
                })
                continue

            try:
                # Process the position (simulate)
                result = await BatchProcessor._simulate_position_processing(
                    position, credentials_map.get(position.user_address, {})
                )

                if result['success']:
                    record_success()
                else:
                    record_failure()

                results.append(result)

            except Exception as e:
                record_failure()
                results.append({
                    'position_id': position.id,
                    'success': False,
                    'error': str(e),
                    'user_address': position.user_address,
                })

        return results

    @staticmethod
    async def process_with_timeout(
        positions: List[Position],
        credentials_map: Dict[str, Dict[str, str]],
        timeout_seconds: int = 30
    ) -> List[Dict[str, Any]]:
        """Process positions with individual timeouts.

        Args:
            positions: Positions to process
            credentials_map: User credentials
            timeout_seconds: Timeout per position

        Returns:
            Processing results
        """
        async def process_with_timeout_single(position: Position) -> Dict[str, Any]:
            """Process a single position with timeout."""
            try:
                # Create a task for position processing
                task = asyncio.create_task(
                    BatchProcessor._simulate_position_processing(
                        position, credentials_map.get(position.user_address, {})
                    )
                )

                # Wait for completion or timeout
                result = await asyncio.wait_for(task, timeout=timeout_seconds)

                return result

            except asyncio.TimeoutError:
                return {
                    'position_id': position.id,
                    'success': False,
                    'error': f'Processing timeout after {timeout_seconds}s',
                    'user_address': position.user_address,
                }
            except Exception as e:
                return {
                    'position_id': position.id,
                    'success': False,
                    'error': str(e),
                    'user_address': position.user_address,
                }

        # Process all positions with individual timeouts
        tasks = [process_with_timeout_single(position) for position in positions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions from gather
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                # This shouldn't happen with the exception handling above
                logger.error(f"Unexpected error in timeout processing: {result}")
                continue
            processed_results.append(result)

        return processed_results

    @staticmethod
    async def adaptive_batch_sizing(
        positions: List[Position],
        credentials_map: Dict[str, Dict[str, str]],
        initial_batch_size: int = 5,
        max_batch_size: int = 20,
        min_batch_size: int = 1,
        adaptation_rate: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Process positions with adaptive batch sizing based on performance.

        Args:
            positions: Positions to process
            credentials_map: User credentials
            initial_batch_size: Starting batch size
            max_batch_size: Maximum batch size
            min_batch_size: Minimum batch size
            adaptation_rate: How quickly to adapt batch size (0.1 = 10%)

        Returns:
            Processing results
        """
        results = []
        current_batch_size = initial_batch_size

        # Performance tracking
        performance_history = []

        for i in range(0, len(positions), current_batch_size):
            batch = positions[i:i + current_batch_size]

            # Record start time
            batch_start_time = datetime.utcnow()

            # Process batch
            batch_results = await BatchProcessor.process_positions_batch(
                batch, credentials_map, max_concurrent=current_batch_size
            )

            # Calculate batch performance
            batch_end_time = datetime.utcnow()
            batch_duration = (batch_end_time - batch_start_time).total_seconds()

            successful_operations = sum(1 for result in batch_results if result['success'])
            batch_success_rate = successful_operations / len(batch_results) if batch_results else 0

            # Record performance
            performance_history.append({
                'batch_size': current_batch_size,
                'duration': batch_duration,
                'success_rate': batch_success_rate,
                'operations_per_second': len(batch_results) / batch_duration if batch_duration > 0 else 0
            })

            # Adapt batch size based on performance
            if len(performance_history) >= 3:  # Need some history for adaptation
                recent_performance = performance_history[-3:]

                # Calculate average success rate and speed
                avg_success_rate = sum(p['success_rate'] for p in recent_performance) / len(recent_performance)
                avg_speed = sum(p['operations_per_second'] for p in recent_performance) / len(recent_performance)

                # Adapt batch size
                if avg_success_rate > 0.9 and avg_speed > 1.0:  # Good performance
                    new_batch_size = min(current_batch_size + 1, max_batch_size)
                elif avg_success_rate < 0.7 or avg_speed < 0.5:  # Poor performance
                    new_batch_size = max(current_batch_size - 1, min_batch_size)
                else:
                    new_batch_size = current_batch_size

                # Smooth the adaptation
                current_batch_size = int(current_batch_size * (1 - adaptation_rate) + new_batch_size * adaptation_rate)

                logger.debug(f"Adapted batch size from {new_batch_size} to {current_batch_size}")

            results.extend(batch_results)

        logger.info(f"Adaptive batch processing completed with final batch size: {current_batch_size}")
        return results