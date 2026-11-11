"""应用级配置依赖。"""

from fastapi import Request

from app.core.config import Settings


def get_app_settings(request: Request) -> Settings:
    """从当前应用读取配置，而不是依赖模块级单例。"""
    settings: Settings = request.app.state.settings
    return settings
