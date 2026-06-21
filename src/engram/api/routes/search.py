from __future__ import annotations

from fastapi import APIRouter, Depends

from engram.api.deps import AppState, get_state
from engram.models.entities import EntityFilter
from engram.models.search import SearchQuery, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def hybrid_search(body: SearchQuery, state: AppState = Depends(get_state)):
    return state.hybrid_search.search(body)


@router.get("/search/file/{file_path:path}")
def search_by_file(file_path: str, state: AppState = Depends(get_state)):
    filt = EntityFilter(file_path=file_path)
    return state.entity_store.list(filt)
