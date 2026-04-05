from app.routers.auth import router as auth_router
from app.routers.reports import router as reports_router
from app.routers.uploads import router as uploads_router
from app.routers.users import router as users_router
from app.routers.votes import router as votes_router

__all__ = ["auth_router", "reports_router", "votes_router", "users_router", "uploads_router"]
