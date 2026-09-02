import os
import sys
import uvicorn
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from seed_data import seed_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bankassist.runner")

if __name__ == "__main__":
    print("==================================================================")
    print("        STARTING BANKASSIST AI - PRODUCTION PLATFORM              ")
    print("==================================================================")
    
    # Run auto-seed
    try:
        seed_database()
    except Exception as e:
        logger.warning(f"Seed step encountered note: {e}")

    print("\n[INFO] Starting Uvicorn server on http://localhost:8000 ...")
    print("[INFO] Web Application Portal: http://localhost:8000")
    print("[INFO] Swagger API Docs:       http://localhost:8000/docs\n")

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
