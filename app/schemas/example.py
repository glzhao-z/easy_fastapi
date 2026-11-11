"""示例业务模块的数据模型。"""

from pydantic import BaseModel


class PingResponse(BaseModel):
    message: str
