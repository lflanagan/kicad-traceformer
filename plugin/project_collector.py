"""
Collects all files needed for a complete KiCad project export.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from .kicad_parser import find_elements, get_element_value, get_property, parse_kicad


class ProjectCollector:
    """
    Collects all files required for a KiCad project export.

    Handles:
    - Core project files (.kicad_pcb, .kicad_sch, .kicad_pro)
    - Hierarchical schematic sheets (recursively)
    - External symbol libraries
    """

    def __init__(self, pcb_path: str):
        """
        Initialize collector with path to .kicad_pcb file.

        Args:
            pcb_path: Full path to the .kicad_pcb file
        """
        self.pcb_path = Path(pcb_path)
        self.project_dir = self.pcb_path.parent
        self.project_name = self.pcb_path.stem

        # Files to include in zip
        self.collected_files: Set[Path] = set()

        # External files (outside project dir) with reason
        self.external_files: Dict[Path, str] = {}

        # Warnings/errors encountered
        self.warnings: List[str] = []

    def collect_all(self) -> None:
        """Collect all project files."""
        self._collect_core_files()
        self._collect_schematic_hierarchy()
        self._collect_symbol_libraries()

    def _collect_core_files(self) -> None:
        """Collect .kicad_pcb, .kicad_pro, .kicad_sch files."""
        # PCB file (always exists since we got path from board)
        if self.pcb_path.exists():
            self.collected_files.add(self.pcb_path)

        # Project file
        pro_path = self.project_dir / f"{self.project_name}.kicad_pro"
        if pro_path.exists():
            self.collected_files.add(pro_path)
        else:
            self.warnings.append(f"Project file not found: {pro_path.name}")

        # Main schematic file
        sch_path = self.project_dir / f"{self.project_name}.kicad_sch"
        if sch_path.exists():
            self.collected_files.add(sch_path)
        else:
            self.warnings.append(f"Schematic file not found: {sch_path.name}")

    def _collect_schematic_hierarchy(self) -> None:
        """Recursively collect all hierarchical sheet files."""
        main_sch = self.project_dir / f"{self.project_name}.kicad_sch"
        if not main_sch.exists():
            return

        visited: Set[Path] = set()
        self._parse_schematic_sheets(main_sch, visited)

    def _parse_schematic_sheets(self, sch_path: Path, visited: Set[Path]) -> None:
        """
        Parse a schematic file for sheet references.

        Args:
            sch_path: Path to .kicad_sch file
            visited: Set of already-visited files (prevents infinite loops)
        """
        resolved = sch_path.resolve()
        if resolved in visited:
            return
        visited.add(resolved)

        if not sch_path.exists():
            self.warnings.append(f"Referenced schematic not found: {sch_path}")
            return

        try:
            content = sch_path.read_text(encoding="utf-8")
            tree = parse_kicad(content)

            # Find all sheet elements
            sheets = find_elements(tree, "sheet")

            for sheet in sheets:
                # Get the Sheetfile property
                sheet_file = get_property(sheet, "Sheetfile")
                if not sheet_file:
                    continue

                # Resolve path relative to current schematic's directory
                sheet_path = sch_path.parent / sheet_file

                if sheet_path.exists():
                    self.collected_files.add(sheet_path.resolve())
                    # Recursively parse this sheet
                    self._parse_schematic_sheets(sheet_path, visited)
                else:
                    self.warnings.append(f"Subsheet not found: {sheet_file}")

        except Exception as e:
            self.warnings.append(f"Error parsing {sch_path.name}: {e}")

    def _collect_symbol_libraries(self) -> None:
        """Collect external symbol libraries from sym-lib-table."""
        lib_table_path = self.project_dir / "sym-lib-table"
        if not lib_table_path.exists():
            return

        try:
            content = lib_table_path.read_text(encoding="utf-8")
            tree = parse_kicad(content)

            # Find all lib entries
            libs = find_elements(tree, "lib")

            for lib in libs:
                uri = get_element_value(lib, "uri")
                if not uri:
                    continue

                lib_path = self._resolve_lib_path(uri)
                if lib_path is None:
                    continue

                if lib_path.exists():
                    # Check if external (outside project directory)
                    if self._is_external(lib_path):
                        lib_name = get_element_value(lib, "name") or lib_path.name
                        self.external_files[lib_path.resolve()] = lib_name
                    else:
                        self.collected_files.add(lib_path.resolve())
                else:
                    self.warnings.append(f"Library not found: {uri}")

        except Exception as e:
            self.warnings.append(f"Error parsing sym-lib-table: {e}")

    def _resolve_lib_path(self, uri: str) -> Optional[Path]:
        """
        Resolve library URI to actual path.

        Handles:
        - ${KIPRJMOD} -> project directory
        - Absolute paths
        - Relative paths

        Skips:
        - ${KICAD_SYMBOL_DIR} (system libraries)
        - ${KICAD7_SYMBOL_DIR} etc.

        Args:
            uri: Library URI from sym-lib-table

        Returns:
            Resolved Path, or None if should be skipped
        """
        # Skip KiCad system libraries
        if uri.startswith("${KICAD"):
            return None

        # Replace ${KIPRJMOD} with project directory
        if uri.startswith("${KIPRJMOD}"):
            uri = uri.replace("${KIPRJMOD}", str(self.project_dir))

        # Normalize path separators
        uri = uri.replace("\\", "/")

        path = Path(uri)

        # If relative, resolve from project directory
        if not path.is_absolute():
            path = self.project_dir / path

        return path

    def _is_external(self, path: Path) -> bool:
        """Check if path is outside the project directory."""
        try:
            path.resolve().relative_to(self.project_dir.resolve())
            return False
        except ValueError:
            return True

    def get_files_for_zip(self) -> Dict[Path, str]:
        """
        Get mapping of source paths to archive paths.

        Returns:
            Dict mapping absolute source paths to relative archive paths.
            External libraries go in 'external_libs/' subdirectory.

        Example:
            {
                Path('/project/board.kicad_pcb'): 'board.kicad_pcb',
                Path('/external/lib.kicad_sym'): 'external_libs/lib.kicad_sym'
            }
        """
        result: Dict[Path, str] = {}

        # Project files (use path relative to project dir)
        for file_path in self.collected_files:
            try:
                rel_path = file_path.relative_to(self.project_dir)
                result[file_path] = str(rel_path)
            except ValueError:
                # Shouldn't happen for collected_files, but handle gracefully
                result[file_path] = file_path.name

        # External libraries go in external_libs/ folder
        for file_path, lib_name in self.external_files.items():
            # Use library name + extension for clarity
            archive_name = f"external_libs/{file_path.name}"
            result[file_path] = archive_name

        return result

    def get_files_by_category(self) -> Dict[str, List[str]]:
        """
        Get files organized by category for tree display.

        Returns:
            Dict with category names as keys and lists of filenames as values.
            Categories: "Project Files", "Schematic Files", "External Libraries"
        """
        result: Dict[str, List[str]] = {
            "Project Files": [],
            "Schematic Files": [],
            "External Libraries": [],
        }

        for file_path in sorted(self.collected_files):
            if file_path.suffix in (".kicad_pcb", ".kicad_pro"):
                result["Project Files"].append(file_path.name)
            elif file_path.suffix == ".kicad_sch":
                result["Schematic Files"].append(file_path.name)

        for file_path in sorted(self.external_files.keys()):
            result["External Libraries"].append(file_path.name)

        # Remove empty categories
        return {k: v for k, v in result.items() if v}
