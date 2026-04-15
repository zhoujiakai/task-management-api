"""异步通知模块（模拟邮件）。"""

import asyncio

from logger import create_logger

log = create_logger("notifications")


async def send_notification(task_id: str, title: str, status: str) -> None:
    """异步模拟发送邮件通知。

    在生产环境中，此处应连接 SMTP 服务器或消息队列。
    """
    log.info(f"Sending notification: task '{title}' ({task_id}) changed to '{status}'")
    # 模拟网络延迟
    await asyncio.sleep(0.01)
    log.info(f"Notification sent for task {task_id}")
