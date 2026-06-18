from fastapi import APIRouter
 
router = APIRouter(
    prefix="/peruano",
    tags=["peruano"],
    responses={404: {"description": "Not Found"}}
)

@router.get("/")
async def read_users():
    return [{"username": "Rick"}]


