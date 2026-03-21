"""选歌列表撤回管理器

使用 NapCatAPI 直接调用 HTTP 接口
"""

import asyncio
from typing import Optional, Dict
from dataclasses import dataclass

from src.plugin_system.apis import logging_api

from .napcat_api import NapCatAPI

logger = logging_api.get_logger("music_plugin")


@dataclass
class RecallTask:
    """撤回任务数据"""
    task: asyncio.Task
    selection_key: str
    message_id: int
    chat_id: str


class SelectionRecallManager:
    """选歌列表撤回管理器"""
    
    def __init__(self):
        self._pending_recalls: Dict[str, RecallTask] = {}
    
    def create_recall_task(
        self,
        selection_key: str,
        message_id: int,
        chat_id: str,
        timeout_seconds: int,
        napcat_host: str,
        napcat_port: int,
        napcat_token: str = "",
    ) -> Optional[asyncio.Task]:
        """创建选歌列表的超时撤回任务"""
        if timeout_seconds <= 0 or not message_id:
            return None
        
        # 取消已存在的任务
        self._cancel_task_only(selection_key)
        
        async def _recall_task():
            try:
                # 等待超时
                await asyncio.sleep(timeout_seconds)
                
                # 创建 NapCatAPI 实例
                napcat = NapCatAPI(napcat_host, napcat_port, napcat_token)
                
                # 执行撤回
                success = await napcat.delete_msg(message_id)
                
                if success:
                    logger.info(f"[RecallManager] 选歌列表已撤回(超时): {message_id}")
                else:
                    logger.warning(f"[RecallManager] 选歌列表撤回失败(超时): {message_id}")
                
            except asyncio.CancelledError:
                logger.debug(f"[RecallManager] 超时撤回任务被取消: {selection_key}")
            except Exception as e:
                logger.error(f"[RecallManager] 超时撤回任务异常: {e}")
            finally:
                self._pending_recalls.pop(selection_key, None)
        
        task = asyncio.create_task(_recall_task())
        
        self._pending_recalls[selection_key] = RecallTask(
            task=task,
            selection_key=selection_key,
            message_id=message_id,
            chat_id=chat_id,
        )
        
        logger.debug(
            f"[RecallManager] 已创建超时撤回任务: {selection_key}, "
            f"message_id={message_id}, timeout={timeout_seconds}s"
        )
        return task
    
    async def recall_immediately(
        self,
        selection_key: str,
        napcat_host: str,
        napcat_port: int,
        napcat_token: str = "",
        reason: str = "",
        send_timestamp: float = 0,
    ) -> bool:
        """立即撤回选歌列表"""
        recall_task = self._pending_recalls.pop(selection_key, None)
        if not recall_task:
            logger.debug(f"[RecallManager] 无待撤回任务: {selection_key}")
            return False
        
        # 检查是否超过2分钟（QQ限制）
        if send_timestamp > 0:
            elapsed = asyncio.get_event_loop().time() - send_timestamp
            if elapsed > 120:
                logger.warning(f"[RecallManager] 消息已发送 {elapsed:.1f} 秒，超过2分钟限制，无法撤回")
                return False
            logger.debug(f"[RecallManager] 消息已发送 {elapsed:.1f} 秒，在2分钟限制内")
        
        # 取消超时任务
        if not recall_task.task.done():
            recall_task.task.cancel()
            try:
                await recall_task.task
            except asyncio.CancelledError:
                pass
        
        # 立即执行撤回
        try:
            napcat = NapCatAPI(napcat_host, napcat_port, napcat_token)
            success = await napcat.delete_msg(recall_task.message_id)
            
            reason_str = f" ({reason})" if reason else ""
            if success:
                logger.info(f"[RecallManager] 选歌列表已撤回{reason_str}: {recall_task.message_id}")
            else:
                logger.warning(f"[RecallManager] 选歌列表撤回失败{reason_str}: {recall_task.message_id}")
            
            return success
        except Exception as e:
            logger.error(f"[RecallManager] 立即撤回失败: {e}")
            return False
    
    def _cancel_task_only(self, selection_key: str) -> bool:
        """仅取消任务（不执行撤回），内部使用"""
        recall_task = self._pending_recalls.pop(selection_key, None)
        if recall_task and not recall_task.task.done():
            recall_task.task.cancel()
            return True
        return False
    
    def cleanup(self):
        """清理所有任务（插件卸载时调用）"""
        for task in self._pending_recalls.values():
            if not task.task.done():
                task.task.cancel()
        self._pending_recalls.clear()
        logger.debug("[RecallManager] 已清理所有撤回任务")


# 全局单例
recall_manager = SelectionRecallManager()
