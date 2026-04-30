from fastapi import APIRouter

from .billing import router as billing_router
from .blog import router as blog_router
from .chat import router as chat_router
from .translate import router as translate_router

router = APIRouter()
router.include_router(translate_router)
router.include_router(blog_router)
router.include_router(chat_router)
router.include_router(billing_router)

__all__ = ['router']
