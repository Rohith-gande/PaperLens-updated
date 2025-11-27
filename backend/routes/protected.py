from fastapi import APIRouter, Depends
from auth.firebase_auth import verify_token

router = APIRouter()

@router.get('/me')
async def me(decoded=Depends(verify_token)):
    """
    Endpoint to verify the token and return user information.
    """
    return {"message": "Hello from protected endpoint", "user": decoded}

