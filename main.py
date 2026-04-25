# ============================================================
# 阶段 5：应用入口 main.py
# ============================================================
#
# 运行方式：
#   D:/software/miniconda/envs/13/python.exe main.py
#
# 然后打开浏览器访问：
#   http://localhost:8000/docs   ← 自动生成的接口文档（可以直接在网页上测试！）
#   http://localhost:8000/health ← 健康检查
#
# 知识点：
#   - FastAPI 是 Web 框架，负责接收 HTTP 请求，返回 HTTP 响应
#   - uvicorn 是服务器，负责监听端口、把请求交给 FastAPI 处理
#   - /docs 是 FastAPI 自动生成的 Swagger 文档页面，非常好用
# ============================================================

from fastapi import FastAPI
from src.api.book import router as book_router
from src.api.chat import router as chat_router
from src.api.homework import router as homework_router
from src.api.lesson import router as lesson_router
from src.api.plan import router as plan_router
from src.api.syllabus import router as syllabus_router
from src.api.ui import router as ui_router
from src.config import settings
from src.storage_plans import init_tables

# 启动时建表（已存在则跳过）
init_tables()

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 私教 · 学习规划 · 任务执行 Agent",
)

# 注册路由（把 chat.py 里定义的接口挂载到应用上）
app.include_router(ui_router)
app.include_router(book_router)
app.include_router(chat_router)
app.include_router(plan_router)
app.include_router(syllabus_router)
app.include_router(lesson_router)
app.include_router(homework_router)


# 健康检查接口：用来确认服务是否正常运行
@app.get("/health", summary="健康检查")
async def health():
    return {"status": "ok", "app": settings.app_name}


# 直接运行这个文件时，启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
