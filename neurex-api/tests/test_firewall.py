from unittest.mock import AsyncMock, patch

import pytest

from core.infrastructure.firewall import (
    FirewallManager,
    PortSet,
    _local_subnet,
    get_master_ports,
)


@pytest.fixture
def firewall():
    return FirewallManager()

def test_local_subnet():
    assert _local_subnet("192.168.1.42") == "192.168.1.0/24"
    assert _local_subnet("invalid") == "0.0.0.0/0"

def test_get_master_ports():
    ports = get_master_ports(api_port=8000)
    assert 8000 in ports.ports
    assert ports.ports[8000] == "Neurex API (FastAPI)"

@pytest.mark.asyncio
async def test_apply_rules_linux(firewall):
    firewall._system = "linux"
    
    with patch("core.infrastructure.firewall._linux_apply", AsyncMock(return_value=["ufw allow"])) as mock_apply:
        res = await firewall.apply_rules(role="master", bind_ip="192.168.1.100")
        assert res["platform"] == "Linux/ufw"
        assert res["rules_applied"] == ["ufw allow"]
        mock_apply.assert_called_once()

@pytest.mark.asyncio
async def test_apply_rules_macos(firewall):
    firewall._system = "darwin"
    
    with patch("core.infrastructure.firewall._macos_apply", AsyncMock(return_value=["pf pass"])) as mock_apply:
        res = await firewall.apply_rules(role="node", bind_ip="0.0.0.0")
        assert res["platform"] == "macOS/pf"
        assert res["rules_applied"] == ["pf pass"]
        mock_apply.assert_called_once()

@pytest.mark.asyncio
async def test_apply_rules_windows(firewall):
    firewall._system = "windows"
    
    with patch("core.infrastructure.firewall._windows_apply", AsyncMock(return_value=["netsh allow"])) as mock_apply:
        res = await firewall.apply_rules(role="master")
        assert res["platform"] == "Windows/netsh"
        assert res["rules_applied"] == ["netsh allow"]
        mock_apply.assert_called_once()

@pytest.mark.asyncio
async def test_check_integrity_linux(firewall):
    firewall._system = "linux"
    
    with patch("core.infrastructure.firewall._run", AsyncMock(return_value=(0, "8000/tcp allow from 192.168.1.0/24"))):
        port_set = PortSet(ports={8000: "API"}, allow_from="192.168.1.0/24", proto="tcp")
        res = await firewall.check_integrity("master", "192.168.1.100", port_set)
        assert res is True

@pytest.mark.asyncio
async def test_check_integrity_macos(firewall):
    firewall._system = "darwin"
    
    with patch("core.infrastructure.firewall._run", AsyncMock(return_value=(0, "pass in quick proto tcp from any to any port 8000"))):
        port_set = PortSet(ports={8000: "API"}, allow_from="0.0.0.0/0", proto="tcp")
        res = await firewall.check_integrity("master", "0.0.0.0", port_set)
        assert res is True

@pytest.mark.asyncio
async def test_linux_apply_internals():
    port_set = PortSet(ports={8000: "API"}, allow_from="0.0.0.0/0", proto="tcp")
    
    from core.infrastructure.firewall import _linux_apply
    
    with patch("core.infrastructure.firewall._ufw_available", AsyncMock(return_value=True)):
        with patch("core.infrastructure.firewall._linux_remove_rules", AsyncMock()):
            with patch("core.infrastructure.firewall._run", AsyncMock(return_value=(0, ""))) as mock_run:
                applied = await _linux_apply(port_set, "0.0.0.0")
                assert len(applied) == 1
                assert mock_run.call_count == 2 # 1 for port, 1 for enable
