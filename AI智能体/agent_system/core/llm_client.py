"""
LLM 客户端模块
作用：封装阿里云百炼 API 的调用，支持流式输出、思考模式、多轮对话
这是整个智能体的"大脑"，所有 AI 回复都通过这里发出
"""
from openai import OpenAI
from typing import List, Dict, Generator, Optional
from config.settings import settings


class LLMClient:
    """大语言模型客户端"""

    def __init__(self):
        """初始化 OpenAI 兼容客户端（百炼 API 兼容 OpenAI 接口）"""
        self.client = OpenAI(
            api_key=settings.API_KEY,
            base_url=settings.BASE_URL,
        )
        self.model = settings.DEFAULT_MODEL
        self.temperature = settings.TEMPERATURE
        self.max_tokens = settings.MAX_TOKENS
        self.enable_thinking = settings.ENABLE_THINKING

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: Optional[bool] = None,
        model: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        发送对话请求，支持流式输出

        Args:
            messages: 消息列表，格式 [{"role": "system/user/assistant", "content": "..."}]
            stream: 是否流式输出，默认使用配置
            model: 指定模型，默认使用配置

        Yields:
            思考过程和回复内容的文本片段
        """
        use_stream = stream if stream is not None else settings.STREAM_OUTPUT
        use_model = model or self.model

        # 构建额外参数（百炼的思考模式）
        extra_body = {}
        if self.enable_thinking:
            extra_body["enable_thinking"] = True

        try:
            response = self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                extra_body=extra_body if extra_body else None,
                stream=use_stream,
            )

            if use_stream:
                # 流式输出：区分思考过程和最终回复
                is_thinking = True
                for chunk in response:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    # 思考过程（reasoning_content）
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        if is_thinking:
                            yield f"\n{'='*20} 思考过程 {'='*20}\n"
                            is_thinking = False
                        yield delta.reasoning_content

                    # 最终回复（content）
                    if hasattr(delta, "content") and delta.content:
                        if not is_thinking:
                            yield f"\n{'='*20} 最终回复 {'='*20}\n"
                            is_thinking = True  # 标记已进入回复阶段
                        yield delta.content
            else:
                # 非流式输出
                choice = response.choices[0]
                if hasattr(choice.message, "reasoning_content") and choice.message.reasoning_content:
                    yield f"\n{'='*20} 思考过程 {'='*20}\n"
                    yield choice.message.reasoning_content
                yield f"\n{'='*20} 最终回复 {'='*20}\n"
                yield choice.message.content

        except Exception as e:
            yield f"\n[API 调用错误] {type(e).__name__}: {str(e)}\n"

    def chat_non_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> str:
        """
        非流式对话，直接返回完整回复（用于工作流内部调用）

        Args:
            messages: 消息列表
            model: 指定模型

        Returns:
            完整的回复文本
        """
        use_model = model or self.model
        extra_body = {}
        if self.enable_thinking:
            extra_body["enable_thinking"] = True

        try:
            response = self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                extra_body=extra_body if extra_body else None,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[API 调用错误] {type(e).__name__}: {str(e)}"


# 全局 LLM 客户端实例
llm = LLMClient()
