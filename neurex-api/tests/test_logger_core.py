import json
from unittest.mock import patch

from core.logger import get_audit_logs, setup_logging


def test_get_audit_logs_not_exist(tmp_path):
    mock_log_file = tmp_path / "nonexistent.jsonl"
    with patch("core.logger.LOG_FILE", mock_log_file):
        logs = get_audit_logs()
        assert logs == []

def test_get_audit_logs_exist(tmp_path):
    mock_log_file = tmp_path / "audit.jsonl"
    
    # Write some valid and invalid JSON lines
    valid_log_1 = {"timestamp": "2026-06-16T10:00:00Z", "level": "info", "event": "start", "user_id": "u1", "ip_address": "127.0.0.1"}
    valid_log_2 = {"timestamp": "2026-06-16T10:05:00Z", "level": "warn", "event": "warning"}
    invalid_line = "not a json line"
    
    with open(mock_log_file, "w") as f:
        f.write(json.dumps(valid_log_1) + "\n")
        f.write(invalid_line + "\n")
        f.write(json.dumps(valid_log_2) + "\n")
        f.write("\n") # empty line
        
    with patch("core.logger.LOG_FILE", mock_log_file):
        logs = get_audit_logs(limit=10)
        # Should be returned in reverse order: log_2 first, then log_1 (invalid/empty ignored)
        assert len(logs) == 2
        assert logs[0]["event"] == "warning"
        assert logs[0]["level"] == "WARN"
        assert logs[1]["event"] == "start"
        assert logs[1]["level"] == "INFO"
        assert logs[1]["user_id"] == "u1"
        assert logs[1]["ip_address"] == "127.0.0.1"

def test_setup_logging(tmp_path):
    mock_log_file = tmp_path / "audit.jsonl"
    with patch("core.logger.LOG_FILE", mock_log_file):
        with patch("structlog.configure") as mock_configure:
            setup_logging()
            mock_configure.assert_called_once()
            assert mock_log_file.parent.exists()
