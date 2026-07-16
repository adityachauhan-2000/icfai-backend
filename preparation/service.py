from sqlalchemy.orm import Session
from . import models, schemas

def get_companies(db: Session):
    return db.query(models.Company).all()

def get_company(db: Session, company_id: int):
    return db.query(models.Company).filter(models.Company.id == company_id).first()

def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = models.Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def update_company(db: Session, company_id: int, company: schemas.CompanyUpdate):
    db_company = get_company(db, company_id)
    if not db_company:
        return None
    for key, value in company.model_dump(exclude_unset=True).items():
        setattr(db_company, key, value)
    db.commit()
    db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: int):
    db_company = get_company(db, company_id)
    if db_company:
        db.delete(db_company)
        db.commit()
    return db_company

def create_round(db: Session, company_id: int, round_data: schemas.InterviewRoundCreate):
    data_dict = round_data.model_dump()
    
    # Enforce standard time limits based on round type
    if data_dict.get('type') == 'gd':
        data_dict['timeLimit'] = 600
    elif data_dict.get('type') == 'aptitude':
        data_dict['timeLimit'] = 3600
    elif data_dict.get('type') == 'interview':
        data_dict['timeLimit'] = 1200
        
    db_round = models.InterviewRound(**data_dict, company_id=company_id)
    db.add(db_round)
    db.commit()
    db.refresh(db_round)
    return db_round

def get_round(db: Session, round_id: int):
    return db.query(models.InterviewRound).filter(models.InterviewRound.id == round_id).first()

def update_round(db: Session, round_id: int, round_data: schemas.InterviewRoundUpdate):
    db_round = get_round(db, round_id)
    if not db_round:
        return None
        
    update_data = round_data.model_dump(exclude_unset=True)
    
    # Enforce standard time limits if round type is updated
    if 'type' in update_data:
        if update_data['type'] == 'gd':
            update_data['timeLimit'] = 600
        elif update_data['type'] == 'aptitude':
            update_data['timeLimit'] = 3600
        elif update_data['type'] == 'interview':
            update_data['timeLimit'] = 1200
            
    for key, value in update_data.items():
        setattr(db_round, key, value)
    db.commit()
    db.refresh(db_round)
    return db_round

def delete_round(db: Session, round_id: int):
    db_round = get_round(db, round_id)
    if db_round:
        db.delete(db_round)
        db.commit()
    return db_round

def create_aptitude_question(db: Session, round_id: int, question_data: schemas.AptitudeQuestionBase):
    db_q = models.AptitudeQuestion(**question_data.model_dump(), round_id=round_id)
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q

def get_aptitude_question(db: Session, question_id: int):
    return db.query(models.AptitudeQuestion).filter(models.AptitudeQuestion.id == question_id).first()

def update_aptitude_question(db: Session, question_id: int, question_data: schemas.AptitudeQuestionBase):
    db_q = get_aptitude_question(db, question_id)
    if not db_q:
        return None
    for key, value in question_data.model_dump(exclude_unset=True).items():
        setattr(db_q, key, value)
    db.commit()
    db.refresh(db_q)
    return db_q

def delete_aptitude_question(db: Session, question_id: int):
    db_q = get_aptitude_question(db, question_id)
    if db_q:
        db.delete(db_q)
        db.commit()
    return db_q
