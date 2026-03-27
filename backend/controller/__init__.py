from fastapi import APIRouter

from .blog import router as blog_router
from .translate import router as translate_router

router = APIRouter()
router.include_router(translate_router)
router.include_router(blog_router)

__all__ = ['router']
