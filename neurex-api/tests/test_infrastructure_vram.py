from unittest.mock import MagicMock, patch

from core.infrastructure.manager import InfrastructureManager


def test_get_system_vram_nvidia():
    mgr = InfrastructureManager()
    with patch("subprocess.run") as mock_run:
        mock_res = MagicMock()
        mock_res.stdout = "8192\n4096\n"
        mock_res.returncode = 0
        mock_run.return_value = mock_res
        
        vram = mgr.get_system_vram()
        # 12288 MB = 12 GB
        assert vram == 12.0

def test_get_system_vram_amd_sysfs():
    mgr = InfrastructureManager()
    with patch("subprocess.run", side_effect=Exception("no nvidia")):
        with patch("glob.glob", return_value=["/sys/class/drm/card0/device/mem_info_vram_total"]):
            with patch("builtins.open") as mock_open:
                mock_file = MagicMock()
                # 8 GB in bytes
                mock_file.read.return_value = str(8 * 1024 * 1024 * 1024)
                mock_open.return_value.__enter__.return_value = mock_file
                
                vram = mgr.get_system_vram()
                assert vram == 8.0

def test_get_system_vram_amd_rocm():
    mgr = InfrastructureManager()
    with patch("subprocess.run") as mock_run:
        def side_effect(*args, **kwargs):
            if "nvidia-smi" in args[0]:
                raise Exception("no nvidia")
            if "rocm-smi" in args[0]:
                mock_res = MagicMock()
                # matches r"VRAM:\s*\d+\s*\(Used\)\s*/\s*(\d+)\s*\(Total\)"
                mock_res.stdout = "VRAM: 1000 (Used) / 17179869184 (Total)"
                mock_res.returncode = 0
                return mock_res
            raise Exception("unknown")
        mock_run.side_effect = side_effect
        
        with patch("glob.glob", return_value=[]):
            vram = mgr.get_system_vram()
            assert vram == 16.0

def test_get_system_vram_intel():
    mgr = InfrastructureManager()
    with patch("subprocess.run") as mock_run:
        def side_effect(*args, **kwargs):
            if "nvidia-smi" in args[0]:
                raise Exception("no nvidia")
            if "rocm-smi" in args[0]:
                raise Exception("no amd")
            if "xpu-smi" in args[0]:
                mock_res = MagicMock()
                mock_res.stdout = "Memory Size: 16.00 GB"
                mock_res.returncode = 0
                return mock_res
            raise Exception("unknown")
        mock_run.side_effect = side_effect
        
        with patch("glob.glob", return_value=[]):
            vram = mgr.get_system_vram()
            assert vram == 16.0

def test_get_system_vram_mac_unified():
    mgr = InfrastructureManager()
    with patch("sys.platform", "darwin"):
        with patch("subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if "system_profiler" in cmd:
                    raise Exception("no profiler")
                if "sysctl" in cmd:
                    if "hw.memsize" in cmd:
                        mock_res = MagicMock()
                        mock_res.stdout = str(16 * 1024 * 1024 * 1024)
                        mock_res.returncode = 0
                        return mock_res
                    if "machdep.cpu.brand_string" in cmd:
                        mock_res = MagicMock()
                        mock_res.stdout = "Apple M1"
                        mock_res.returncode = 0
                        return mock_res
                raise Exception("unknown")
            mock_run.side_effect = side_effect
            
            with patch("glob.glob", return_value=[]):
                vram = mgr.get_system_vram()
                # 16 GB * 0.75 = 12.0 GB
                assert vram == 12.0

def test_get_system_vram_fallback():
    mgr = InfrastructureManager()
    with patch("subprocess.run", side_effect=Exception("no tools")):
        with patch("glob.glob", return_value=[]):
            vram = mgr.get_system_vram()
            assert vram == 0.0
