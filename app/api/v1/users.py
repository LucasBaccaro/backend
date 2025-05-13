from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from ...core.supabase import get_supabase_client
from ...models.user import UserResponse, UserUpdate
from ...schemas.response import APIResponse, ErrorDetail
from ..v1.auth import get_current_user

router = APIRouter()

@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current user information.
    """
    try:
        return APIResponse(
            success=True,
            data=current_user
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="FETCH_ERROR",
                message=str(e)
            )
        )

@router.put("/me", response_model=APIResponse[UserResponse])
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update current user information.
    """
    try:
        supabase = get_supabase_client()
        
        # Update user data
        result = supabase.table("users").update(user_update.dict(exclude_unset=True)).eq("id", current_user.id).execute()
        
        if not result.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="UPDATE_ERROR",
                    message="Failed to update user information"
                )
            )
        
        return APIResponse(
            success=True,
            data=UserResponse(**result.data[0])
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="UPDATE_ERROR",
                message=str(e)
            )
        )

@router.get("/workers", response_model=APIResponse[List[UserResponse]])
async def list_workers(
    current_user: UserResponse = Depends(get_current_user),
    category_id: Optional[str] = None,
    location_id: Optional[str] = None
):
    """
    List all verified workers, optionally filtered by category and location.
    """
    try:
        # Verify current user is a client
        if current_user.role != "client":
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="UNAUTHORIZED",
                    message="Only clients can list workers"
                )
            )
        
        supabase = get_supabase_client()
        query = supabase.table("users").select("*").eq("role", "worker").eq("is_verified", True)
        
        # Apply filters if provided
        if category_id:
            query = query.eq("category_id", category_id)
        if location_id:
            query = query.eq("location_id", location_id)
        
        result = query.execute()
        
        if not result.data:
            return APIResponse(
                success=True,
                data=[]  # Return empty list instead of error
            )
        
        return APIResponse(
            success=True,
            data=[UserResponse(**worker) for worker in result.data]
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="FETCH_ERROR",
                message=str(e)
            )
        ) 