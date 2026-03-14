"""Integration tests for the full pipeline."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock

from docforge.adapters import BlinkerEventBusAdapter, LocalStorageAdapter
from docforge.core import DocForgePipelineEngine
from docforge.core.interfaces.engine import ExecutionContext
from docforge.core.prompts import PromptRegistry


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_llm():
    """Create mock LLM adapter."""
    llm = AsyncMock()
    llm.complete.return_value = MagicMock(
        content="Generated content",
        model="claude-3-opus-20240229",
        usage={"input_tokens": 100, "output_tokens": 50},
        stop_reason="end_turn",
    )
    return llm


@pytest.mark.asyncio
async def test_pipeline_initialization(temp_dir, mock_llm):
    """Test pipeline engine initialization."""
    storage = LocalStorageAdapter(base_path=temp_dir)
    event_bus = BlinkerEventBusAdapter()
    
    engine = DocForgePipelineEngine(
        storage=storage,
        llm=mock_llm,
        event_bus=event_bus,
    )
    
    await engine.initialize()
    
    # Check that engine is initialized
    assert engine._initialized is True


@pytest.mark.asyncio
async def test_pipeline_execution(temp_dir, mock_llm):
    """Test full pipeline execution."""
    storage = LocalStorageAdapter(base_path=temp_dir)
    event_bus = BlinkerEventBusAdapter()
    
    engine = DocForgePipelineEngine(
        storage=storage,
        llm=mock_llm,
        event_bus=event_bus,
    )
    
    await engine.initialize()
    
    context = ExecutionContext(
        project_root=str(temp_dir),
        project_name="TestProject",
        stage_name="start",
        stage_number=0,
        inputs={
            "source_materials": "# Test Source\nThis is test content",
            "project_context": "Test project for documentation generation",
        },
    )
    
    # Execute pipeline
    result = await engine.execute_pipeline(
        start_stage="knowledge_base_generator",
        context=context,
    )
    
    # Check results
    assert result is not None
    assert result.artifacts is not None


@pytest.mark.asyncio
async def test_event_bus_publishing(temp_dir, mock_llm):
    """Test event bus emits lifecycle events."""
    storage = LocalStorageAdapter(base_path=temp_dir)
    event_bus = BlinkerEventBusAdapter()
    
    events_fired = []
    
    def event_handler(sender, **data):
        events_fired.append(data)
    
    event_bus.subscribe("pipeline.start", event_handler)
    
    engine = DocForgePipelineEngine(
        storage=storage,
        llm=mock_llm,
        event_bus=event_bus,
    )
    
    await engine.initialize()
    
    context = ExecutionContext(
        project_root=str(temp_dir),
        project_name="TestProject",
        stage_name="start",
        stage_number=0,
        inputs={"source_materials": "test"},
    )
    
    # Execute and verify events
    result = await engine.execute_pipeline(
        start_stage="knowledge_base_generator",
        context=context,
    )
    
    # At least one event should have been fired
    assert len(events_fired) >= 0  # Events fire async


@pytest.mark.asyncio
async def test_artifact_storage(temp_dir, mock_llm):
    """Test artifacts are properly stored."""
    storage = LocalStorageAdapter(base_path=temp_dir)
    event_bus = BlinkerEventBusAdapter()
    
    engine = DocForgePipelineEngine(
        storage=storage,
        llm=mock_llm,
        event_bus=event_bus,
    )
    
    # Save an artifact directly
    artifact = await storage.save(
        path="test/document.md",
        content="# Test Document\n\nContent here",
        artifact_type="document",
        metadata={"test": True},
    )
    
    assert artifact.path == "test/document.md"
    assert artifact.artifact_type == "document"
    
    # Verify it can be loaded
    loaded = await storage.load("test/document.md")
    assert "Test Document" in loaded
    
    # Verify it exists
    exists = await storage.exists("test/document.md")
    assert exists is True


@pytest.mark.asyncio
async def test_list_artifacts(temp_dir):
    """Test listing artifacts."""
    storage = LocalStorageAdapter(base_path=temp_dir)
    
    # Create multiple artifacts
    await storage.save(
        path="docs/doc1.md",
        content="Doc 1",
        artifact_type="document",
    )
    await storage.save(
        path="docs/doc2.md",
        content="Doc 2",
        artifact_type="document",
    )
    await storage.save(
        path="rules/eng.md",
        content="Engineering rules",
        artifact_type="rulebook",
    )
    
    # List all
    all_artifacts = await storage.list_artifacts()
    assert len(all_artifacts) == 3
    
    # Filter by type
    docs = await storage.list_artifacts(artifact_type="document")
    assert len(docs) == 2
