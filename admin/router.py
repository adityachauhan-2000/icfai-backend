from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from config.database import get_db
from auth.models import Student
from study_plans.models import Program
from admin.schemas import StudentAdminCreate, StudentAdminUpdate, StudentAdminOut, AdminStats
from auth.utils import get_password_hash
from case_studies import models as case_study_models, schemas as case_study_schemas

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/students", response_model=list[StudentAdminOut])
def get_all_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    result = []
    for s in students:
        branch = "N/A"
        if s.program_id:
            prog = db.query(Program).filter(Program.id == s.program_id).first()
            if prog:
                branch = prog.name
                
        result.append({
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "phone": s.phone,
            "program_id": s.program_id,
            "is_active": s.is_active,
            "branch": branch,
            "year": "N/A",
            "status": "In Progress" if s.is_active else "Needs Attention",
            "studyPlanProgress": 0,
            "interviewsCompleted": 0,
            "averageMockScore": 0,
            "joinDate": "July 2026"
        })
    return result

@router.post("/students", response_model=StudentAdminOut)
def create_student(student_in: StudentAdminCreate, db: Session = Depends(get_db)):
    existing_student = db.query(Student).filter(Student.email == student_in.email).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    import secrets
    import string
    
    # Generate random password
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(12))
    
    print(f"\n{'='*50}")
    print(f" NEW CREDENTIAL GENERATED ")
    print(f" Email: {student_in.email}")
    print(f" Password: {password}")
    print(f"{'='*50}\n")
    
    hashed_pwd = get_password_hash(password)
    new_student = Student(
        name=student_in.name,
        email=student_in.email,
        phone=student_in.phone,
        program_id=student_in.program_id,
        is_active=student_in.is_active,
        hash_pass=hashed_pwd
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    branch = "N/A"
    if new_student.program_id:
        prog = db.query(Program).filter(Program.id == new_student.program_id).first()
        if prog:
            branch = prog.name
            
    return {
        "id": new_student.id,
        "name": new_student.name,
        "email": new_student.email,
        "phone": new_student.phone,
        "program_id": new_student.program_id,
        "is_active": new_student.is_active,
        "branch": branch,
        "year": "N/A",
        "status": "In Progress",
        "studyPlanProgress": 0,
        "interviewsCompleted": 0,
        "averageMockScore": 0,
        "joinDate": "July 2026"
    }

@router.put("/students/{student_id}", response_model=StudentAdminOut)
def update_student(student_id: int, student_in: StudentAdminUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    update_data = student_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(student, key, value)
        
    db.commit()
    db.refresh(student)
    
    branch = "N/A"
    if student.program_id:
        prog = db.query(Program).filter(Program.id == student.program_id).first()
        if prog:
            branch = prog.name
            
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "program_id": student.program_id,
        "is_active": student.is_active,
        "branch": branch,
        "year": "N/A",
        "status": "In Progress" if student.is_active else "Needs Attention",
        "studyPlanProgress": 0,
        "interviewsCompleted": 0,
        "averageMockScore": 0,
        "joinDate": "July 2026"
    }

@router.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    student.is_active = False
    db.commit()
    return {"message": "Student deleted"}

@router.get("/case-studies", response_model=list[case_study_schemas.CaseStudyOut])
def get_all_case_studies(db: Session = Depends(get_db)):
    return db.query(case_study_models.CaseStudy).order_by(case_study_models.CaseStudy.display_order.asc()).all()

@router.post("/case-studies", response_model=case_study_schemas.CaseStudyOut)
def create_admin_case_study(case_study: case_study_schemas.CaseStudyCreate, db: Session = Depends(get_db)):
    db_case_study = case_study_models.CaseStudy(**case_study.model_dump())
    db.add(db_case_study)
    db.commit()
    db.refresh(db_case_study)
    return db_case_study

@router.put("/case-studies/{case_study_id}", response_model=case_study_schemas.CaseStudyOut)
def update_admin_case_study(case_study_id: int, case_study_in: case_study_schemas.CaseStudyUpdate, db: Session = Depends(get_db)):
    db_case_study = db.query(case_study_models.CaseStudy).filter(case_study_models.CaseStudy.id == case_study_id).first()
    if not db_case_study:
        raise HTTPException(status_code=404, detail="Case study not found")
        
    update_data = case_study_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_case_study, key, value)
        
    db.commit()
    db.refresh(db_case_study)
    return db_case_study

@router.delete("/case-studies/{case_study_id}")
def delete_admin_case_study(case_study_id: int, db: Session = Depends(get_db)):
    db_case_study = db.query(case_study_models.CaseStudy).filter(case_study_models.CaseStudy.id == case_study_id).first()
    if not db_case_study:
        raise HTTPException(status_code=404, detail="Case study not found")
        
    db.delete(db_case_study)
    db.commit()
    return {"message": "Case study deleted"}

@router.get("/case-studies/{case_study_id}/youtube-resources", response_model=list[case_study_schemas.CaseStudyResourceOut])
def get_admin_case_study_resources(case_study_id: int, db: Session = Depends(get_db)):
    db_case_study = db.query(case_study_models.CaseStudy).filter(case_study_models.CaseStudy.id == case_study_id).first()
    if not db_case_study:
        raise HTTPException(status_code=404, detail="Case study not found")
    return db.query(case_study_models.CaseStudyResource).filter(case_study_models.CaseStudyResource.case_study_id == case_study_id).order_by(case_study_models.CaseStudyResource.display_order.asc()).all()

@router.post("/case-studies/{case_study_id}/youtube-resources")
def create_admin_case_study_resources(
    case_study_id: int,
    payload: case_study_schemas.CaseStudyResourceBatchInput | case_study_schemas.CaseStudyResourceCreate,
    db: Session = Depends(get_db)
):
    db_case_study = db.query(case_study_models.CaseStudy).filter(case_study_models.CaseStudy.id == case_study_id).first()
    if not db_case_study:
        raise HTTPException(status_code=404, detail="Case study not found")

    if isinstance(payload, case_study_schemas.CaseStudyResourceBatchInput):
        # Batch replacement/synchronization
        db.query(case_study_models.CaseStudyResource).filter(case_study_models.CaseStudyResource.case_study_id == case_study_id).delete()
        new_items = []
        for res_in in payload.resources:
            db_res = case_study_models.CaseStudyResource(
                case_study_id=case_study_id,
                **res_in.model_dump()
            )
            db.add(db_res)
            new_items.append(db_res)
        db.commit()
        for item in new_items:
            db.refresh(item)
        return [case_study_schemas.CaseStudyResourceOut.model_validate(item) for item in new_items]
    else:
        # Single resource creation
        db_res = case_study_models.CaseStudyResource(
            case_study_id=case_study_id,
            **payload.model_dump()
        )
        db.add(db_res)
        db.commit()
        db.refresh(db_res)
        return case_study_schemas.CaseStudyResourceOut.model_validate(db_res)

@router.put("/case-studies/{case_study_id}/youtube-resources/{resource_id}", response_model=case_study_schemas.CaseStudyResourceOut)
def update_admin_case_study_resource(
    case_study_id: int,
    resource_id: int,
    resource_in: case_study_schemas.CaseStudyResourceUpdate,
    db: Session = Depends(get_db)
):
    db_res = db.query(case_study_models.CaseStudyResource).filter(
        case_study_models.CaseStudyResource.id == resource_id,
        case_study_models.CaseStudyResource.case_study_id == case_study_id
    ).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Resource not found")

    update_data = resource_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_res, key, value)

    db.commit()
    db.refresh(db_res)
    return db_res

@router.delete("/case-studies/{case_study_id}/youtube-resources/{resource_id}")
def delete_admin_case_study_resource(case_study_id: int, resource_id: int, db: Session = Depends(get_db)):
    db_res = db.query(case_study_models.CaseStudyResource).filter(
        case_study_models.CaseStudyResource.id == resource_id,
        case_study_models.CaseStudyResource.case_study_id == case_study_id
    ).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Resource not found")

    db.delete(db_res)
    db.commit()
    return {"message": "Resource deleted successfully"}

@router.get("/stats", response_model=AdminStats)
def get_admin_stats(db: Session = Depends(get_db)):
    total = db.query(Student).count()
    active = db.query(Student).filter(Student.is_active == True).count()
    inactive = total - active
    
    return {
        "total_students": total,
        "active_students": active,
        "inactive_students": inactive,
        "last_month_active": active,
        "last_month_inactive": inactive
    }
