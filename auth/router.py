from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, UploadFile, File
from sqlalchemy.orm import Session
from config.database import get_db
from auth.models import Student, Admin
from auth.schemas import (
    StudentCreate,
    StudentLogin,
    StudentOut,
    StudentUpdate,
    StudentPasswordUpdate,
    AdminCreate,
    AdminLogin,
    AdminResponse,
    AdminUpdate,
    AdminPasswordUpdate
)
from auth.utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_admin
)
import os
import shutil
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_current_student(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("student_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
        
    student_id = payload.get("sub")
    if not student_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
        
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student not found",
        )
        
    if not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
        
    return student

# --- Student Auth Endpoints ---

@router.post("/register", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def register_student(student_in: StudentCreate, db: Session = Depends(get_db)):
    existing_student = db.query(Student).filter(Student.email == student_in.email).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_pwd = get_password_hash(student_in.password)
    new_student = Student(
        name=student_in.name,
        email=student_in.email,
        phone=student_in.phone,
        hash_pass=hashed_pwd,
        is_active=True
    )
    
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@router.post("/login")
def login_student(response: Response, student_in: StudentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == student_in.email).first()
    if not student or not verify_password(student_in.password, student.hash_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    token = create_access_token(data={"sub": str(student.id)})
    
    response.set_cookie(
        key="student_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60*24*7*60
    )
    return {"message": "Login successful"}

@router.post("/logout")
def logout_student(response: Response):
    response.delete_cookie(key="student_token", httponly=True, samesite="lax", secure=False)
    return {"message": "Logout successful"}

@router.get("/student/me", response_model=StudentOut)
def read_student_me(current_student: Student = Depends(get_current_student)):
    return current_student

@router.put("/student/me", response_model=StudentOut)
def update_student_me(student_in: StudentUpdate, db: Session = Depends(get_db), current_student: Student = Depends(get_current_student)):
    current_student.name = student_in.name
    db.commit()
    db.refresh(current_student)
    return current_student

@router.put("/student/me/password")
def update_student_password(password_in: StudentPasswordUpdate, db: Session = Depends(get_db), current_student: Student = Depends(get_current_student)):
    if not verify_password(password_in.current_password, current_student.hash_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password",
        )
    
    current_student.hash_pass = get_password_hash(password_in.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

@router.post("/student/me/upload-image")
def upload_student_image(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_student: Student = Depends(get_current_student)
):
    os.makedirs("uploads/profiles", exist_ok=True)
    ext = file.filename.split(".")[-1]
    filename = f"student_{current_student.id}_{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join("uploads", "profiles", filename)
    
    if current_student.profile_image:
        old_path = current_student.profile_image.replace("http://localhost:8000/", "")
        if os.path.exists(old_path):
            os.remove(old_path)
            
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    image_url = f"http://localhost:8000/{file_path.replace(os.sep, '/')}"
    current_student.profile_image = image_url
    db.commit()
    db.refresh(current_student)
    
    return {"profile_image": image_url}

# Admin Auth Endpoints

@router.post("/admin/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def register_admin(admin_in: AdminCreate, db: Session = Depends(get_db)):
    existing_admin = db.query(Admin).filter(Admin.email == admin_in.email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email already registered",
        )
    
    hashed_pwd = get_password_hash(admin_in.password)
    new_admin = Admin(
        name=admin_in.name,
        email=admin_in.email,
        hash_pass=hashed_pwd
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin

@router.post("/admin/login")
def login_admin(response: Response, admin_in: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == admin_in.email).first()
    if not admin or not verify_password(admin_in.password, admin.hash_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    token = create_access_token(data={"sub": str(admin.id)})
    
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60*24*7*60
    )
    return {"message": "Admin login successful"}

@router.post("/admin/logout")
def logout_admin(response: Response):
    response.delete_cookie(key="admin_token", httponly=True, samesite="lax", secure=False)
    return {"message": "Admin logout successful"}

@router.get("/admin/me", response_model=AdminResponse)
def read_admin_me(current_admin: Admin = Depends(get_current_admin)):
    return current_admin

@router.put("/admin/me", response_model=AdminResponse)
def update_admin_me(admin_in: AdminUpdate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    current_admin.name = admin_in.name
    db.commit()
    db.refresh(current_admin)
    return current_admin

@router.put("/admin/me/password")
def update_admin_password(password_in: AdminPasswordUpdate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    if not verify_password(password_in.current_password, current_admin.hash_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password",
        )
    
    current_admin.hash_pass = get_password_hash(password_in.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

@router.post("/admin/me/upload-image")
def upload_admin_image(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_admin: Admin = Depends(get_current_admin)
):
    # Ensure directory exists
    os.makedirs("uploads/profiles", exist_ok=True)
    
    # Generate unique filename
    ext = file.filename.split(".")[-1]
    filename = f"admin_{current_admin.id}_{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join("uploads", "profiles", filename)
    
    # Delete old profile image if exists
    if current_admin.profile_image:
        old_path = current_admin.profile_image.replace("http://localhost:8000/", "")
        if os.path.exists(old_path):
            os.remove(old_path)
    
    # Save new file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Update database
    image_url = f"http://localhost:8000/{file_path.replace(os.sep, '/')}"
    current_admin.profile_image = image_url
    db.commit()
    db.refresh(current_admin)
    
    return {"profile_image": image_url}
