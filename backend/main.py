from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models  # ensure all models are registered
from routers import courses, tasks, agent

Base.metadata.create_all(bind=engine)

app = FastAPI(title="本科破局系统 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(tasks.router)
app.include_router(agent.router)


@app.get("/health")
def health():
    return {"ok": True}
