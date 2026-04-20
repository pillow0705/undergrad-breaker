from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Task, TaskResult, Material
import agent_runner

router = APIRouter(tags=["agent"])


@router.post("/tasks/{task_id}/run")
def trigger_task(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == "running":
        raise HTTPException(status_code=409, detail="Task already running")

    task.status = "running"
    db.commit()

    background_tasks.add_task(run_task_background, task_id)
    return {"ok": True, "task_id": task_id, "status": "running"}


@router.get("/tasks/{task_id}/status")
def task_status(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task_id,
        "status": task.status,
        "has_pdf": bool(task.result and task.result.pdf_path),
    }


def run_task_background(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        task.status = "running"
        db.commit()

        materials = db.query(Material).filter(Material.course_id == task.course_id).all()
        material_paths = [m.filepath for m in materials]
        task_file_paths = [f.filepath for f in task.files]

        result = agent_runner.run_agent(
            task_id=task_id,
            course_name=task.course.name,
            material_paths=material_paths,
            task_title=task.title,
            task_description=task.description,
            task_file_paths=task_file_paths,
        )

        # Remove old result if retrying
        old_result = db.query(TaskResult).filter(TaskResult.task_id == task_id).first()
        if old_result:
            db.delete(old_result)
            db.flush()

        if result["ok"]:
            task_result = TaskResult(
                task_id=task_id,
                pdf_path=result["pdf_path"],
                latex_source=result.get("latex_source"),
            )
            task.status = "done"
        else:
            task_result = TaskResult(
                task_id=task_id,
                latex_source=result.get("latex_source"),
                error_message=result.get("error"),
            )
            task.status = "failed"

        db.add(task_result)
        db.commit()
    except Exception as e:
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = "failed"
                err_result = TaskResult(task_id=task_id, error_message=str(e))
                db.add(err_result)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
