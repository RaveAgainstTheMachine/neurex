from unittest.mock import AsyncMock, patch

import pytest

from core.mcp.tools.security import security_scan


@pytest.mark.asyncio
async def test_security_scan_no_issues():
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_exec.return_value = mock_proc
        
        res = await security_scan()
        assert "No immediate threats detected" in res

@pytest.mark.asyncio
async def test_security_scan_with_issues():
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        def side_effect(*args, **kwargs):
            mock_proc = AsyncMock()
            if args[0] == "bandit":
                mock_proc.communicate.return_value = (b"Issue: High severity", b"")
            elif args[0] == "safety":
                mock_proc.communicate.return_value = (b"2 vulnerabilities found", b"")
            elif args[0] == "git":
                mock_proc.communicate.return_value = (b".env\nsecret.pem", b"")
            return mock_proc
            
        mock_exec.side_effect = side_effect
        
        res = await security_scan()
        assert "Bandit found" in res
        assert "Safety found" in res
        assert "Sensitive files" in res

@pytest.mark.asyncio
async def test_security_scan_exception():
    with patch("asyncio.create_subprocess_exec", side_effect=Exception("failed")):
        res = await security_scan()
        assert "No immediate threats detected" in res
