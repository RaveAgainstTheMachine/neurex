# neurex-api/api/routes/languages.py
from fastapi import APIRouter, Request
from core.languages.lsp_manager import lsp_manager

router = APIRouter()

@router.get("/supported")
async def get_supported_languages(request: Request):
    """Return a list of languages that have a detected LSP on the host."""
    supported = lsp_manager.get_supported_languages()
    return {"languages": supported}
