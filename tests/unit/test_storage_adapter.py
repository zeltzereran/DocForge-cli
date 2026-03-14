"""Tests for file storage adapter."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from docforge.adapters.storage import LocalStorageAdapter


@pytest.fixture
def temp_storage():
    """Create temporary storage adapter."""
    with TemporaryDirectory() as tmpdir:
        adapter = LocalStorageAdapter(tmpdir)
        yield adapter


@pytest.mark.asyncio
async def test_save_and_load_text(temp_storage):
    """Test saving and loading text artifacts."""
    content = "Hello, DocForge!"
    
    # Save
    artifact = await temp_storage.save(
        path="test.txt",
        content=content,
        artifact_type="test",
    )
    
    assert artifact.path == "test.txt"
    assert artifact.artifact_type == "test"
    
    # Load
    loaded = await temp_storage.load("test.txt")
    assert loaded == content


@pytest.mark.asyncio
async def test_save_and_load_binary(temp_storage):
    """Test saving and loading binary artifacts."""
    content = b"\x00\x01\x02\x03"
    
    # Save
    artifact = await temp_storage.save(
        path="test.bin",
        content=content,
        artifact_type="binary",
    )
    
    # Load
    loaded = await temp_storage.load("test.bin")
    assert loaded == content


@pytest.mark.asyncio
async def test_exists(temp_storage):
    """Test existence checking."""
    await temp_storage.save(
        path="existing.txt",
        content="exists",
        artifact_type="test",
    )
    
    assert await temp_storage.exists("existing.txt")
    assert not await temp_storage.exists("nonexistent.txt")


@pytest.mark.asyncio
async def test_delete(temp_storage):
    """Test artifact deletion."""
    await temp_storage.save(
        path="delete_me.txt",
        content="temporary",
        artifact_type="test",
    )
    
    assert await temp_storage.exists("delete_me.txt")
    await temp_storage.delete("delete_me.txt")
    assert not await temp_storage.exists("delete_me.txt")


@pytest.mark.asyncio
async def test_list_artifacts(temp_storage):
    """Test listing artifacts."""
    await temp_storage.save(
        path="doc1.md",
        content="Document 1",
        artifact_type="document",
    )
    await temp_storage.save(
        path="rule1.yaml",
        content="Rule 1",
        artifact_type="rulebook",
    )
    await temp_storage.save(
        path="doc2.md",
        content="Document 2",
        artifact_type="document",
    )
    
    # List all
    all_artifacts = await temp_storage.list_artifacts()
    assert len(all_artifacts) == 3
    
    # Filter by type
    docs = await temp_storage.list_artifacts(artifact_type="document")
    assert len(docs) == 2
    assert all(a.artifact_type == "document" for a in docs)


@pytest.mark.asyncio
async def test_path_escaping_protection(temp_storage):
    """Test that path escaping is prevented."""
    with pytest.raises(ValueError):
        await temp_storage.save(
            path="../../etc/passwd",
            content="malicious",
            artifact_type="test",
        )
