from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import uuid

from config.database import get_db
from auth.router import get_current_student
from auth.models import Student
from . import schemas, service

from pydantic import BaseModel

class FrontendLog(BaseModel):
    message: str

router = APIRouter(prefix="/preparation", tags=["Preparation"])

@router.post("/log")
def log_frontend_message(log_data: FrontendLog):
    print(f"[FRONTEND WebRTC LOG] {log_data.message}")
    return {"status": "ok"}

@router.post("/webrtc/session")
async def webrtc_session(round_type: str = "interview", current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    from .kitefish import KiteFishAIService
    kitefish_service = KiteFishAIService()
    try:
        from study_plans.models import Program
        program = db.query(Program).filter(Program.id == current_student.program_id).first() if current_student.program_id else None
        program_name = program.name if program else "Management"
        
        if round_type == "gd":
            instructions = (
                f"You are Rex, a senior GD Moderator at a Fortune 500 company in India. You are moderating a group discussion for {current_student.name} "
                f"who is from a {program_name} program background. \n\n"
                "CRITICAL LANGUAGE & TONE RULES:\n"
                "- Speak ONLY in English. Never use any other language or mixed dialects.\n"
                "- Adopt the tone of a professional, articulate corporate leader: warm, polite, respectful, yet thorough and evaluative.\n"
                "- Speak at a calm, deliberate, and relaxed pace. Use frequent commas, hyphens, and ellipses (...) in your responses to naturally slow down your voice.\n\n"
                "BEHAVIOR & TURN-TAKING RULES:\n"
                "- The opening: Warmly welcome the candidate by name. Introduce yourself briefly as Rex, the moderator, clearly state the discussion topic, and STOP.\n"
                "- ONE question per turn: Never ask multiple questions at once. Ask your question clearly, then STOP completely and wait for the full response.\n"
                "- Patient listening: Assume the candidate may pause for a few seconds while thinking. Do not rush the conversation.\n"
                "- Active listening: Briefly acknowledge what they just said with natural transition phrases (e.g., 'I see...', 'That makes sense...') before challenging or probing deeper.\n"
                "- Keep turns SHORT: Limit your responses to 1 to 3 spoken sentences maximum. Real moderators do not give speeches."
            )
        else:
            instructions = (
                f"You are Rex, a senior Hiring Manager at a Fortune 500 company in India, conducting a personal interview. "
                f"You are interviewing {current_student.name} for a role matching their {program_name} program background. \n\n"
                "CRITICAL LANGUAGE & TONE RULES:\n"
                "- Speak ONLY in English. Never use any other language or mixed dialects.\n"
                "- Adopt the tone of a professional, articulate Indian corporate leader: warm, polite, respectful, yet thorough and evaluative.\n"
                "- Speak at a calm, deliberate, and relaxed pace. Use phrasing like 'Take your time,' 'That is quite interesting,' or 'I appreciate you sharing that.'\n"
                "- Use frequent commas, hyphens, and ellipses (...) in your responses. This naturally forces the voice engine to pause and speak more slowly.\n\n"
                "BEHAVIOR & TURN-TAKING RULES:\n"
                "- The opening: Warmly greet the candidate by name. Introduce yourself as Rex, the hiring manager. Ask a brief, welcoming question to settle them in (e.g., 'Hello {current_student.name}, it is a pleasure to meet you today... How are you doing?') and STOP.\n"
                "- ONE question per turn: Never ask multiple questions at once. Ask your question clearly, then STOP completely and wait for the full response.\n"
                "- Patient listening: Assume the candidate may pause for a few seconds while thinking. Do not rush the conversation.\n"
                "- Active listening: Briefly acknowledge what they just said with natural transition phrases (e.g., 'I see...', 'That makes sense...', 'Right, that is a great point...') before moving to your next question.\n"
                "- Deep probing: Ask tailored follow-up questions based on the details they provide, rather than reading from a generic script.\n"
                "- Keep turns SHORT: Limit your responses to 1 to 3 spoken sentences maximum. Real interviewers do not give monologues.\n"
                "- Clarification: If an answer is too brief or unclear, politely ask them to elaborate (e.g., 'Could you shed some more light on how you handled that specific challenge?')."
            )
        
        data = await kitefish_service.create_realtime_session(instructions=instructions)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webrtc/sdp")
async def webrtc_sdp(request: Request, current_student: Student = Depends(get_current_student)):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    client_secret = auth_header.replace("Bearer ", "")
    body = await request.body()
    sdp_offer = body.decode('utf-8')
    
    from .kitefish import KiteFishAIService
    kitefish_service = KiteFishAIService()
    try:
        answer_sdp = await kitefish_service.exchange_sdp(client_secret, sdp_offer)
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=answer_sdp, media_type="application/sdp")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-logo")
async def upload_logo(request: Request, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    
    # Use /tmp on Vercel because the main filesystem is read-only
    base_dir = "/tmp/uploads/logos" if os.getenv("VERCEL") else os.path.join("uploads", "logos")
    os.makedirs(base_dir, exist_ok=True)
    
    file_path = os.path.join(base_dir, file_name)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    base_url = str(request.base_url).rstrip("/")
    return {"url": f"{base_url}/uploads/logos/{file_name}"}

@router.get("/companies", response_model=List[schemas.CompanyResponse])
def get_companies(db: Session = Depends(get_db)):
    return service.get_companies(db)

@router.get("/companies/{company_id}", response_model=schemas.CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = service.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.post("/companies", response_model=schemas.CompanyResponse)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    return service.create_company(db, company)

@router.put("/companies/{company_id}", response_model=schemas.CompanyResponse)
def update_company(company_id: int, company: schemas.CompanyUpdate, db: Session = Depends(get_db)):
    db_company = service.update_company(db, company_id, company)
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    return db_company

@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    db_company = service.delete_company(db, company_id)
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted successfully"}

@router.post("/companies/{company_id}/rounds", response_model=schemas.InterviewRoundResponse)
def create_round(company_id: int, round_data: schemas.InterviewRoundCreate, db: Session = Depends(get_db)):
    company = service.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return service.create_round(db, company_id, round_data)

@router.put("/rounds/{round_id}", response_model=schemas.InterviewRoundResponse)
def update_round(round_id: int, round_data: schemas.InterviewRoundUpdate, db: Session = Depends(get_db)):
    db_round = service.update_round(db, round_id, round_data)
    if not db_round:
        raise HTTPException(status_code=404, detail="Round not found")
    return db_round

@router.delete("/rounds/{round_id}")
def delete_round(round_id: int, db: Session = Depends(get_db)):
    db_round = service.delete_round(db, round_id)
    if not db_round:
        raise HTTPException(status_code=404, detail="Round not found")
    return {"message": "Round deleted successfully"}

from .models import AptitudeQuestion
from sqlalchemy.sql.expression import func

from fastapi import Response

@router.get("/rounds/{round_id}/questions", response_model=List[schemas.AptitudeQuestionResponse])
def get_round_questions(round_id: int, response: Response, all: bool = False, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    # Pull from the global question bank instead of filtering by round_id
    # since questions were only seeded for round 1
    query = db.query(AptitudeQuestion)
    if all:
        return query.all()
    else:
        return query.order_by(func.random()).limit(60).all()

@router.post("/rounds/{round_id}/questions", response_model=schemas.AptitudeQuestionResponse)
def create_question(round_id: int, question: schemas.AptitudeQuestionBase, db: Session = Depends(get_db)):
    round_exists = service.get_round(db, round_id)
    if not round_exists:
        raise HTTPException(status_code=404, detail="Round not found")
    return service.create_aptitude_question(db, round_id, question)

@router.put("/questions/{question_id}", response_model=schemas.AptitudeQuestionResponse)
def update_question(question_id: int, question: schemas.AptitudeQuestionBase, db: Session = Depends(get_db)):
    db_q = service.update_aptitude_question(db, question_id, question)
    if not db_q:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_q

@router.delete("/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    db_q = service.delete_aptitude_question(db, question_id)
    if not db_q:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question deleted successfully"}

@router.get("/questions", response_model=schemas.PaginatedAptitudeQuestionResponse)
def get_all_questions(page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    total = db.query(AptitudeQuestion).count()
    offset = (page - 1) * limit
    questions = db.query(AptitudeQuestion).offset(offset).limit(limit).all()
    return {
        "data": questions,
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/aptitude-rounds", response_model=List[schemas.InterviewRoundResponse])
def get_aptitude_rounds(db: Session = Depends(get_db)):
    from .models import InterviewRound
    return db.query(InterviewRound).filter(InterviewRound.type == "aptitude").all()

from fastapi import Form
from .kitefish import KiteFishAIService
import json
from .models import InterviewResult, GDQuestion, InterviewQuestion

@router.get("/gd-questions/random", response_model=schemas.GDQuestionResponse)
def get_random_gd_question(program_id: int, db: Session = Depends(get_db)):
    question = db.query(GDQuestion).filter(GDQuestion.program_id == program_id).order_by(func.random()).first()
    if not question:
        raise HTTPException(status_code=404, detail="No GD question found for this program")
    return question

@router.get("/interview-questions/random", response_model=schemas.InterviewQuestionResponse)
def get_random_interview_question(program_id: int, db: Session = Depends(get_db)):
    question = db.query(InterviewQuestion).filter(InterviewQuestion.program_id == program_id).order_by(func.random()).first()
    if not question:
        raise HTTPException(status_code=404, detail="No Interview question found for this program")
    return question

@router.post("/analyze-interview", response_model=schemas.InterviewResultResponse)
async def analyze_interview(
    company_id: int = Form(...),
    student_id: int = Form(...),
    aptitude_score: str = Form("{}"),
    gd_question_text: str = Form(""),
    interview_question_text: str = Form(""),
    gd_audio: UploadFile = File(None),
    interview_video: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    kitefish = KiteFishAIService()
    
    posture_analysis = "No video provided for the interview."
    if interview_video:
        content = await interview_video.read()
        await interview_video.seek(0)
        if len(content) > 1000:
            video_result = await kitefish.analyze_video(interview_video)
            posture_analysis = video_result.get("posture_analysis", "")
        else:
            posture_analysis = "Video response was too short or empty."
        
    interview_transcript = "No audio provided for the interview."
    if interview_video:
        content = await interview_video.read()
        await interview_video.seek(0)
        if len(content) > 1000:
            interview_transcript = await kitefish.transcribe_audio(interview_video)
        else:
            interview_transcript = "Audio response was too short or empty."
        
    gd_transcript = "No audio provided for the group discussion."
    if gd_audio:
        content = await gd_audio.read()
        await gd_audio.seek(0)
        if len(content) > 1000:
            gd_transcript = await kitefish.transcribe_audio(gd_audio)
        else:
            gd_transcript = "Audio response was too short or empty."
        
    try:
        aptitude_data = json.loads(aptitude_score)
    except:
        aptitude_data = {}
        
    final_report = await kitefish.generate_interview_report(
        gd_transcript=gd_transcript,
        interview_transcript=interview_transcript,
        posture_analysis=posture_analysis,
        aptitude_score=aptitude_data,
        gd_question=gd_question_text,
        interview_question=interview_question_text
    )
    
    # Calculate overall score: aptitude score (correct count, max 60) + LLM score (max 40)
    aptitude_points = aptitude_data.get("correct", 0)
    llm_score = final_report.get("overall_score", 0)
    
    # Fallback/Scale check: if LLM returned score out of 100 instead of 40, scale it down to 40
    if llm_score > 40:
        llm_score = int((llm_score / 100.0) * 40)
        
    # Check if candidate did nothing in GD and Personal Interview
    is_gd_empty = (not gd_transcript or 
                   "No audio" in gd_transcript or 
                   "too short or empty" in gd_transcript or
                   len(gd_transcript.strip()) < 15)
                   
    is_interview_empty = (not interview_transcript or 
                          "No audio" in interview_transcript or 
                          "too short or empty" in interview_transcript or
                          len(interview_transcript.strip()) < 15)
                          
    if is_gd_empty and is_interview_empty:
        llm_score = 1  # 1 score for doing nothing in GD and interview
        
    calculated_overall_score = min(aptitude_points + llm_score, 100)
    final_report["overall_score"] = calculated_overall_score
    
    # Save to database
    db_result = InterviewResult(
        company_id=company_id,
        student_id=student_id,
        aptitude_score=aptitude_data,
        gd_analysis={"posture": posture_analysis, "question": gd_question_text, "transcript": gd_transcript},
        interview_analysis={"report": final_report, "question": interview_question_text, "transcript": interview_transcript},
        overall_score=calculated_overall_score
    )
    
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    print("\n" + "*"*40)
    print(f"✅ FINAL ANALYSIS SAVED TO DATABASE FOR STUDENT {student_id}")
    print(f"Overall Score: {db_result.overall_score}")
    print("*"*40 + "\n")
    
    return db_result

@router.get("/all-sessions", response_model=List[schemas.InterviewResultResponse])
def get_all_sessions(current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    results = db.query(InterviewResult).filter(
        InterviewResult.student_id == current_student.id
    ).order_by(InterviewResult.id.desc()).all()
    return results

@router.get("/sessions/{company_id}", response_model=List[schemas.InterviewResultResponse])
def get_sessions_for_company(company_id: int, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    results = db.query(InterviewResult).filter(
        InterviewResult.student_id == current_student.id,
        InterviewResult.company_id == company_id
    ).order_by(InterviewResult.id.desc()).all()
    return results

@router.get("/sessions/detail/{session_id}", response_model=schemas.InterviewResultResponse)
def get_session_detail(session_id: int, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    result = db.query(InterviewResult).filter(
        InterviewResult.id == session_id,
        InterviewResult.student_id == current_student.id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result
