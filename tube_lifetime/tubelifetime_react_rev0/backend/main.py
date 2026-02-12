from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import asyncio
from engine import TestEngine

app = FastAPI()

# 全局变量，稍后在 startup 中初始化
engine: Optional[TestEngine] = None
# 用于存储 WebSocket 连接的管理器
manager = None

# --- WebSocket 连接管理器 ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, type_: str, payload):
        # 广播消息并清理断开的连接
        message = {"type": type_, "payload": payload}
        to_remove = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                to_remove.append(connection)
        
        for conn in to_remove:
            self.disconnect(conn)

manager = ConnectionManager()

# --- 桥接 Engine 回调到 Async ---
def sync_broadcast(type_, payload):
    # 这是给 Engine 线程调用的同步函数
    # 它会将任务“扔”回主线程的事件循环执行
    loop = getattr(app.state, "loop", None)
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast_json(type_, payload), loop)

@app.on_event("startup")
async def on_startup():
    global engine
    # 1. 捕获主线程的事件循环 (Critical Fix)
    app.state.loop = asyncio.get_running_loop()
    # 2. 现在初始化 Engine 是安全的
    engine = TestEngine(broadcast_func=sync_broadcast)
    print("✅ Engine initialized and monitor thread started.")

# --- 数据模型 ---
class StepItem(BaseModel):
    id: Optional[int] = 0
    type: str
    pos: float = 0.0
    speed: float = 10.0
    force: float = 30.0
    time: float = 0.0

class RunRequest(BaseModel):
    sequence: List[StepItem]
    cycles: int

# --- API 接口 ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/start")
async def start_test(req: RunRequest):
    if not engine: return {"status": "error", "msg": "Engine not ready"}
    seq_data = [s.dict() for s in req.sequence]
    engine.start_sequence(seq_data, req.cycles)
    return {"status": "ok"}

@app.post("/api/pause")
async def pause_test():
    if engine: engine.pause_resume()
    return {"status": "ok"}

@app.post("/api/stop")
async def stop_test():
    if engine: engine.stop()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)