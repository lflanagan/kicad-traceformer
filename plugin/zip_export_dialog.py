"""
wxPython dialog for configuring project zip export.
"""

from pathlib import Path
from typing import Dict, List, Optional

import wx


class ZipExportDialog(wx.Dialog):
    """Dialog for configuring project zip export destination and filename."""

    def __init__(
        self,
        parent: Optional[wx.Frame],
        project_name: str,
        default_dir: str,
        files_by_category: Optional[Dict[str, List[str]]] = None,
    ):
        """
        Initialize export dialog.

        Args:
            parent: Parent window (can be None)
            project_name: Default name for the zip file
            default_dir: Default export directory
            files_by_category: Dict mapping category names to file lists
        """
        super().__init__(parent, title="Export Project for Netlist.io")

        self.export_path: Optional[Path] = None
        self._project_name = project_name
        self._default_dir = default_dir

        self._create_ui(files_by_category or {})
        self.Centre()

    def _create_ui(self, files_by_category: Dict[str, List[str]]) -> None:
        """Build dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Export Project as ZIP")
        title_font = title.GetFont()
        title_font.SetPointSize(12)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL, 10)

        # Description
        desc = wx.StaticText(
            self,
            label="Create a zip archive of your KiCad project for upload to netlist.io",
        )
        main_sizer.Add(desc, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Separator
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Form fields
        form_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        form_sizer.AddGrowableCol(1, 1)

        # Destination folder
        folder_label = wx.StaticText(self, label="Export to folder:")
        self.folder_picker = wx.DirPickerCtrl(
            self,
            path=self._default_dir,
            message="Select export folder",
            style=wx.DIRP_USE_TEXTCTRL,
        )
        form_sizer.Add(folder_label, 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.folder_picker, 1, wx.EXPAND)

        # Zip filename
        name_label = wx.StaticText(self, label="Zip filename:")
        self.name_entry = wx.TextCtrl(self, value=f"{self._project_name}.zip")
        form_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.name_entry, 1, wx.EXPAND)

        main_sizer.Add(form_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Files tree (if files provided)
        if files_by_category:
            files_label = wx.StaticText(self, label="Files to include:")
            main_sizer.Add(files_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)

            # Create tree control
            self.files_tree = wx.TreeCtrl(
                self,
                style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_NO_LINES,
                size=(-1, 150),
            )

            # Add root (hidden)
            root = self.files_tree.AddRoot("Files")

            # Add categories and files
            for category, files in files_by_category.items():
                # Category node with count
                category_label = f"{category} ({len(files)})"
                category_node = self.files_tree.AppendItem(root, category_label)

                # Make category bold
                self.files_tree.SetItemBold(category_node, True)

                # Add file children
                for filename in files:
                    self.files_tree.AppendItem(category_node, filename)

            # Expand all categories by default
            self.files_tree.ExpandAll()

            main_sizer.Add(
                self.files_tree, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10
            )

        # Buttons
        btn_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(main_sizer)
        self.Fit()

        # Set minimum width only
        self.SetMinSize(wx.Size(450, -1))

        # Bind events
        self.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)

    def _on_ok(self, event: wx.CommandEvent) -> None:
        """Validate inputs and set export_path."""
        folder = self.folder_picker.GetPath()
        filename = self.name_entry.GetValue().strip()

        # Validate folder
        if not folder:
            wx.MessageBox(
                "Please select an export folder.",
                "Validation Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        if not Path(folder).is_dir():
            wx.MessageBox(
                "Selected folder does not exist.",
                "Validation Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        # Validate filename
        if not filename:
            wx.MessageBox(
                "Please enter a filename.",
                "Validation Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        # Ensure .zip extension
        if not filename.lower().endswith(".zip"):
            filename += ".zip"

        self.export_path = Path(folder) / filename

        # Check if file already exists
        if self.export_path.exists():
            result = wx.MessageBox(
                f"File '{filename}' already exists. Overwrite?",
                "Confirm Overwrite",
                wx.YES_NO | wx.ICON_WARNING,
            )
            if result != wx.YES:
                return

        self.EndModal(wx.ID_OK)

    def get_export_path(self) -> Optional[Path]:
        """Get the configured export path."""
        return self.export_path
