from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional
from pydantic import BaseModel

from ...core.auth import verify_password, get_password_hash, create_access_token, verify_token
from ...core.supabase import get_supabase_client, get_supabase_admin_client
from ...models.user import UserCreate, WorkerCreate, UserRole, UserResponse, ClientCreate
from ...schemas.response import APIResponse, ErrorDetail
from ...core.config import get_settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
settings = get_settings()

class LoginRequest(BaseModel):
    email: str
    password: str

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        
        supabase = get_supabase_client()
        user = supabase.table("users").select("*").eq("id", payload["sub"]).execute()
        
        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        return UserResponse(**user.data[0])
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/register/client", response_model=APIResponse[UserResponse])
async def register_client(user_data: ClientCreate):
    try:
        # Use admin client for registration
        supabase = get_supabase_admin_client()
        
        # Check if user already exists
        existing_user = supabase.table("users").select("email").eq("email", user_data.email).execute()
        if existing_user.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="USER_EXISTS",
                    message="User with this email already exists"
                )
            )
        
        # Verify location exists
        location = supabase.table("locations").select("id").eq("id", user_data.location_id).execute()
        if not location.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="INVALID_LOCATION",
                    message="Invalid location_id"
                )
            )
        
        # Create auth user (auto-confirmar email)
        auth_response = supabase.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True  # Auto-confirmar email
        })
        
        if not auth_response.user:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="AUTH_ERROR",
                    message="Failed to create authentication user"
                )
            )
        
        # Create user profile (clients don't need verification)
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["id"] = auth_response.user.id
        user_dict["is_verified"] = None  # None for clients
        
        result = supabase.table("users").insert(user_dict).execute()
        
        if not result.data:
            # Rollback auth user creation if profile creation fails
            supabase.auth.admin.delete_user(auth_response.user.id)
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="PROFILE_CREATION_ERROR",
                    message="Failed to create user profile"
                )
            )
        
        return APIResponse(
            success=True,
            data=UserResponse(**result.data[0])
        )
        
    except ValueError as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=str(e)
            )
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="REGISTRATION_ERROR",
                message=str(e)
            )
        )

@router.post("/register/worker", response_model=APIResponse[UserResponse])
async def register_worker(worker_data: WorkerCreate):
    try:
        # Use admin client for registration
        supabase = get_supabase_admin_client()
        
        # Check if user already exists
        existing_user = supabase.table("users").select("email").eq("email", worker_data.email).execute()
        if existing_user.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="USER_EXISTS",
                    message="User with this email already exists"
                )
            )
        
        # Verify location and category exist
        location = supabase.table("locations").select("id").eq("id", worker_data.location_id).execute()
        category = supabase.table("categories").select("id").eq("id", worker_data.category_id).execute()
        
        if not location.data or not category.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="INVALID_REFERENCE",
                    message="Invalid location_id or category_id"
                )
            )
        
        # Create auth user (auto-confirmar email)
        auth_response = supabase.auth.admin.create_user({
            "email": worker_data.email,
            "password": worker_data.password,
            "email_confirm": True  # Auto-confirmar email
        })
        
        if not auth_response.user:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="AUTH_ERROR",
                    message="Failed to create authentication user"
                )
            )
        
        # Create worker profile (workers empiezan sin verificar)
        worker_dict = worker_data.model_dump(exclude={"password"})
        worker_dict["id"] = auth_response.user.id
        worker_dict["is_verified"] = False  # Workers empiezan sin verificar hasta que se verifique manualmente
        
        result = supabase.table("users").insert(worker_dict).execute()
        
        if not result.data:
            # Rollback auth user creation if profile creation fails
            supabase.auth.admin.delete_user(auth_response.user.id)
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="PROFILE_CREATION_ERROR",
                    message="Failed to create worker profile"
                )
            )
        
        return APIResponse(
            success=True,
            data=UserResponse(**result.data[0])
        )
        
    except ValueError as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=str(e)
            )
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="REGISTRATION_ERROR",
                message=str(e)
            )
        )

@router.post("/login", response_model=APIResponse[dict])
async def login(request: LoginRequest):
    """Simple login endpoint that only requires email and password"""
    try:
        supabase = get_supabase_client()
        
        # Get user from auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not auth_response.user:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="INVALID_CREDENTIALS",
                    message="Invalid email or password"
                )
            )
        
        # Get user profile
        user = supabase.table("users").select("*").eq("id", auth_response.user.id).execute()
        
        if not user.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="USER_NOT_FOUND",
                    message="User profile not found"
                )
            )
        
        user_data = user.data[0]
        user_response = UserResponse(**user_data)
        
        # Check if worker needs verification
        if user_response.needs_verification:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="WORKER_NOT_VERIFIED",
                    message="Worker account is pending verification"
                )
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_data["id"], "role": user_data["role"]}
        )
        
        return APIResponse(
            success=True,
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_response
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="LOGIN_ERROR",
                message=str(e)
            )
        )

@router.post("/token", response_model=APIResponse[dict])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login, get an access token for future requests"""
    try:
        supabase = get_supabase_client()
        
        # Get user from auth (sin verificar email)
        auth_response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        if not auth_response.user:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="INVALID_CREDENTIALS",
                    message="Invalid email or password"
                )
            )
        
        # Get user profile
        user = supabase.table("users").select("*").eq("id", auth_response.user.id).execute()
        
        if not user.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="USER_NOT_FOUND",
                    message="User profile not found"
                )
            )
        
        user_data = user.data[0]
        user_response = UserResponse(**user_data)
        
        # Check if worker needs verification (solo verificamos is_verified, no el email)
        if user_response.needs_verification:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="WORKER_NOT_VERIFIED",
                    message="Worker account is pending verification"
                )
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_data["id"], "role": user_data["role"]}
        )
        
        return APIResponse(
            success=True,
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_response
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="LOGIN_ERROR",
                message=str(e)
            )
        )

@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get the current user's profile"""
    return APIResponse(
        success=True,
        data=current_user
    ) 