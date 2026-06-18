from fastapi import Depends,FastAPI
from .routers import bayo, peruano, negro
app = FastAPI()


#Agrego los router para cada tipo de frijol
app.include_router(peruano.router)
app.include_router(bayo.router)
app.include_router(negro.router)

@app.get("/")
async def root():
    return {"message":"Hello Bigger App"}