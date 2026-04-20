import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Course, Material

router = APIRouter(prefix="/courses", tags=["courses"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")


class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = ""


@router.post("")
def create_course(body: CourseCreate, db: Session = Depends(get_db)):
    course = Course(name=body.name, description=body.description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return _course_dict(course)


@router.get("")
def list_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).order_by(Course.created_at.desc()).all()
    return [_course_dict(c) for c in courses]


@router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {
        **_course_dict(course),
        "materials": [_material_dict(m) for m in course.materials],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
            }
            for t in course.tasks
        ],
    }


@router.post("/{course_id}/materials")
async def upload_material(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    dest_dir = os.path.join(UPLOAD_DIR, "materials", str(course_id))
    os.makedirs(dest_dir, exist_ok=True)
    filepath = os.path.join(dest_dir, file.filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    material = Material(course_id=course_id, filename=file.filename, filepath=filepath)
    db.add(material)
    db.commit()
    db.refresh(material)
    return _material_dict(material)


@router.delete("/{course_id}/materials/{material_id}")
def delete_material(course_id: int, material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(
        Material.id == material_id, Material.course_id == course_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    if os.path.exists(material.filepath):
        os.remove(material.filepath)
    db.delete(material)
    db.commit()
    return {"ok": True}


def _course_dict(course: Course):
    return {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "created_at": course.created_at.isoformat(),
    }


def _material_dict(m: Material):
    return {
        "id": m.id,
        "course_id": m.course_id,
        "filename": m.filename,
        "created_at": m.created_at.isoformat(),
    }
