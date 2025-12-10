"""
阿里云DashScope API客户端
用于调用阿里云的兼容OpenAI接口的模型服务
"""

import requests
import json
from typing import Optional, Dict, List, Any
from common.logging_system import setup_logger

logger = setup_logger(__name__)


class AliyunAPIClient:
    """阿里云API客户端类"""
    
    def __init__(self, api_key: str, model: str = "qwen-plus"):
        """
        初始化阿里云API客户端
        
        Args:
            api_key: 阿里云API密钥
            model: 使用的模型名称，默认qwen-plus
        """
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用阿里云聊天补全API
        
        Args:
            messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            temperature: 温度参数，控制随机性 (0-2)
            max_tokens: 最大生成token数
            top_p: nucleus采样参数
            stream: 是否使用流式输出
            **kwargs: 其他参数
            
        Returns:
            API响应字典
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        # 添加其他自定义参数
        payload.update(kwargs)
        
        try:
            logger.info(f"调用阿里云API，模型: {self.model}")
            logger.debug(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
            
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info("阿里云API调用成功")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"阿里云API调用失败: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"响应内容: {e.response.text}")
            raise Exception(f"阿里云API调用失败: {str(e)}")
    
    def get_response_text(self, response: Dict[str, Any]) -> str:
        """
        从API响应中提取文本内容
        
        Args:
            response: API响应字典
            
        Returns:
            提取的文本内容
        """
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"解析响应失败: {str(e)}")
            logger.error(f"响应内容: {json.dumps(response, ensure_ascii=False)}")
            raise Exception(f"解析阿里云API响应失败: {str(e)}")
    
    def simple_chat(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        简单的聊天接口，直接返回文本响应
        
        Args:
            user_message: 用户消息
            system_message: 系统消息（可选）
            temperature: 温度参数
            max_tokens: 最大生成token数
            
        Returns:
            AI回复的文本内容
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        messages.append({"role": "user", "content": user_message})
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return self.get_response_text(response)
    
    def chat_with_history(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        带历史记录的聊天接口
        
        Args:
            user_message: 用户消息
            history: 历史消息列表
            system_message: 系统消息（可选）
            temperature: 温度参数
            max_tokens: 最大生成token数
            
        Returns:
            AI回复的文本内容
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # 添加历史消息
        messages.extend(history)
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return self.get_response_text(response)

