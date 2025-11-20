import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

# Initialize Firebase Admin SDK
cred_path = os.getenv('FIREBASE_CRED_PATH', './serviceAccountKey.json')
#cred_path='./serviceAccountKey.json'
firebase_initialized = False

if not firebase_admin._apps:
    try:
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
            print("✓ Firebase Admin SDK initialized successfully")
        else:
            print(f"⚠ Warning: Firebase credentials not found at {cred_path}")
            print("  Firebase authentication will be disabled")
    except Exception as e:
        print(f"⚠ Warning: Failed to initialize Firebase: {str(e)}")
        print("  Firebase authentication will be disabled")

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verifies the Firebase token and returns the decoded user information.
    """
    if not firebase_initialized:
        # For development: return a mock user if Firebase is not initialized
        print("⚠ Warning: Using mock authentication (Firebase not initialized)")
        return {"uid": "mock_user_id", "email": "mock@example.com"}
    
    token = credentials.credentials
    try:
        decoded = auth.verify_id_token(token)
        return decoded  # Return decoded token (contains uid, email, etc.)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token. {str(e)}")

