from fastapi import APIRouter

router = APIRouter(
    prefix="/negro",
    tags=["negro"],
    responses={404:{"description":"Not Found"}}
)

@router.get("/")
async def read_users():
    return {"",""}