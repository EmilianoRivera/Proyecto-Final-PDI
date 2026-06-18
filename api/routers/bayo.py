from fastapi import APIRouter, File, UploadFile, Response
from typing import Annotated
from ..proccesing.negros_process import procesar_mi_imagen 


router = APIRouter(
    prefix="/v1/bayo",
    tags=["bayo"],
    responses={404: {"description":"Not Found"},
               422: {"description": "Unprocessable Content"}}
)

#endpoint de prueba
@router.get("/", description="Este endpoint no hace nada, solo es de prueba.")
async def read_users():
    return {"message","Endpoint de prueba"}

#endpoint para subir la imagen
@router.post("/process-image/", description="Este endpoint es para subir la imagen")
async def create_upload_file(file: UploadFile = File(...)):
    if not file:
        return {"message": "No upload file sent"}
    else:
        bytes_originales = await file.read()
        bytes_procesados = procesar_mi_imagen(bytes_originales)
        return Response(content=bytes_procesados, media_type="image/png")
