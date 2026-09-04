from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.id_generator import generate_business_id
from app.models.application import Application
from app.models.resume import Resume
from app.models.user import User
from app.services import audit_service, resume_parser


async def upload_resume_file(db: Session, application: Application, file: UploadFile, actor: User) -> Resume:
    """1 Resume/1 Application (v2 changelog #13) - neu da co resume (vi du tu
    luc dan text CV o Apply), file upload GHI DE len ban ghi do thay vi tao
    moi, giu nguyen business_id cu.
    """
    file_name, file_path, file_type, extracted_text = await resume_parser.save_and_extract(
        file, application.business_id
    )

    resume = db.query(Resume).filter(Resume.application_id == application.id).first()
    is_new = resume is None
    if resume is None:
        resume = Resume(
            business_id=generate_business_id(db, "resume"),
            candidate_id=application.candidate_id,
            application_id=application.id,
        )
        db.add(resume)

    resume.file_name = file_name
    resume.file_path = file_path
    resume.file_type = file_type
    resume.extracted_text = extracted_text
    db.flush()

    if not extracted_text:
        application.needs_manual_review = 1
        db.flush()

    audit_service.log(
        db,
        actor=actor,
        action="RESUME_UPLOADED" if is_new else "RESUME_REPLACED",
        entity_type="resume",
        entity_business_id=resume.business_id,
        after={"file_name": file_name, "extracted_chars": len(extracted_text)},
    )
    db.commit()
    db.refresh(resume)
    return resume
