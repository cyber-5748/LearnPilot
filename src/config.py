"""全局配置：从 .env 文件读取所有设置。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM 配置（对应 .env 里的变量名）
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = "deepseek-v3.2"

    # Tavily 搜索配置
    tavily_api_key: str = ""

    # 应用信息
    app_name: str = "LearnPilot"
    app_version: str = "0.1.0"


# 全局单例：其他文件直接导入这个对象使用
settings = Settings()
