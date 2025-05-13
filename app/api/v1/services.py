from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List
from ...core.supabase import get_supabase_client
from ...models.service_request import ServiceRequestCreate, ServiceRequestResponse, ServiceRequestStatus
from ...models.user import UserResponse, UserRole
from ...schemas.response import APIResponse, ErrorDetail
from ..v1.auth import get_current_user
from ...models.rating import ServiceRatingCreate

router = APIRouter()

@router.post("/request", response_model=APIResponse[ServiceRequestResponse])
async def create_service_request(
    request_data: ServiceRequestCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Client creates a service request for a worker"""
    if current_user.role != UserRole.CLIENT:
        return APIResponse(
            success=False, 
            error=ErrorDetail(
                code="UNAUTHORIZED", 
                message="Only clients can create service requests"
            )
        )
    try:
        supabase = get_supabase_client()
        # Insert request
        insert_data = {
            "client_id": current_user.id,
            "worker_id": request_data.worker_id,
            "description": request_data.description,
            "status": ServiceRequestStatus.pending.value
        }
        result = supabase.table("service_requests").insert(insert_data).execute()
        if not result.data:
            return APIResponse(
                success=False, 
                error=ErrorDetail(
                    code="CREATE_ERROR", 
                    message="Failed to create service request"
                )
            )
        return APIResponse(success=True, data=ServiceRequestResponse(**result.data[0]))
    except Exception as e:
        return APIResponse(
            success=False, 
            error=ErrorDetail(
                code="CREATE_ERROR", 
                message=str(e)
            )
        )

@router.get("/requests", response_model=APIResponse[List[ServiceRequestResponse]])
async def list_service_requests(current_user: UserResponse = Depends(get_current_user)):
    """Worker views their service requests"""
    if current_user.role != UserRole.WORKER:
        return APIResponse(
            success=False, 
            error=ErrorDetail(
                code="UNAUTHORIZED", 
                message="Only workers can view their service requests"
            )
        )
    try:
        supabase = get_supabase_client()
        result = supabase.table("service_requests").select("*").eq("worker_id", current_user.id).order("created_at", desc=True).execute()
        if not result.data:
            return APIResponse(success=True, data=[])
        return APIResponse(success=True, data=[ServiceRequestResponse(**req) for req in result.data])
    except Exception as e:
        return APIResponse(
            success=False, 
            error=ErrorDetail(
                code="FETCH_ERROR", 
                message=str(e)
            )
        )

@router.post("/request/{request_id}/action", response_model=APIResponse[ServiceRequestResponse])
async def action_service_request(
    request_id: str,
    action: str = Body(..., embed=True, description="Action: accept, reject, cancel"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Worker accepts/rejects/cancels a request"""
    if current_user.role != UserRole.WORKER:
        return APIResponse(
            success=False, 
            error=ErrorDetail(
                code="UNAUTHORIZED", 
                message="Only workers can modify service requests"
            )
        )
    if action not in [ServiceRequestStatus.accepted, ServiceRequestStatus.rejected, ServiceRequestStatus.cancelled, ServiceRequestStatus.completed]:
        return APIResponse(
            success=False, 
            error=ErrorDetail(
                code="INVALID_ACTION", 
                message="Invalid action"
            )
        )
    try:
        supabase = get_supabase_client()
        # Find request and verify ownership
        req = supabase.table("service_requests").select("*").eq("id", request_id).eq("worker_id", current_user.id).single().execute()
        if not req.data:
            return APIResponse(
                success=False, 
                error=ErrorDetail(
                    code="NOT_FOUND", 
                    message="Service request not found"
                )
            )
        # Update status
        updated = supabase.table("service_requests").update({"status": action}).eq("id", request_id).execute()
        if not updated.data:
            return APIResponse(
                success=False, 
                error=ErrorDetail(
                    code="UPDATE_ERROR", 
                    message="Failed to update service request"
                )
            )
        return APIResponse(success=True, data=ServiceRequestResponse(**updated.data[0]))
    except Exception as e:
        return APIResponse(
            success=False, 
            error=ErrorDetail(
                code="ACTION_ERROR", 
                message=str(e)
            )
        )

@router.post("/request/{service_request_id}/rate", response_model=APIResponse[dict])
async def rate_worker(
    service_request_id: str,
    rating_data: ServiceRatingCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Client rates a worker for a completed service and updates worker's average rating"""
    try:
        supabase = get_supabase_client()
        # Get service request
        req = supabase.table("service_requests").select("*").eq("id", service_request_id).single().execute()
        if not req.data:
            return APIResponse(
                success=False, 
                error=ErrorDetail(
                    code="NOT_FOUND", 
                    message="Service request not found"
                )
            )
        if req.data["status"] != "completed":
            return APIResponse(
                success=False, 
                error=ErrorDetail(
                    code="INVALID_STATUS", 
                    message="Can only rate completed services"
                )
            )
        if req.data["client_id"] != current_user.id:
            return APIResponse(
                success=False, 
                error=ErrorDetail(
                    code="FORBIDDEN", 
                    message="Only the client can rate the service"
                )
            )
        worker_id = req.data["worker_id"]
        client_id = req.data["client_id"]
        # Check if rating already exists
        existing = supabase.table("service_ratings").select("id").eq("service_request_id", service_request_id).eq("client_id", client_id).execute()
        if existing.data:
            return APIResponse(
                success=False, 
                error=ErrorDetail(
                    code="ALREADY_RATED", 
                    message="Service already rated"
                )
            )
        # Insert rating
        supabase.table("service_ratings").insert({
            "service_request_id": service_request_id,
            "worker_id": worker_id,
            "client_id": client_id,
            "rating": rating_data.rating
        }).execute()
        # Calculate new average and count
        ratings = supabase.table("service_ratings").select("rating").eq("worker_id", worker_id).execute()
        ratings_list = [r["rating"] for r in ratings.data] if ratings.data else []
        avg = sum(ratings_list) / len(ratings_list) if ratings_list else 0
        count = len(ratings_list)
        # Update worker
        supabase.table("users").update({"average_rating": avg, "ratings_count": count}).eq("id", worker_id).execute()
        return APIResponse(
            success=True, 
            data={
                "average_rating": avg, 
                "ratings_count": count
            }
        )
    except Exception as e:
        return APIResponse(
            success=False, 
            error=ErrorDetail(
                code="RATING_ERROR", 
                message=str(e)
            )
        ) 