import os

import pcbnew
import wx

from .project_collector import ProjectCollector
from .zip_export_dialog import ZipExportDialog
from .zip_exporter import ZipExporter


class NetlistPluginAction(pcbnew.ActionPlugin):
    def defaults(self) -> None:
        self.name = "Netlist.io KiCad Plugin"
        self.category = "Netlist"
        self.description = "Export project as ZIP for upload to netlist.io"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "icon.png")

    def Run(self) -> None:
        board = pcbnew.GetBoard()
        pcb_path = board.GetFileName()

        # Check if board is saved
        if not pcb_path:
            wx.MessageBox(
                "Please save the board first before exporting.",
                "No Project Open",
                wx.OK | wx.ICON_WARNING,
            )
            return

        project_name = os.path.splitext(os.path.basename(pcb_path))[0]
        project_dir = os.path.dirname(pcb_path)

        # Collect project files
        collector = ProjectCollector(pcb_path)
        try:
            collector.collect_all()
        except Exception as e:
            wx.MessageBox(
                f"Error collecting project files:\n{e}",
                "Collection Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        # Get files organized by category for tree display
        files_by_category = collector.get_files_by_category()

        # Show export dialog
        dialog = ZipExportDialog(None, project_name, project_dir, files_by_category)
        result = dialog.ShowModal()

        if result != wx.ID_OK:
            dialog.Destroy()
            return

        export_path = dialog.get_export_path()
        dialog.Destroy()

        if export_path is None:
            return

        # Get files for zip
        files = collector.get_files_for_zip()

        if not files:
            wx.MessageBox(
                "No files found to export.",
                "Export Error",
                wx.OK | wx.ICON_WARNING,
            )
            return

        # Create zip
        exporter = ZipExporter(export_path)

        try:
            exporter.create_zip(files)

            # Show success message
            file_count = len(files)
            external_count = len(collector.external_files)

            message = f"Project exported successfully!\n\n"
            message += f"Location: {export_path}\n"
            message += f"Files included: {file_count}"
            if external_count > 0:
                message += f"\nExternal libraries: {external_count}"

            if collector.warnings:
                message += f"\n\nWarnings: {len(collector.warnings)}"
                for warning in collector.warnings[:3]:
                    message += f"\n  - {warning}"
                if len(collector.warnings) > 3:
                    message += f"\n  ... and {len(collector.warnings) - 3} more"

            wx.MessageBox(
                message,
                "Export Complete",
                wx.OK | wx.ICON_INFORMATION,
            )

        except PermissionError:
            wx.MessageBox(
                f"Cannot write to:\n{export_path}\n\nCheck file permissions.",
                "Export Error",
                wx.OK | wx.ICON_ERROR,
            )
        except Exception as e:
            wx.MessageBox(
                f"Error creating zip file:\n{e}",
                "Export Error",
                wx.OK | wx.ICON_ERROR,
            )
