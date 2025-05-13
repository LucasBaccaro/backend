from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from ..schemas.response import APIResponse, ErrorDetail

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors consistently"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=APIResponse(
            success=False,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Validation error",
                details=errors
            )
        ).model_dump()
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions consistently"""
    error_code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        error_code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        error_code = "FORBIDDEN"
    
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            error=ErrorDetail(
                code=error_code,
                message=str(exc.detail)
            )
        ).model_dump()
    ) 