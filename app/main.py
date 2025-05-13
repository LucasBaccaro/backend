from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.api.v1 import auth, references, services, ws_chat
from app.core.config import get_settings
from app.middleware.error_handler import validation_exception_handler, http_exception_handler
from app.schemas.response import APIResponse

settings = get_settings()

app = FastAPI(
    title="Services API",
    description="API for services between workers and clients",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(references.router, prefix="/api/v1/references", tags=["references"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])
app.include_router(ws_chat.router)  # Sin prefijo para WebSocket - la ruta ya está completa en el router

@app.get("/")
async def root():
    return APIResponse(
        success=True,
        data={"message": "Welcome to Services API"}
    )

@app.get("/health")
async def health_check():
    return APIResponse(
        success=True,
        data={"status": "healthy"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 