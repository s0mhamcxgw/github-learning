"""
配置加载模块
作用：从 .env 文件读取所有配置，提供统一的配置访问入口
为什么需要：避免在代码中硬编码 API Key 和各种参数，方便统一管理
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件（项目根目录下）
load_dotenv()


class Settings:
    """全局配置单例类"""

    # ========== 百炼 API 配置 ==========
    API_KEY: str = os.getenv("ALIBABA_CLOUD_API_KEY", "")
    BASE_URL: str = os.getenv(
        "ALIBABA_CLOUD_BASE_URL",
        "https://ws-q3ed5buioquiomzd.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
    )
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "qwen3.8-max")

    # ========== 智能体配置 ==========
    AGENT_NAME: str = os.getenv("AGENT_NAME", "贵财大数据专硕全能智能体")
    AGENT_VERSION: str = os.getenv("AGENT_VERSION", "2.0")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    STREAM_OUTPUT: bool = os.getenv("STREAM_OUTPUT", "true").lower() == "true"
    ENABLE_THINKING: bool = os.getenv("ENABLE_THINKING", "true").lower() == "true"

    # ========== 路径配置 ==========
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SYSTEM_PROMPT_DIR: str = os.path.join(BASE_DIR, "config", "prompts")
    MEMORY_DIR: str = os.path.join(BASE_DIR, "data", "memory")
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "outputs")  # 智能体产出文件目录

    @classmethod
    def validate(cls) -> bool:
        """配置校验：检查必要配置是否齐全"""
        if not cls.API_KEY:
            print("[错误] 未配置 ALIBABA_CLOUD_API_KEY，请在 .env 文件中设置")
            return False
        if not cls.BASE_URL:
            print("[错误] 未配置 BASE_URL")
            return False
        # 确保目录存在
        for d in [cls.MEMORY_DIR, cls.LOG_DIR, cls.SYSTEM_PROMPT_DIR, cls.OUTPUT_DIR]:
            os.makedirs(d, exist_ok=True)
        print(f"[配置] {cls.AGENT_NAME} v{cls.AGENT_VERSION} 加载完成")
        print(f"[配置] 默认模型: {cls.DEFAULT_MODEL}")
        print(f"[配置] 思考模式: {'开启' if cls.ENABLE_THINKING else '关闭'}")
        return True


# 全局配置实例
settings = Settings()
