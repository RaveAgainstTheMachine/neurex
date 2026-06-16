import os

from core.context.skeptical_memory import SkepticalMemory


def test_skeptical_memory_lifecycle(tmp_path):
    ws_path = str(tmp_path)
    sm = SkepticalMemory(ws_path)
    
    # Initially memory file doesn't exist
    assert sm.get_memory() == ""
    
    # Update memory
    sm.update_memory("This is a sticky note.")
    memory_content = sm.get_memory()
    assert "This is a sticky note." in memory_content
    assert "## NEUREX AGENT MEMORY" in memory_content

    # Check skeptical instruction
    instruction = sm.get_skeptical_instruction()
    assert "SKEPTICAL EXECUTION ENABLED" in instruction

def test_skeptical_memory_read_failure(tmp_path):
    ws_path = str(tmp_path)
    sm = SkepticalMemory(ws_path)
    
    # Create the directory structure but make MEMORY.md a directory to force an OSError
    os.makedirs(os.path.join(ws_path, ".neurex"), exist_ok=True)
    os.makedirs(sm.memory_file, exist_ok=True)
    
    assert sm.get_memory() == ""
