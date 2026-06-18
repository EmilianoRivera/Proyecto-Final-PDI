from fastapi import APIRouter

router = APIRouter(
    prefix="/bayo",
    tags=["bayo"],
    responses={404: {"description":"Not Found"}}
)

@router.get("/")
async def read_users():
    return {"":""}
