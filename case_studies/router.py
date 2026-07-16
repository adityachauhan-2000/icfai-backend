from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from case_studies import models, schemas

router = APIRouter(prefix="/case-studies", tags=["Case Studies"])


@router.post("", response_model=schemas.CaseStudyOut, status_code=status.HTTP_201_CREATED)
def create_case_study(case_study: schemas.CaseStudyCreate, db: Session = Depends(get_db)):
    db_case_study = models.CaseStudy(**case_study.model_dump())
    db.add(db_case_study)
    db.commit()
    db.refresh(db_case_study)
    return db_case_study


@router.get("", response_model=schemas.CaseStudyListResponse)
def read_case_studies(db: Session = Depends(get_db)):
    active_case_studies = (
        db.query(models.CaseStudy)
        .filter(models.CaseStudy.is_active == True)
        .order_by(models.CaseStudy.display_order.asc())
        .all()
    )
    return {"case_studies": active_case_studies}


@router.get("/{case_study_id}", response_model=schemas.CaseStudyOut)
def read_case_study(case_study_id: int, db: Session = Depends(get_db)):
    case_study = db.query(models.CaseStudy).filter(models.CaseStudy.id == case_study_id).first()
    if case_study is None:
        raise HTTPException(status_code=404, detail="Case study not found")
    return case_study


@router.put("/{case_study_id}", response_model=schemas.CaseStudyOut)
def update_case_study(case_study_id: int, case_study_in: schemas.CaseStudyUpdate, db: Session = Depends(get_db)):
    db_case_study = db.query(models.CaseStudy).filter(models.CaseStudy.id == case_study_id).first()
    if db_case_study is None:
        raise HTTPException(status_code=404, detail="Case study not found")

    update_data = case_study_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_case_study, key, value)

    db.commit()
    db.refresh(db_case_study)
    return db_case_study


@router.delete("/{case_study_id}")
def delete_case_study(case_study_id: int, db: Session = Depends(get_db)):
    db_case_study = db.query(models.CaseStudy).filter(models.CaseStudy.id == case_study_id).first()
    if db_case_study is None:
        raise HTTPException(status_code=404, detail="Case study not found")

    db.delete(db_case_study)
    db.commit()
    return {"message": "Case study deleted successfully"}


@router.get("/{case_study_id}/youtube-resources", response_model=list[schemas.CaseStudyResourceOut])
def read_case_study_resources(case_study_id: int, db: Session = Depends(get_db)):
    db_case_study = db.query(models.CaseStudy).filter(models.CaseStudy.id == case_study_id).first()
    if db_case_study is None:
        raise HTTPException(status_code=404, detail="Case study not found")
    return db.query(models.CaseStudyResource).filter(models.CaseStudyResource.case_study_id == case_study_id).order_by(models.CaseStudyResource.display_order.asc()).all()


@router.post("/{case_study_id}/youtube-resources")
def create_case_study_resources(
    case_study_id: int,
    payload: schemas.CaseStudyResourceBatchInput | schemas.CaseStudyResourceCreate,
    db: Session = Depends(get_db)
):
    db_case_study = db.query(models.CaseStudy).filter(models.CaseStudy.id == case_study_id).first()
    if db_case_study is None:
        raise HTTPException(status_code=404, detail="Case study not found")

    if isinstance(payload, schemas.CaseStudyResourceBatchInput):
        db.query(models.CaseStudyResource).filter(models.CaseStudyResource.case_study_id == case_study_id).delete()
        new_items = []
        for res_in in payload.resources:
            db_res = models.CaseStudyResource(
                case_study_id=case_study_id,
                **res_in.model_dump()
            )
            db.add(db_res)
            new_items.append(db_res)
        db.commit()
        for item in new_items:
            db.refresh(item)
        return [schemas.CaseStudyResourceOut.model_validate(item) for item in new_items]
    else:
        db_res = models.CaseStudyResource(
            case_study_id=case_study_id,
            **payload.model_dump()
        )
        db.add(db_res)
        db.commit()
        db.refresh(db_res)
        return schemas.CaseStudyResourceOut.model_validate(db_res)


@router.put("/{case_study_id}/youtube-resources/{resource_id}", response_model=schemas.CaseStudyResourceOut)
def update_case_study_resource(
    case_study_id: int,
    resource_id: int,
    resource_in: schemas.CaseStudyResourceUpdate,
    db: Session = Depends(get_db)
):
    db_res = db.query(models.CaseStudyResource).filter(
        models.CaseStudyResource.id == resource_id,
        models.CaseStudyResource.case_study_id == case_study_id
    ).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Resource not found")

    update_data = resource_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_res, key, value)

    db.commit()
    db.refresh(db_res)
    return db_res


@router.delete("/{case_study_id}/youtube-resources/{resource_id}")
def delete_case_study_resource(case_study_id: int, resource_id: int, db: Session = Depends(get_db)):
    db_res = db.query(models.CaseStudyResource).filter(
        models.CaseStudyResource.id == resource_id,
        models.CaseStudyResource.case_study_id == case_study_id
    ).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Resource not found")

    db.delete(db_res)
    db.commit()
    return {"message": "Resource deleted successfully"}
