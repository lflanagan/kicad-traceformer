"""
Creates zip archive from collected project files.
"""

import zipfile
from pathlib import Path
from typing import Dict


class ZipExporter:
    """Creates zip archive with project files."""

    def __init__(self, output_path: Path):
        """
        Initialize exporter with output path.

        Args:
            output_path: Full path for the output .zip file
        """
        self.output_path = output_path

    def create_zip(self, files: Dict[Path, str]) -> None:
        """
        Create zip file with project files.

        Args:
            files: Dict mapping source_path -> archive_path
                   e.g., {
                       Path('/path/to/project.kicad_pcb'): 'project.kicad_pcb',
                       Path('/external/lib.kicad_sym'): 'external_libs/lib.kicad_sym'
                   }

        Raises:
            FileNotFoundError: If a source file doesn't exist
            PermissionError: If cannot write to output path
        """
        with zipfile.ZipFile(self.output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for source_path, archive_path in files.items():
                if source_path.exists():
                    zf.write(source_path, archive_path)

