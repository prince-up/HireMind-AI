from fastapi import FastAPI
from .routers import interview, upload


app = FastAPI(
    title="HireMind AI"
)

# Allow CORS from frontend dev
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "HireMind AI Backend Running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(interview.router)
app.include_router(upload.router)