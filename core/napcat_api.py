"""NapCat HTTP API 直接调用

绕过 MaiBot 的封装，直接调用 NapCat 的 HTTP API 获取真实的 message_id
"""

import json
import traceback
from typing import Optional, Dict, Any, List

import httpx

from src.plugin_system.apis import logging_api

logger = logging_api.get_logger("music_plugin")


class NapCatAPI:
    """NapCat HTTP API 客户端"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 3000, token: str = ""):
        self.base_url = f"http://{host}:{port}"
        self.token = token
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    async def send_group_msg(self, group_id: str, message: List[Dict]) -> Optional[int]:
        """发送群消息，返回真实的 message_id
        
        Args:
            group_id: 群号
            message: OneBot 消息段列表
        
        Returns:
            message_id 或 None
        """
        path = "/send_group_msg"
        payload = {
            "group_id": group_id,
            "message": message
        }
        
        try:
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                resp = await client.post(path, json=payload, headers=self.headers)
                
                logger.debug(f"[NapCatAPI] send_group_msg 响应状态: {resp.status_code}")
                
                if resp.status_code != 200:
                    logger.warning(f"[NapCatAPI] send_group_msg 失败: {resp.status_code}")
                    return None
                
                data = resp.json()
                logger.debug(f"[NapCatAPI] send_group_msg 响应: {data}")
                
                if data.get("status") == "ok" and data.get("retcode") == 0:
                    message_id = data.get("data", {}).get("message_id")
                    if message_id:
                        logger.info(f"[NapCatAPI] 发送群消息成功，message_id: {message_id}")
                        return message_id
                
                logger.warning(f"[NapCatAPI] send_group_msg 返回错误: {data.get('message', '未知错误')}")
                return None
                
        except Exception as e:
            logger.error(f"[NapCatAPI] send_group_msg 异常: {traceback.format_exc()}")
            return None
    
    async def send_private_msg(self, user_id: str, message: List[Dict]) -> Optional[int]:
        """发送私聊消息，返回真实的 message_id
        
        Args:
            user_id: 用户 QQ 号
            message: OneBot 消息段列表
        
        Returns:
            message_id 或 None
        """
        path = "/send_private_msg"
        payload = {
            "user_id": user_id,
            "message": message
        }
        
        try:
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                resp = await client.post(path, json=payload, headers=self.headers)
                
                logger.debug(f"[NapCatAPI] send_private_msg 响应状态: {resp.status_code}")
                
                if resp.status_code != 200:
                    logger.warning(f"[NapCatAPI] send_private_msg 失败: {resp.status_code}")
                    return None
                
                data = resp.json()
                logger.debug(f"[NapCatAPI] send_private_msg 响应: {data}")
                
                if data.get("status") == "ok" and data.get("retcode") == 0:
                    message_id = data.get("data", {}).get("message_id")
                    if message_id:
                        logger.info(f"[NapCatAPI] 发送私聊消息成功，message_id: {message_id}")
                        return message_id
                
                logger.warning(f"[NapCatAPI] send_private_msg 返回错误: {data.get('message', '未知错误')}")
                return None
                
        except Exception as e:
            logger.error(f"[NapCatAPI] send_private_msg 异常: {traceback.format_exc()}")
            return None
    
    async def delete_msg(self, message_id: int) -> bool:
        """撤回消息
        
        Args:
            message_id: 消息 ID
        
        Returns:
            是否成功
        """
        path = "/delete_msg"
        payload = {"message_id": int(message_id)}
        
        try:
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                resp = await client.post(path, json=payload, headers=self.headers)
                
                if resp.status_code != 200:
                    logger.warning(f"[NapCatAPI] delete_msg 失败: {resp.status_code}")
                    return False
                
                data = resp.json()
                logger.debug(f"[NapCatAPI] delete_msg 响应: {data}")
                
                if data.get("status") == "ok" and data.get("retcode") == 0:
                    logger.info(f"[NapCatAPI] 撤回消息成功: {message_id}")
                    return True
                else:
                    logger.warning(f"[NapCatAPI] 撤回消息失败: {data.get('message', '未知错误')}")
                    return False
                
        except Exception as e:
            logger.error(f"[NapCatAPI] delete_msg 异常: {traceback.format_exc()}")
            return False
