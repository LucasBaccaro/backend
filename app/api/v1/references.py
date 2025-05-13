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
    category_id: str = Query(..., description="ID de la categoría"),
    location_id: str = Query(..., description="ID de la ubicación"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Busca trabajadores disponibles por categoría y ubicación.
    Solo retorna trabajadores verificados que coincidan con la categoría y ubicación especificadas.
    """
    try:
        # Verificar que el usuario actual es un cliente
        if current_user.role != "client":
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="UNAUTHORIZED",
                    message="Solo los clientes pueden buscar trabajadores"
                )
            )
        
        supabase = get_supabase_client()
        
        # Verificar que la categoría existe
        category = supabase.table("categories").select("id").eq("id", category_id).execute()
        if not category.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="INVALID_CATEGORY",
                    message="Categoría no encontrada"
                )
            )
        
        # Verificar que la ubicación existe
        location = supabase.table("locations").select("id").eq("id", location_id).execute()
        if not location.data:
            return APIResponse(
                success=False,
                error=ErrorDetail(
                    code="INVALID_LOCATION",
                    message="Ubicación no encontrada"
                )
            )
        
        # Primero, veamos cuántos trabajadores hay en total
        all_workers = supabase.table("users").select("*").eq("role", "worker").execute()
        print(f"Total de trabajadores: {len(all_workers.data)}")
        
        # Luego, veamos cuántos hay por cada criterio
        workers_by_category = supabase.table("users").select("*").eq("role", "worker").eq("category_id", category_id).execute()
        print(f"Trabajadores en categoría {category_id}: {len(workers_by_category.data)}")
        
        workers_by_location = supabase.table("users").select("*").eq("role", "worker").eq("location_id", location_id).execute()
        print(f"Trabajadores en ubicación {location_id}: {len(workers_by_location.data)}")
        
        workers_verified = supabase.table("users").select("*").eq("role", "worker").eq("is_verified", True).execute()
        print(f"Trabajadores verificados: {len(workers_verified.data)}")
        
        # Buscar trabajadores que coincidan con los criterios
        workers = supabase.table("users").select("*").eq("role", "worker").eq("category_id", category_id).eq("location_id", location_id).eq("is_verified", True).execute()
        print(f"Trabajadores que cumplen todos los criterios: {len(workers.data)}")
        
        if workers.data:
            print("Ejemplo de trabajador encontrado:", workers.data[0])
        
        if not workers.data:
            return APIResponse(
                success=True,
                data=[]  # Retornar lista vacía en lugar de error
            )
        
        return APIResponse(
            success=True,
            data=[UserResponse(**worker) for worker in workers.data]
        )
        
    except Exception as e:
        print(f"Error en búsqueda de trabajadores: {str(e)}")
        return APIResponse(
            success=False,
            error=ErrorDetail(
                code="SEARCH_ERROR",
                message=str(e)
            )
        ) 