import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Task, TaskFile, TaskResult, Course

router = APIRouter(tags=["tasks"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")


@router.post("/courses/{course_id}/tasks")
async def create_task(
    course_id: int,
    title: str = Form(...),
    description: str = Form(""),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    task = Task(course_id=course_id, title=title, description=description, status="pending")
    db.add(task)
    db.commit()
    db.refresh(task)

    if files:
        dest_dir = os.path.join(UPLOAD_DIR, "tasks", str(task.id))
        os.makedirs(dest_dir, exist_ok=True)
        for f in files:
            if not f.filename:
                continue
            filepath = os.path.join(dest_dir, f.filename)
            with open(filepath, "wb") as out:
                shutil.copyfileobj(f.file, out)
            tf = TaskFile(task_id=task.id, filename=f.filename, filepath=filepath)
            db.add(tf)
        db.commit()
        db.refresh(task)

    return _task_dict(task)


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        **_task_dict(task),
        "files": [{"id": f.id, "filename": f.filename} for f in task.files],
        "result": _result_dict(task.result) if task.result else None,
    }


@router.get("/tasks/{task_id}/result/pdf")
def get_task_pdf(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.result or not task.result.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not available")
    if not os.path.exists(task.result.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file missing")
    return FileResponse(task.result.pdf_path, media_type="application/pdf")


@router.post("/tasks/{task_id}/retry")
async def retry_task(
    task_id: int,
    feedback: str = Form(""),
    db: Session = Depends(get_db),
):
    from routers.agent import run_task_background
    from fastapi import BackgroundTasks

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == "running":
        raise HTTPException(status_code=409, detail="Task already running")

    # Append feedback to description for the retry
    if feedback:
        task.description = task.description + f"\n\n[重做反馈] {feedback}"
    task.status = "pending"

    # Clear old result
    if task.result:
        db.delete(task.result)

    db.commit()
    db.refresh(task)

    bg = BackgroundTasks()
    bg.add_task(run_task_background, task_id)
    # Trigger immediately without waiting
    import asyncio
    asyncio.create_task(_run_bg(task_id))

    return {"ok": True, "task_id": task_id}


async def _run_bg(task_id: int):
    from routers.agent import run_task_background
    await asyncio.get_event_loop().run_in_executor(None, run_task_background, task_id)


def _task_dict(task: Task):
    return {
        "id": task.id,
        "course_id": task.course_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
    }


def _result_dict(result: TaskResult):
    if not result:
        return None
    return {
        "id": result.id,
        "pdf_path": result.pdf_path,
        "latex_source": result.latex_source,
        "error_message": result.error_message,
        "created_at": result.created_at.isoformat(),
    }
