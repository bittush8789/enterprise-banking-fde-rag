import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models import AuditLog
from backend.app.guardrails.pii_masker import PIIMasker

logger = logging.getLogger("bankassist.audit")

class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        event_status: str,
        user_id: Optional[int] = None,
        details: Optional[Any] = None,
    ) -> AuditLog:
        """
        Persists a security or audit event with automatic PII masking.
        """
        masked_details_str = None
        if details is not None:
            if isinstance(details, (dict, list)):
                raw_json = json.dumps(details)
                masked_str, _ = PIIMasker.mask_text(raw_json)
                masked_details_str = masked_str
            else:
                masked_str, _ = PIIMasker.mask_text(str(details))
                masked_details_str = masked_str

        audit_entry = AuditLog(
            user_id=user_id,
            event_type=event_type,
            event_status=event_status,
            details=masked_details_str,
        )

        try:
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
            logger.info(f"Audit event logged: [{event_type}] status={event_status} user_id={user_id}")
            return audit_entry
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to write audit log: {e}")
            return None
