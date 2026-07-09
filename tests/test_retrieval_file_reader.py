from pathlib import Path

from Bugfix_agent.retrieval.file_reader import read_files


def test_read_files_skips_generated_directories(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text("def run():\n    return True\n", encoding="utf-8")

    cache_dir = tmp_path / ".pytest_cache"
    cache_dir.mkdir()
    (cache_dir / "cached.py").write_text("def ignored():\n    return False\n", encoding="utf-8")

    pycache_dir = tmp_path / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "compiled.py").write_text("def ignored_again():\n    return False\n", encoding="utf-8")

    result = read_files({"repo_path": str(tmp_path)})
    paths = {Path(file_node["path"]).name for file_node in result["getfiles"]}

    assert paths == {"app.py"}
