"""Local file system storage adapter."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from docforge.core.interfaces.adapters import StorageAdapter, StorageArtifact


class LocalStorageAdapter(StorageAdapter):
    """Stores artifacts in the local file system.
    
    Artifacts are organized by type:
    - rulebooks/ for rulebook artifacts
    - contexts/ for product context artifacts
    - documents/ for generated documents
    - etc.
    """

    def __init__(self, base_path: Union[str, Path] = ".docforge"):
        """Initialize with base storage path.
        
        Args:
            base_path: Root directory for all artifacts (default: .docforge/)
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """Resolve artifact path relative to base.
        
        Args:
            path: Relative or absolute path
            
        Returns:
            Resolved absolute path
            
        Raises:
            ValueError: If path tries to escape base directory
        """
        target = (self.base_path / path).resolve()
        if not str(target).startswith(str(self.base_path)):
            raise ValueError(f"Path {path} escapes base directory")
        return target

    async def save(
        self,
        path: str,
        content: Union[str, bytes],
        artifact_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageArtifact:
        """Save artifact to disk.
        
        Args:
            path: Relative path within storage
            content: File content
            artifact_type: Type of artifact (for organization)
            metadata: Optional metadata dict
            
        Returns:
            StorageArtifact with metadata
        """
        target_path = self._resolve_path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        if isinstance(content, bytes):
            async_write = asyncio.coroutine(lambda: None)  # placeholder
            target_path.write_bytes(content)
        else:
            target_path.write_text(content, encoding="utf-8")

        # Create metadata
        now = datetime.utcnow().isoformat()
        artifact_metadata = {
            "size": len(content),
            "saved_by": "LocalStorageAdapter",
            **(metadata or {}),
        }

        artifact = StorageArtifact(
            path=str(path),
            artifact_type=artifact_type,
            created_at=now,
            modified_at=now,
            version="1.0",
            metadata=artifact_metadata,
        )

        # Store metadata alongside artifact
        meta_path = target_path.with_suffix(target_path.suffix + ".meta.json")
        meta_path.write_text(artifact.model_dump_json(), encoding="utf-8")

        return artifact

    async def load(self, path: str) -> Union[str, bytes]:
        """Load artifact from disk.
        
        Args:
            path: Relative path within storage
            
        Returns:
            File content (detected as text or binary)
        """
        target_path = self._resolve_path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"Artifact not found: {path}")

        # Load metadata to determine type
        meta_path = target_path.with_suffix(target_path.suffix + ".meta.json")
        if meta_path.exists():
            try:
                import json
                meta_data = json.loads(meta_path.read_text())
                # If metadata indicates binary, load as binary
                artifact_type = meta_data.get("artifact_type", "")
                if artifact_type == "binary" or artifact_type.startswith("binary"):
                    return target_path.read_bytes()
            except Exception:
                pass

        # Try to load as text first
        try:
            return target_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fall back to binary
            return target_path.read_bytes()

    async def exists(self, path: str) -> bool:
        """Check if artifact exists.
        
        Args:
            path: Relative path within storage
            
        Returns:
            True if artifact exists
        """
        target_path = self._resolve_path(path)
        return target_path.exists()

    async def list_artifacts(
        self, artifact_type: Optional[str] = None, prefix: Optional[str] = None
    ) -> List[StorageArtifact]:
        """List all artifacts, optionally filtered.
        
        Args:
            artifact_type: Filter by artifact type
            prefix: Filter by path prefix
            
        Returns:
            List of StorageArtifacts
        """
        artifacts: List[StorageArtifact] = []

        for meta_file in self.base_path.rglob("*.meta.json"):
            try:
                metadata = StorageArtifact.model_validate_json(meta_file.read_text())

                if artifact_type and metadata.artifact_type != artifact_type:
                    continue

                if prefix and not metadata.path.startswith(prefix):
                    continue

                artifacts.append(metadata)
            except Exception:
                # Skip malformed metadata
                continue

        return artifacts

    async def delete(self, path: str) -> None:
        """Delete artifact and its metadata.
        
        Args:
            path: Relative path within storage
        """
        target_path = self._resolve_path(path)
        if target_path.exists():
            target_path.unlink()

        meta_path = target_path.with_suffix(target_path.suffix + ".meta.json")
        if meta_path.exists():
            meta_path.unlink()
