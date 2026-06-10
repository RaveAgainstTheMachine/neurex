# neurex-api/api/routes/languages.py

from fastapi import APIRouter, Depends, HTTPException

from core.languages.lsp_manager import LSP_RECIPES, lsp_manager

from .auth import get_current_user

router = APIRouter()


@router.get("/supported")
async def get_supported():
    """Returns languages that have a detected LSP binary."""
    return {"languages": lsp_manager.get_supported_languages()}


@router.get("/installable")
async def get_installable():
    """Returns languages that have an installation recipe."""
    return {"languages": list(LSP_RECIPES.keys())}


@router.post("/install/{lang}")
async def install_language(lang: str, user=Depends(get_current_user)):
    """Triggers the automated installation of an LSP for the given language."""
    if lang not in LSP_RECIPES:
        raise HTTPException(status_code=400, detail=f"No installation recipe for {lang}")

    try:
        await lsp_manager.install_lsp(lang)
        return {"status": "ok", "message": f"Successfully installed {lang} support"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
