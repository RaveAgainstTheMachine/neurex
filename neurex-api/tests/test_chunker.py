from core.memory.chunker import MAX_CHUNK_CHARS, _sliding_window_chunks, _split_long, chunk_file


def test_chunk_file_prose(tmp_path):
    f = tmp_path / "doc.md"
    content = "Hello world.\n" * 10
    f.write_text(content)
    
    chunks = chunk_file(f)
    assert len(chunks) > 0
    assert "Hello world" in chunks[0]["text"]
    assert chunks[0]["metadata"]["language"] == "prose"

def test_chunk_file_python(tmp_path):
    f = tmp_path / "script.py"
    content = "def hello():\n    print('hello')\n\nclass World:\n    pass\n"
    f.write_text(content)
    
    chunks = chunk_file(f)
    assert len(chunks) > 0
    # Should chunk at function/class boundaries
    texts = [c["text"] for c in chunks]
    assert any("def hello():" in t for t in texts)
    assert any("class World:" in t for t in texts)
    assert chunks[0]["metadata"]["language"] in ["python", "prose"]

def test_sliding_window_chunks(tmp_path):
    f = tmp_path / "long.txt"
    # Create content longer than MAX_CHUNK_CHARS
    line = "a" * 100 + "\n"
    content = line * 20 # 2000 chars
    f.write_text(content)
    
    chunks = _sliding_window_chunks(content, f)
    assert len(chunks) > 1
    assert len(chunks[0]["text"]) >= MAX_CHUNK_CHARS - 100

def test_split_long():
    text = "b\n" * (MAX_CHUNK_CHARS + 100)
    parts = list(_split_long(text, 0))
    assert len(parts) == 3
    assert len(parts[0][0]) >= MAX_CHUNK_CHARS
    assert len(parts[1][0]) > 0

def test_chunk_file_unreadable(tmp_path):
    # A directory path should raise an exception when read_text is called, caught by try/except
    chunks = chunk_file(tmp_path)
    assert chunks == []
