from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse


router = APIRouter()
FRONTEND_INDEX = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "index.html"


@router.api_route("/api", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
@router.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def unknown_api(path: str = "") -> None:
    # Unknown API paths must not fall through to the SPA's index.html.
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy API này.")


@router.get("/", include_in_schema=False)
@router.get("/{path:path}", include_in_schema=False)
async def frontend(path: str = "") -> FileResponse:
    if not FRONTEND_INDEX.is_file():
        raise HTTPException(
            status_code=503,
            detail="React frontend has not been built. Run npm run build in the frontend directory.",
        )
    return FileResponse(FRONTEND_INDEX)
