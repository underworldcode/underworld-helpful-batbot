"""
Content Manager for HelpfulBatBot

Manages fetching and updating content from multiple git repositories.
Supports automatic updates, caching, and flexible include/exclude patterns.
"""

import os
import yaml
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging
import json

logger = logging.getLogger(__name__)


class ContentSource:
    """Represents a single content source (e.g., a git repository)"""

    def __init__(self, config: Dict):
        self.name = config["name"]
        self.type = config["type"]
        self.url = config["url"]
        self.branch = config.get("branch", "main")
        self.local_path = Path(config["local_path"])
        self.update_frequency = config.get("update_frequency", "daily")
        self.include_paths = config.get("include_paths", [])
        self.exclude_paths = config.get("exclude_paths", [])
        self.priority = config.get("priority", 1.0)
        self.source_label = config.get("source_label", self.name)

        self.last_update = None
        self._load_update_timestamp()

    def _load_update_timestamp(self):
        """Load last update timestamp from disk"""
        update_marker = self.local_path / ".last_update"
        if update_marker.exists():
            try:
                timestamp = float(update_marker.read_text())
                self.last_update = datetime.fromtimestamp(timestamp)
            except (ValueError, OSError):
                pass

    def _save_update_timestamp(self):
        """Save update timestamp to disk"""
        update_marker = self.local_path / ".last_update"
        try:
            update_marker.write_text(str(datetime.now().timestamp()))
        except OSError as e:
            logger.warning(f"Could not save update timestamp: {e}")

    def needs_update(self) -> bool:
        """Check if content needs to be updated based on frequency"""
        if not self.local_path.exists():
            return True

        if self.last_update is None:
            return True

        if self.update_frequency == "on_startup":
            return False  # Only update once per run

        now = datetime.now()
        if self.update_frequency == "hourly":
            return (now - self.last_update) > timedelta(hours=1)
        elif self.update_frequency == "daily":
            return (now - self.last_update) > timedelta(days=1)
        elif self.update_frequency == "never":
            return False

        return False

    def clone_or_pull(self) -> bool:
        """Clone or pull the git repository"""
        logger.info(f"Updating content source: {self.name}")

        try:
            if not self.local_path.exists():
                # Clone repository
                logger.info(f"Cloning {self.url} to {self.local_path}")
                self.local_path.parent.mkdir(parents=True, exist_ok=True)

                result = subprocess.run([
                    "git", "clone",
                    "--depth", "1",  # Shallow clone for faster download
                    "--single-branch",
                    "--branch", self.branch,
                    self.url,
                    str(self.local_path)
                ], check=True, capture_output=True, text=True)

                logger.info(f"✅ Cloned {self.name}")

            else:
                # Pull latest changes
                logger.info(f"Pulling latest from {self.name}")

                result = subprocess.run([
                    "git", "-C", str(self.local_path),
                    "pull", "--ff-only", "origin", self.branch
                ], check=True, capture_output=True, text=True)

                if "Already up to date" in result.stdout:
                    logger.info(f"✅ {self.name} already up to date")
                else:
                    logger.info(f"✅ Updated {self.name}")

            # Mark update time
            self.last_update = datetime.now()
            self._save_update_timestamp()

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update {self.name}: {e}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating {self.name}: {e}")
            return False

    def get_files(self) -> List[Path]:
        """Get all files matching include/exclude patterns"""
        from pathlib import PurePosixPath

        if not self.local_path.exists():
            logger.warning(f"Content path does not exist: {self.local_path}")
            return []

        files = []

        # Find all files matching include patterns
        for pattern in self.include_paths:
            # Use glob to match patterns
            for file_path in self.local_path.glob(pattern):
                if file_path.is_file():
                    # Get relative path for exclude checking
                    try:
                        rel_path = file_path.relative_to(self.local_path)
                        rel_posix = PurePosixPath(rel_path)

                        # Check against exclude patterns
                        excluded = False
                        for exclude_pattern in self.exclude_paths:
                            if rel_posix.match(exclude_pattern):
                                excluded = True
                                break

                        if not excluded:
                            files.append(file_path)
                    except ValueError:
                        # Path is not relative to local_path
                        pass

        logger.info(f"Found {len(files)} files in {self.name}")
        return files

    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            "name": self.name,
            "url": self.url,
            "branch": self.branch,
            "file_count": len(self.get_files()) if self.local_path.exists() else 0,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "priority": self.priority
        }


class ContentManager:
    """Manages all content sources for HelpfulBatBot"""

    def __init__(self, config_path: str = "content_sources.yaml"):
        self.config_path = Path(config_path)
        self.sources: List[ContentSource] = []

        # Load configuration
        if self.config_path.exists():
            self._load_config()
        else:
            logger.warning(f"Config file not found: {config_path}")
            logger.warning("Content manager initialized with no sources")

    def _load_config(self):
        """Load content sources from YAML configuration"""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)

            if not config or "content_sources" not in config:
                logger.warning("No content sources defined in config")
                return

            for source_config in config["content_sources"]:
                try:
                    source = ContentSource(source_config)
                    self.sources.append(source)
                    logger.info(f"Loaded content source: {source.name}")
                except Exception as e:
                    logger.error(f"Failed to load source {source_config.get('name')}: {e}")

        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")

    def update_all(self, force: bool = False) -> bool:
        """
        Update all content sources that need updating.

        Args:
            force: Force update even if not needed by frequency

        Returns:
            True if all updates succeeded, False if any failed
        """
        if not self.sources:
            logger.warning("No content sources configured")
            return False

        success = True
        updated_count = 0

        for source in self.sources:
            if force or source.needs_update():
                if source.clone_or_pull():
                    updated_count += 1
                else:
                    success = False

        if updated_count > 0:
            logger.info(f"Updated {updated_count}/{len(self.sources)} content sources")
        else:
            logger.info("All content sources up to date")

        return success

    def get_all_files(self) -> List[Tuple[Path, str, float, str]]:
        """
        Get all files from all sources.

        Returns:
            List of (file_path, source_name, priority, source_label) tuples
        """
        all_files = []

        for source in self.sources:
            for file_path in source.get_files():
                all_files.append((
                    file_path,
                    source.name,
                    source.priority,
                    source.source_label
                ))

        logger.info(f"Total files from all sources: {len(all_files)}")
        return all_files

    def get_stats(self) -> Dict:
        """Get statistics about content sources"""
        return {
            "source_count": len(self.sources),
            "sources": [source.to_dict() for source in self.sources],
            "total_files": len(self.get_all_files())
        }


def extract_notebook_text(notebook_path: Path) -> str:
    """
    Extract text content from Jupyter notebook (.ipynb) file.

    Args:
        notebook_path: Path to .ipynb file

    Returns:
        Extracted text content
    """
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)

        text_parts = []
        text_parts.append(f"# Jupyter Notebook: {notebook_path.name}\n")

        for i, cell in enumerate(notebook.get('cells', []), 1):
            cell_type = cell.get('cell_type')
            source = cell.get('source', [])

            # Convert source to string
            if isinstance(source, list):
                content = ''.join(source)
            else:
                content = source

            if cell_type == 'markdown':
                text_parts.append(f"## Cell {i} (Markdown)\n{content}\n")
            elif cell_type == 'code':
                text_parts.append(f"## Cell {i} (Code)\n```python\n{content}\n```\n")

        return '\n\n'.join(text_parts)

    except Exception as e:
        logger.error(f"Failed to extract notebook text from {notebook_path}: {e}")
        return ""


def load_files_from_sources(config_path: str = "content_sources.yaml") -> List[Tuple[str, str, Dict]]:
    """
    Load all files from configured content sources.

    Args:
        config_path: Path to content_sources.yaml

    Returns:
        List of (file_path_str, content, metadata) tuples
    """
    content_manager = ContentManager(config_path)

    # Update content if needed
    logger.info("Checking for content updates...")
    content_manager.update_all()

    # Get all files
    files = content_manager.get_all_files()
    logger.info(f"Loading {len(files)} files for indexing")

    documents = []

    for file_path, source_name, priority, source_label in files:
        try:
            # Read file content
            if file_path.suffix.lower() == '.ipynb':
                content = extract_notebook_text(file_path)
            else:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Skip empty files
            if not content.strip():
                logger.warning(f"Skipping empty file: {file_path}")
                continue

            # Create metadata
            metadata = {
                "file": file_path.name,
                "full_path": str(file_path),
                "source": source_name,
                "source_label": source_label,
                "priority": priority,
                "last_modified": file_path.stat().st_mtime
            }

            documents.append((str(file_path), content, metadata))

        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}")

    logger.info(f"Successfully loaded {len(documents)} documents")
    return documents
