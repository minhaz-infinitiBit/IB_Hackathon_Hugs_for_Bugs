import redis
import json
from .celery_worker import celery_app
from app.core.database import get_db
from app.models.files import Project, RunStatus, File
from app.services.preprocess_document import DocumentPreprocessService

document_processing_service = DocumentPreprocessService()
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def publish_status(project_id: int, status: str, message: str = "", progress: int = 0):
    payload = json.dumps({
        "project_id": project_id,
        "status": status,
        "message": message,
        "progress": progress
    })
    redis_client.publish(f"project:{project_id}:status", payload)

@celery_app.task
def document_processing(project_id: int):
    db = next(get_db())
    project = None
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            publish_status(project_id, "error", "Project not found")
            return

        project.status = RunStatus.processing
        db.commit()
        publish_status(project_id, "processing", "Starting processing...")

        files = db.query(File).filter(File.project_id == project_id).all()
        total = len(files)

        for idx, file in enumerate(files, 1):
            publish_status(project_id, "processing", f"Processing file {idx}/{total}: {file.file_path}", int((idx - 1) / total * 100))

            result = document_processing_service.process_document(file.file_path)

            if not result.success:
                project.status = RunStatus.failed_processing
                db.commit()
                publish_status(project_id, "error", f"Failed on file: {file.file_path} - {result.error_message}")
                return

            summary_json = {
                "filename": result.llm_output_file,
                "keywords": result.keywords,
                "key_entities": result.key_entities,
                "document_type": result.document_type,
                "structured_content": result.structured_content,
                "summary": result.summary,
            }
            file.summary_json = str(summary_json)
            db.commit()
            publish_status(project_id, "processing", f"Completed file {idx}/{total}", int(idx / total * 100))

        project.status = RunStatus.finished_processing
        db.commit()
        publish_status(project_id, "completed", "All files processed successfully", 100)

    except Exception as e:
        if project:
            project.status = RunStatus.failed_processing
            db.commit()
        publish_status(project_id, "error", str(e))
    finally:
        db.close()