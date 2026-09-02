import os
import sys
import shutil
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.core.database import engine, Base, SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.core.config import settings
from backend.app.models import User, Role, Document
from backend.app.rag.ingestion import DocumentIngestionService
from backend.app.services.audit_service import AuditService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bankassist.seed")

def seed_database():
    logger.info("Initializing BankAssist AI Database Schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create Roles
        role_definitions = [
            ("ADMIN", "System Administrator with unrestricted access"),
            ("LOAN_OFFICER", "Authorized for retail and commercial lending policies"),
            ("COMPLIANCE_OFFICER", "Authorized for KYC, AML, regulatory & audit policies"),
            ("CUSTOMER_SUPPORT", "Authorized for retail products, savings & fixed deposit guides"),
            ("MANAGER", "Departmental Manager with multi-division operational access"),
        ]

        roles_map = {}
        for rname, rdesc in role_definitions:
            role = db.query(Role).filter(Role.name == rname).first()
            if not role:
                role = Role(name=rname, description=rdesc)
                db.add(role)
                db.flush()
                logger.info(f"Created role: {rname}")
            roles_map[rname] = role

        db.commit()

        # 2. Create Default Test Users
        default_users = [
            ("Apex Administrator", "admin@bankassist.ai", "Admin@123456", ["ADMIN"]),
            ("Senior Loan Officer", "loan.officer@bankassist.ai", "Loan@123456", ["LOAN_OFFICER"]),
            ("Chief Compliance Analyst", "compliance@bankassist.ai", "Compliance@123456", ["COMPLIANCE_OFFICER"]),
            ("Customer Care Specialist", "support@bankassist.ai", "Support@123456", ["CUSTOMER_SUPPORT"]),
            ("Branch General Manager", "manager@bankassist.ai", "Manager@123456", ["MANAGER"]),
        ]

        created_users = {}
        for name, email, raw_password, user_roles in default_users:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    name=name,
                    email=email,
                    password_hash=get_password_hash(raw_password),
                    is_active=True
                )
                for rname in user_roles:
                    user.roles.append(roles_map[rname])
                db.add(user)
                db.flush()
                logger.info(f"Created default user: {email} (Roles: {user_roles})")
            created_users[email] = user

        db.commit()

        # 3. Ingest Sample Banking Documents
        sample_docs_dir = os.path.abspath("./data/sample_docs")
        uploads_dir = os.path.abspath(settings.UPLOAD_DIRECTORY)
        os.makedirs(uploads_dir, exist_ok=True)

        sample_documents_meta = [
            {
                "file_name": "Home_Loan_Policy_2026.txt",
                "document_name": "Apex Home Loan Underwriting Policy (2026)",
                "document_type": "loan_policy",
                "classification": "confidential",
                "department": "Retail Lending",
                "version": "v2.4",
                "allowed_roles": ["LOAN_OFFICER", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "KYC_AML_Compliance_Directive.txt",
                "document_name": "KYC & Anti-Money Laundering Master Directive",
                "document_type": "compliance_directive",
                "classification": "restricted",
                "department": "Regulatory Compliance",
                "version": "v3.1",
                "allowed_roles": ["COMPLIANCE_OFFICER", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Retail_Banking_Products_and_FD_Guide.txt",
                "document_name": "Retail Savings, Deposits & Fixed Deposit Guide",
                "document_type": "product_guide",
                "classification": "internal",
                "department": "Retail Banking",
                "version": "v4.0",
                "allowed_roles": ["CUSTOMER_SUPPORT", "LOAN_OFFICER", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Internal_IT_Security_SOP.txt",
                "document_name": "Internal IT & Cybersecurity Operational Standard",
                "document_type": "security_sop",
                "classification": "restricted",
                "department": "Information Security",
                "version": "v1.9",
                "allowed_roles": ["ADMIN", "MANAGER", "CUSTOMER_SUPPORT", "LOAN_OFFICER"],
            },
            {
                "file_name": "Credit_Card_Reward_and_Dispute_Policy_2026.txt",
                "document_name": "Credit Card Issuance, Rewards & Dispute Policy (2026)",
                "document_type": "card_policy",
                "classification": "internal",
                "department": "Cards & Digital Payments",
                "version": "v3.2",
                "allowed_roles": ["CUSTOMER_SUPPORT", "LOAN_OFFICER", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Commercial_MSME_Business_Loan_Policy.txt",
                "document_name": "Commercial Lending & MSME Business Financing Directive",
                "document_type": "commercial_loan_policy",
                "classification": "confidential",
                "department": "Commercial Credit Underwriting",
                "version": "v2.8",
                "allowed_roles": ["LOAN_OFFICER", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Digital_Banking_Fraud_Prevention_and_Zero_Liability_Policy.txt",
                "document_name": "Digital Fraud Defense & Customer Zero-Liability Mandate",
                "document_type": "fraud_policy",
                "classification": "public_mandate",
                "department": "Fraud Risk Management",
                "version": "v4.0",
                "allowed_roles": ["CUSTOMER_SUPPORT", "COMPLIANCE_OFFICER", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Foreign_Exchange_and_Cross_Border_Remittance_Guide.txt",
                "document_name": "Foreign Exchange & Cross-Border Remittance SOP",
                "document_type": "forex_sop",
                "classification": "internal",
                "department": "Treasury & Trade Ops",
                "version": "v3.1",
                "allowed_roles": ["CUSTOMER_SUPPORT", "COMPLIANCE_OFFICER", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Wealth_Management_and_Mutual_Fund_Advisory_SOP.txt",
                "document_name": "Wealth Management, Mutual Funds & Sovereign Gold Bonds SOP",
                "document_type": "wealth_sop",
                "classification": "internal_advisory",
                "department": "Wealth Management",
                "version": "v2.5",
                "allowed_roles": ["CUSTOMER_SUPPORT", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Personal_and_Education_Loan_Policy_2026.txt",
                "document_name": "Personal & Higher Education Loan Underwriting Policy (2026)",
                "document_type": "retail_loan_policy",
                "classification": "internal",
                "department": "Unsecured Retail Lending",
                "version": "v3.4",
                "allowed_roles": ["LOAN_OFFICER", "CUSTOMER_SUPPORT", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Trade_Finance_Letter_of_Credit_and_Bank_Guarantee_Manual.txt",
                "document_name": "Trade Finance, Letters of Credit (LC) & Bank Guarantees (BG) Manual",
                "document_type": "trade_manual",
                "classification": "confidential",
                "department": "Trade Services",
                "version": "v4.2",
                "allowed_roles": ["LOAN_OFFICER", "COMPLIANCE_OFFICER", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Locker_Operations_and_Deceased_Claim_Settlement_Directive.txt",
                "document_name": "Safe Deposit Lockers & Deceased Depositor Settlement Directive",
                "document_type": "branch_sop",
                "classification": "internal",
                "department": "Branch Banking",
                "version": "v3.0",
                "allowed_roles": ["CUSTOMER_SUPPORT", "MANAGER", "ADMIN"],
            },
            {
                "file_name": "Treasury_Derivatives_and_Interest_Rate_Risk_Policy.txt",
                "document_name": "Treasury Derivatives & Market Risk Management Policy",
                "document_type": "treasury_policy",
                "classification": "confidential",
                "department": "Treasury & Risk",
                "version": "v2.9",
                "allowed_roles": ["MANAGER", "ADMIN"],
            },
        ]

        admin_user = created_users.get("admin@bankassist.ai")

        for meta in sample_documents_meta:
            src_path = os.path.join(sample_docs_dir, meta["file_name"])
            if not os.path.exists(src_path):
                logger.warning(f"Sample file {src_path} not found. Skipping.")
                continue

            dest_path = os.path.join(uploads_dir, meta["file_name"])
            shutil.copyfile(src_path, dest_path)

            doc = db.query(Document).filter(Document.document_name == meta["document_name"]).first()
            if not doc:
                doc = Document(
                    document_name=meta["document_name"],
                    document_type=meta["document_type"],
                    classification=meta["classification"],
                    department=meta["department"],
                    version=meta["version"],
                    file_path=dest_path,
                    status="PENDING",
                    uploaded_by=admin_user.id if admin_user else None
                )
                for rname in meta["allowed_roles"]:
                    if rname in roles_map:
                        doc.allowed_roles.append(roles_map[rname])
                db.add(doc)
                db.commit()
                db.refresh(doc)
                logger.info(f"Created Document record: {doc.document_name}")

            # Trigger indexing into ChromaDB
            try:
                chunks_indexed = DocumentIngestionService.ingest_document(db, doc.id)
                logger.info(f"Indexed {chunks_indexed} chunks for '{doc.document_name}'.")
            except Exception as e:
                logger.error(f"Error indexing {doc.document_name}: {e}")

        # 4. Log Seed Completion
        AuditService.log_event(
            db=db,
            event_type="SYSTEM_INITIALIZED",
            event_status="SUCCESS",
            user_id=admin_user.id if admin_user else None,
            details={"message": "Database and sample banking documents seeded successfully."}
        )

        logger.info("BankAssist AI Seed Process Completed Successfully!")
        print("\n=======================================================")
        print("  BANKASSIST AI SEEDED SUCCESSFULLY")
        print("=======================================================")
        print("  Default Logins:")
        print("  - Admin:        admin@bankassist.ai        / Admin@123456")
        print("  - Loan Officer: loan.officer@bankassist.ai / Loan@123456")
        print("  - Compliance:   compliance@bankassist.ai   / Compliance@123456")
        print("  - Support:      support@bankassist.ai      / Support@123456")
        print("  - Manager:      manager@bankassist.ai      / Manager@123456")
        print("=======================================================\n")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
