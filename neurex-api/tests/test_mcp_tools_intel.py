
import pytest

from core.mcp.tools.intel import (
    audit_codebase_health,
    check_design_compliance,
    query_project_intel,
    synthesize_project_intel,
)


@pytest.fixture
def mock_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr("core.mcp.tools.intel.WORKSPACE_PATH", str(tmp_path))
    return tmp_path

@pytest.mark.asyncio
async def test_synthesize_project_intel(mock_workspace):
    (mock_workspace / "package.json").touch()
    (mock_workspace / "requirements.txt").touch()
    (mock_workspace / "README.md").write_text("we use fastapi and react and sqlite.")
    
    res = await synthesize_project_intel()
    
    intel_file = mock_workspace / ".neurex" / "intel.json"
    assert intel_file.exists()
    assert "FastAPI/REST" in res
    assert "React/Frontend" in res
    assert "TypeScript/Node.js" in res

@pytest.mark.asyncio
async def test_query_project_intel(mock_workspace):
    res1 = await query_project_intel()
    assert "No project intelligence found" in res1
    
    intel_dir = mock_workspace / ".neurex"
    intel_dir.mkdir()
    (intel_dir / "intel.json").write_text('{"project_name": "test"}')
    
    res2 = await query_project_intel()
    assert "test" in res2

@pytest.mark.asyncio
async def test_audit_codebase_health(mock_workspace):
    res = await audit_codebase_health()
    assert "documentation_drift" in res
    assert "Create a CHANGELOG.md" in res
    
    (mock_workspace / "CHANGELOG.md").touch()
    (mock_workspace / "neurex-api").mkdir()
    (mock_workspace / "neurex-api" / "node_modules").mkdir()
    
    res2 = await audit_codebase_health()
    assert "Audit required" in res2
    assert "Found node_modules in API" in res2

@pytest.mark.asyncio
async def test_check_design_compliance(mock_workspace):
    res1 = await check_design_compliance("missing.css")
    assert "not found" in res1
    
    css = mock_workspace / "style.css"
    css.write_text(".test { color: #ff0000; }")
    res2 = await check_design_compliance("style.css")
    assert "Hardcoded hex" in res2
    assert "No glassmorphism tokens" in res2
    
    tsx = mock_workspace / "App.tsx"
    tsx.write_text("function App() { return <div className='myClass'></div> }")
    res3 = await check_design_compliance("App.tsx")
    assert "BEM naming convention" in res3
    
    css_good = mock_workspace / "good.css"
    css_good.write_text(".glass { backdrop-filter: blur(10px); }")
    res4 = await check_design_compliance("good.css")
    assert "✅ Pass" in res4
