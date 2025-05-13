from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from ...core.supabase import get_supabase_client
from ...models.location import LocationInDB
from ...models.category import CategoryInDB
from ...models.user import UserResponse
from ...schemas.response import APIResponse, ErrorDetail
from ..v1.auth import get_current_user

router = APIRouter()

@router.get("/locations", response_model=APIResponse[List[LocationInDB]])
async def get_locations():
    try:
        supabase = get_supabase_client()
        result = supabase.table("locations").select("*").order("name").execute()
        
        if not result.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="No locations found"
                )
            )
        
        return APIResponse(
            success=True,
            data=[LocationInDB(**location) for location in result.data]
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="FETCH_ERROR",
                message=str(e)
            )
        )

@router.get("/categories", response_model=APIResponse[List[CategoryInDB]])
async def get_categories():
    try:
        supabase = get_supabase_client()
        result = supabase.table("categories").select("*").order("name").execute()
        
        if not result.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="No categories found"
                )
            )
        
        return APIResponse(
            success=True,
            data=[CategoryInDB(**category) for category in result.data]
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="FETCH_ERROR",
                message=str(e)
            )
        )

@router.get("/workers/search", response_model=APIResponse[List[UserResponse]])
async def search_workers(
    category_id: str = Query(..., description="Category ID"),
    location_id: str = Query(..., description="Location ID"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Search for available workers by category and location.
    Only returns verified workers that match the specified category and location.
    """
    try:
        # Verify current user is a client
        if current_user.role != "client":
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="UNAUTHORIZED",
                    message="Only clients can search for workers"
                )
            )
        
        supabase = get_supabase_client()
        
        # Verify category exists
        category = supabase.table("categories").select("id").eq("id", category_id).execute()
        if not category.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="INVALID_CATEGORY",
                    message="Category not found"
                )
            )
        
        # Verify location exists
        location = supabase.table("locations").select("id").eq("id", location_id).execute()
        if not location.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="INVALID_LOCATION",
                    message="Location not found"
                )
            )
        
        # Search for workers matching criteria
        workers = supabase.table("users").select("*").eq("role", "worker").eq("category_id", category_id).eq("location_id", location_id).eq("is_verified", True).execute()
        
        if not workers.data:
            return APIResponse(
                success=True,
                data=[]  # Return empty list instead of error
            )
        
        return APIResponse(
            success=True,
            data=[UserResponse(**worker) for worker in workers.data]
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="SEARCH_ERROR",
                message=str(e)
            )
        ) 