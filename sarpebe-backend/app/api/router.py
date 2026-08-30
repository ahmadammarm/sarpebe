from fastapi import APIRouter
from app.api.routers.users import router as users_router
from app.api.routers.lesson_plans import router as lesson_plans_router
from app.api.routers.curriculum import router as curriculum_router

api_router = APIRouter(prefix="/api")

api_router.include_router(users_router)
api_router.include_router(lesson_plans_router)
api_router.include_router(curriculum_router)
