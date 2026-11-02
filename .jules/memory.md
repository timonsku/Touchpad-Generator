
## Archived: 2026-11-02
* To ensure KiCad compatibility, the project uses Eagle 7.7.0 format for templates (`empty.brd`, `empty.sch`) and explicitly sets `isolate='0'` on generated polygons.
* Project tasks and improvements are tracked in `TODO.md`.
* The project is a Touchpad Generator that creates Eagle-compatible board files (`.brd`) and schematics (`.sch`) from DXF inputs.
* `create_touchpad_pcb.py` supports CLI arguments for specifying input/output files and design parameters (e.g., via size, trace width).
* The core script `create_touchpad_pcb.py` requires the `ezdxf` library to parse DXF files.
