from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from study_plans import models, schemas
from auth.models import Student
from auth.router import get_current_student

router = APIRouter()

@router.get("/api/student/me/study-plan", tags=["Student Candidate"])
def get_my_study_plan(db: Session = Depends(get_db), current_student: Student = Depends(get_current_student)):
    if not current_student.program_id:
        return []

    program = db.query(models.Program).filter(models.Program.id == current_student.program_id).first()
    if not program:
        return []

    # Get all courses for this program's specializations
    result = []
    
    # We also need to map progress status IDs to readable statuses
    status_map = {s.id: s.name.lower().replace(" ", "-") for s in db.query(models.ProgressStatus).all()}
    
    for spec in program.specializations:
        for course in spec.courses:
            # Find progress for this student and this course
            progress_record = db.query(models.CourseProgress).filter(
                models.CourseProgress.student_id == current_student.id,
                models.CourseProgress.course_id == course.id
            ).first()

            progress_val = progress_record.progress if progress_record else 0
            
            # Use 'upcoming' as default if no record exists
            status_val = "upcoming"
            if progress_record and progress_record.progress_status in status_map:
                status_val = status_map[progress_record.progress_status]
                
            result.append({
                "code": course.code,
                "title": course.name,
                "subject": spec.name,
                "status": status_val,
                "progress": progress_val
            })
            
    return result

@router.get("/api/student/me/course/{course_code}", response_model=schemas.CourseDetailOut, tags=["Student Candidate"])
def get_my_course_details(course_code: str, db: Session = Depends(get_db), current_student: Student = Depends(get_current_student)):
    course = db.query(models.Course).filter(models.Course.code == course_code).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    status_map = {s.id: s.name.lower().replace(" ", "-") for s in db.query(models.ProgressStatus).all()}
    progress_record = db.query(models.CourseProgress).filter(
        models.CourseProgress.student_id == current_student.id,
        models.CourseProgress.course_id == course.id
    ).first()

    progress_val = progress_record.progress if progress_record else 0
    status_val = "upcoming"
    if progress_record and progress_record.progress_status in status_map:
        status_val = status_map[progress_record.progress_status]

    # Fetch topics and completion status
    topics_with_completion = []
    for topic in course.topics:
        completion = db.query(models.IsComplete).filter(
            models.IsComplete.student_id == current_student.id,
            models.IsComplete.topic_id == topic.id
        ).first()
        is_completed = completion.status if completion else False
        topics_with_completion.append({
            "id": topic.id,
            "name": topic.name,
            "is_completed": is_completed
        })
        
    return {
        "id": course.id,
        "name": course.name,
        "code": course.code,
        "is_active": course.is_active,
        "specialization_id": course.specialization_id,
        "subject": course.specialization.name if course.specialization else "Unknown",
        "progress": progress_val,
        "status": status_val,
        "topics": topics_with_completion
    }

@router.post("/api/student/me/topic/{topic_id}/toggle", tags=["Student Candidate"])
def toggle_topic_completion(topic_id: int, db: Session = Depends(get_db), current_student: Student = Depends(get_current_student)):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    completion = db.query(models.IsComplete).filter(
        models.IsComplete.student_id == current_student.id,
        models.IsComplete.topic_id == topic_id
    ).first()
    
    if completion:
        completion.status = not completion.status
    else:
        completion = models.IsComplete(
            student_id=current_student.id,
            topic_id=topic_id,
            status=True
        )
        db.add(completion)
        
    db.commit()
    
    # Recalculate CourseProgress
    course = topic.course
    total_topics = len(course.topics)
    completed_topics = 0
    
    if total_topics > 0:
        for t in course.topics:
            comp = db.query(models.IsComplete).filter(
                models.IsComplete.student_id == current_student.id,
                models.IsComplete.topic_id == t.id
            ).first()
            if comp and comp.status:
                completed_topics += 1
                
        new_progress = int((completed_topics / total_topics) * 100)
    else:
        new_progress = 0
        
    progress_record = db.query(models.CourseProgress).filter(
        models.CourseProgress.student_id == current_student.id,
        models.CourseProgress.course_id == course.id
    ).first()
    
    # Determine new status based on progress
    statuses = {s.name.lower().replace(" ", "-"): s.id for s in db.query(models.ProgressStatus).all()}
    
    if new_progress == 100:
        new_status_id = statuses.get("completed", statuses.get("complete"))
    elif new_progress > 0:
        new_status_id = statuses.get("in-progress")
    else:
        new_status_id = statuses.get("upcoming")
        
    if progress_record:
        progress_record.progress = new_progress
        if new_status_id:
            progress_record.progress_status = new_status_id
    else:
        if not new_status_id:
            # Fallback if statuses aren't seeded
            new_status_id = 1
        progress_record = models.CourseProgress(
            student_id=current_student.id,
            course_id=course.id,
            progress=new_progress,
            progress_status=new_status_id
        )
        db.add(progress_record)
        
    db.commit()
    
    return {"message": "Topic completion toggled", "is_completed": completion.status, "new_progress": new_progress}

# --- Program ---
@router.post("/programs/", response_model=schemas.ProgramOut, tags=["Programs"])
def create_program(program: schemas.ProgramCreate, db: Session = Depends(get_db)):
    db_program = models.Program(**program.model_dump())
    db.add(db_program)
    db.commit()
    db.refresh(db_program)
    return db_program

@router.get("/programs/", response_model=List[schemas.ProgramOut], tags=["Programs"])
def read_programs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    programs = db.query(models.Program).offset(skip).limit(limit).all()
    return programs

@router.get("/programs/{program_id}", response_model=schemas.ProgramOut, tags=["Programs"])
def read_program(program_id: int, db: Session = Depends(get_db)):
    program = db.query(models.Program).filter(models.Program.id == program_id).first()
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    return program

@router.put("/programs/{program_id}", response_model=schemas.ProgramOut, tags=["Programs"])
def update_program(program_id: int, program: schemas.ProgramCreate, db: Session = Depends(get_db)):
    db_program = db.query(models.Program).filter(models.Program.id == program_id).first()
    if db_program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    
    for key, value in program.model_dump().items():
        setattr(db_program, key, value)
    db.commit()
    db.refresh(db_program)
    return db_program

@router.delete("/programs/{program_id}", tags=["Programs"])
def delete_program(program_id: int, db: Session = Depends(get_db)):
    db_program = db.query(models.Program).filter(models.Program.id == program_id).first()
    if db_program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    db.delete(db_program)
    db.commit()
    return {"message": "Program deleted successfully"}

# --- Specialization ---
@router.post("/specializations/", response_model=schemas.SpecializationOut, tags=["Specializations"])
def create_specialization(specialization: schemas.SpecializationCreate, db: Session = Depends(get_db)):
    db_specialization = models.Specialization(**specialization.model_dump())
    db.add(db_specialization)
    db.commit()
    db.refresh(db_specialization)
    return db_specialization

@router.get("/specializations/", response_model=List[schemas.SpecializationOut], tags=["Specializations"])
def read_specializations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    specializations = db.query(models.Specialization).offset(skip).limit(limit).all()
    return specializations

@router.get("/specializations/{specialization_id}", response_model=schemas.SpecializationOut, tags=["Specializations"])
def read_specialization(specialization_id: int, db: Session = Depends(get_db)):
    specialization = db.query(models.Specialization).filter(models.Specialization.id == specialization_id).first()
    if specialization is None:
        raise HTTPException(status_code=404, detail="Specialization not found")
    return specialization

@router.put("/specializations/{specialization_id}", response_model=schemas.SpecializationOut, tags=["Specializations"])
def update_specialization(specialization_id: int, specialization: schemas.SpecializationCreate, db: Session = Depends(get_db)):
    db_specialization = db.query(models.Specialization).filter(models.Specialization.id == specialization_id).first()
    if db_specialization is None:
        raise HTTPException(status_code=404, detail="Specialization not found")
    
    for key, value in specialization.model_dump().items():
        setattr(db_specialization, key, value)
    db.commit()
    db.refresh(db_specialization)
    return db_specialization

@router.delete("/specializations/{specialization_id}", tags=["Specializations"])
def delete_specialization(specialization_id: int, db: Session = Depends(get_db)):
    db_specialization = db.query(models.Specialization).filter(models.Specialization.id == specialization_id).first()
    if db_specialization is None:
        raise HTTPException(status_code=404, detail="Specialization not found")
    db.delete(db_specialization)
    db.commit()
    return {"message": "Specialization deleted successfully"}

# --- Course ---
@router.post("/courses/", response_model=schemas.CourseOut, tags=["Courses"])
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/courses/", response_model=List[schemas.CourseOut], tags=["Courses"])
def read_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    courses = db.query(models.Course).offset(skip).limit(limit).all()
    return courses

@router.get("/courses/{course_id}", response_model=schemas.CourseOut, tags=["Courses"])
def read_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.put("/courses/{course_id}", response_model=schemas.CourseOut, tags=["Courses"])
def update_course(course_id: int, course: schemas.CourseCreate, db: Session = Depends(get_db)):
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    
    for key, value in course.model_dump().items():
        setattr(db_course, key, value)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.delete("/courses/{course_id}", tags=["Courses"])
def delete_course(course_id: int, db: Session = Depends(get_db)):
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(db_course)
    db.commit()
    return {"message": "Course deleted successfully"}

# --- Topic ---
@router.post("/topics/", response_model=schemas.TopicOut, tags=["Topics"])
def create_topic(topic: schemas.TopicCreate, db: Session = Depends(get_db)):
    db_topic = models.Topic(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@router.get("/topics/", response_model=List[schemas.TopicOut], tags=["Topics"])
def read_topics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    topics = db.query(models.Topic).offset(skip).limit(limit).all()
    return topics

@router.get("/topics/{topic_id}", response_model=schemas.TopicOut, tags=["Topics"])
def read_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

@router.put("/topics/{topic_id}", response_model=schemas.TopicOut, tags=["Topics"])
def update_topic(topic_id: int, topic: schemas.TopicCreate, db: Session = Depends(get_db)):
    db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if db_topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    for key, value in topic.model_dump().items():
        setattr(db_topic, key, value)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@router.delete("/topics/{topic_id}", tags=["Topics"])
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if db_topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(db_topic)
    db.commit()
    return {"message": "Topic deleted successfully"}

# --- ProgressStatus ---
@router.post("/progress-status/", response_model=schemas.ProgressStatusOut, tags=["Student Progress"])
def create_progress_status(status_in: schemas.ProgressStatusCreate, db: Session = Depends(get_db)):
    db_status = models.ProgressStatus(**status_in.model_dump())
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

@router.get("/progress-status/", response_model=List[schemas.ProgressStatusOut], tags=["Student Progress"])
def read_progress_statuses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    statuses = db.query(models.ProgressStatus).offset(skip).limit(limit).all()
    return statuses

# --- CourseProgress ---
@router.post("/course-progress/", response_model=schemas.CourseProgressOut, tags=["Student Progress"])
def create_course_progress(progress: schemas.CourseProgressCreate, db: Session = Depends(get_db)):
    db_progress = models.CourseProgress(**progress.model_dump())
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress

@router.get("/course-progress/", response_model=List[schemas.CourseProgressOut], tags=["Student Progress"])
def read_course_progresses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    progresses = db.query(models.CourseProgress).offset(skip).limit(limit).all()
    return progresses

# --- IsComplete (Topic Completion) ---
@router.post("/topic-completions/", response_model=schemas.IsCompleteOut, tags=["Student Progress"])
def create_topic_completion(completion: schemas.IsCompleteCreate, db: Session = Depends(get_db)):
    db_completion = models.IsComplete(**completion.model_dump())
    db.add(db_completion)
    db.commit()
    db.refresh(db_completion)
    return db_completion

@router.get("/topic-completions/", response_model=List[schemas.IsCompleteOut], tags=["Student Progress"])
def read_topic_completions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    completions = db.query(models.IsComplete).offset(skip).limit(limit).all()
    return completions
