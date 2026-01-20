"""Model slot management for storing and retrieving named model versions."""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class ModelSlotManager:
    """Manages named model slots under checkpoints/slots/.

    Model slots allow users to save trained models to named slots for later
    retrieval, comparison, or export. Each slot contains model.zip and
    metadata.json (replay buffer is excluded due to size).

    Example:
        >>> manager = ModelSlotManager("./checkpoints")
        >>> manager.save_to_slot("best", "my_best_model")
        True
        >>> manager.list_slots()
        [{'name': 'my_best_model', 'path': '...', 'total_timesteps_trained': 50000}]
        >>> manager.export_model("my_best_model", "./exports/model.zip")
        True
    """

    # Valid slot name pattern: alphanumeric, underscore, hyphen
    SLOT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    def __init__(self, base_dir: str = "./checkpoints"):
        """Initialize ModelSlotManager.

        Args:
            base_dir: Base directory for checkpoints. Slots will be stored
                under {base_dir}/slots/.
        """
        self.base_dir = Path(base_dir)
        self.slots_dir = self.base_dir / "slots"
        self.slots_dir.mkdir(parents=True, exist_ok=True)

    def _validate_slot_name(self, slot_name: str) -> bool:
        """Validate slot name format.

        Args:
            slot_name: Name to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not slot_name:
            return False
        return bool(self.SLOT_NAME_PATTERN.match(slot_name))

    def list_slots(self) -> List[Dict]:
        """List all model slots with metadata.

        Returns:
            List of dicts with: name, path, and metadata fields
            (total_timesteps_trained, num_timesteps, config, best_lines if available).
        """
        slots = []
        for slot_dir in self.slots_dir.iterdir():
            if not slot_dir.is_dir():
                continue
            # Only include directories that have model.zip
            model_path = slot_dir / "model.zip"
            if not model_path.exists():
                continue

            slot_info = {
                "name": slot_dir.name,
                "path": str(slot_dir),
            }

            # Load metadata if available
            metadata_path = slot_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path) as f:
                        metadata = json.load(f)
                    # Include key metadata fields
                    for key in ["total_timesteps_trained", "num_timesteps", "config", "best_lines"]:
                        if key in metadata:
                            slot_info[key] = metadata[key]
                except (json.JSONDecodeError, IOError):
                    pass  # Metadata corrupted, still include slot

            slots.append(slot_info)

        # Sort by name for consistent ordering
        slots.sort(key=lambda x: x["name"])
        return slots

    def save_to_slot(self, source: str, slot_name: str) -> bool:
        """Copy model from source (best/latest/final) to named slot.

        Only copies model.zip and metadata.json (NOT replay_buffer.pkl - too large).
        Overwrites if slot exists.

        Args:
            source: Source checkpoint name ("best", "latest", or "final").
            slot_name: Name for the new slot.

        Returns:
            True on success, False if source doesn't exist or invalid slot name.
        """
        if not self._validate_slot_name(slot_name):
            return False

        source_path = self.base_dir / source
        if not source_path.exists():
            return False

        # Check source has model.zip
        source_model = source_path / "model.zip"
        if not source_model.exists():
            return False

        # Create slot directory
        slot_path = self.slots_dir / slot_name
        slot_path.mkdir(parents=True, exist_ok=True)

        # Copy model.zip
        shutil.copy2(source_model, slot_path / "model.zip")

        # Copy metadata.json if exists
        source_metadata = source_path / "metadata.json"
        if source_metadata.exists():
            shutil.copy2(source_metadata, slot_path / "metadata.json")

        return True

    def delete_slot(self, slot_name: str) -> bool:
        """Delete a named slot.

        Args:
            slot_name: Name of slot to delete.

        Returns:
            True if deleted, False if not found or invalid name.
        """
        if not self._validate_slot_name(slot_name):
            return False

        slot_path = self.slots_dir / slot_name
        if not slot_path.exists():
            return False

        shutil.rmtree(slot_path)
        return True

    def export_model(self, slot_name: str, export_path: str) -> bool:
        """Export model.zip to standalone file path.

        Args:
            slot_name: Name of slot to export.
            export_path: Destination file path for the exported model.

        Returns:
            True on success, False if slot doesn't exist or invalid name.
        """
        if not self._validate_slot_name(slot_name):
            return False

        slot_path = self.slots_dir / slot_name
        model_path = slot_path / "model.zip"

        if not model_path.exists():
            return False

        # Ensure parent directory exists
        export_file = Path(export_path)
        export_file.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(model_path, export_file)
        return True

    def get_slot_path(self, slot_name: str) -> Optional[Path]:
        """Get path to slot directory.

        Args:
            slot_name: Name of slot.

        Returns:
            Path to slot directory, or None if doesn't exist.
        """
        if not self._validate_slot_name(slot_name):
            return None

        slot_path = self.slots_dir / slot_name
        if not slot_path.exists():
            return None

        return slot_path

    def slot_exists(self, slot_name: str) -> bool:
        """Check if a slot with given name exists.

        Args:
            slot_name: Name of slot to check.

        Returns:
            True if slot exists and contains model.zip, False otherwise.
        """
        if not self._validate_slot_name(slot_name):
            return False

        slot_path = self.slots_dir / slot_name
        model_path = slot_path / "model.zip"
        return model_path.exists()
