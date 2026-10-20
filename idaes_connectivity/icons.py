"""Unit icons and optional port sides for diagram consumers."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from idaes_connectivity.const import ComponentNames


@dataclass(frozen=True)
class UnitIconSpec:
    """An SVG path (None for a plain box) and port-name to side mapping.

    Registered paths are absolute; bundled filenames are relative to the
    Mermaid component image directory, as in the existing image API.
    """

    svg_path: Optional[Path]
    ports: Dict[str, str] = field(default_factory=dict)


_registry = {}


def _icon_key(key):
    # IDAES public block classes and indexed elements share a data class.
    return getattr(key, "_ComponentDataClass", key) if isinstance(key, type) else key


def register_unit_icon(cls_or_module_name, svg_path, ports=None):
    """Register an icon for a Python class or its fully qualified module name.

    Re-registering a key replaces its icon and port sides. Call before rendering.
    Port sides must be left, right, top, or bottom.
    """
    if not isinstance(cls_or_module_name, (type, str)) or cls_or_module_name == "":
        raise TypeError("Icon key must be a class or a nonempty module name")
    path = Path(svg_path).expanduser().resolve()
    if path.suffix.lower() != ".svg":
        raise ValueError("Unit icons must be SVG files")
    if not path.is_file():
        raise FileNotFoundError(path)
    sides = dict(ports) if ports is not None else {}
    if any(side not in ("left", "right", "top", "bottom") for side in sides.values()):
        raise ValueError("Port sides must be left, right, top, or bottom")
    _registry[_icon_key(cls_or_module_name)] = UnitIconSpec(path, sides)


def lookup_unit_icon(component):
    """Resolve class, base classes, modules, bundled name, then a plain box.

    Accept a model unit, its class, or a class-name string from tabular input.
    """
    if isinstance(component, str):
        name, classes = component, ()
    else:
        cls = component if isinstance(component, type) else type(component)
        name, classes = cls.__name__, cls.__mro__
    for key in (*classes, *(cls.__module__ for cls in classes)):
        key = _icon_key(key)
        if key in _registry:
            icon = _registry[key]
            return UnitIconSpec(icon.svg_path, icon.ports.copy())
    filename = ComponentNames().get_filename(name)
    return UnitIconSpec(Path(filename) if filename else None)
