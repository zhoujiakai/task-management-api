"""Async notification module (simulated email)."""

import asyncio

from logger import create_logger

log = create_logger("notifications")


async def send_notification(task_id: str, title: str, status: str) -> None:
    """Simulate sending an email notification asynchronously.

    In production, this would connect to an SMTP server or message queue.
    """
    log.info(f"Sending notification: task '{title}' ({task_id}) changed to '{status}'")
    # Simulate network latency
    await asyncio.sleep(0.01)
    log.info(f"Notification sent for task {task_id}")
