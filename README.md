# Netlist.io KiCad Plugin

A KiCad plugin that packages your project files into a ZIP archive for upload to [netlist.io](https://netlist.io).

## Features

- Export your KiCad project as a ZIP file ready for upload
- Automatically collects all required files:
  - Project files (`.kicad_pcb`, `.kicad_pro`)
  - Schematic files (`.kicad_sch`)
  - Hierarchical subsheets (recursively detected)
  - External symbol libraries referenced outside your project folder
- Simple dialog to choose export location and filename
- Tree view showing exactly which files will be included

## Installation

### From File

1. Download the latest release ZIP from the [releases page](https://github.com/liamflanagan/kicad-netlist/releases)
2. Open KiCad → Plugin and Content Manager
3. Click "Install from File..."
4. Select the downloaded ZIP

### Development Install

For development, you can symlink the plugin directly:

```shell
./scripts/link_plugin.sh
```

## Usage

1. Open your project in KiCad's PCB Editor
2. Click the Netlist button in the toolbar
3. Choose your export folder and filename
4. Review the files that will be included
5. Click OK to create the ZIP

The resulting ZIP can be uploaded directly to [netlist.io](https://netlist.io).

## Building from Source

Requires [Hatch](https://hatch.pypa.io/):

```shell
pip install hatch hatch-kicad
hatch build --target kicad-package
```

The built plugin will be in `dist/`.

## Acknowledgments

This plugin was built using the [kicad-plugin-template](https://github.com/adamws/kicad-plugin-template) by [@adamws](https://github.com/adamws).

## License

MIT
