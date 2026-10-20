"""Port metadata, Arc traversal, and icon resolution without a solver."""

import base64

from idaes.core import FlowsheetBlock
from idaes.models.properties.examples.saponification_thermo import (
    SaponificationParameterBlock,
)
from idaes.models.unit_models import MSContactor
from pyomo.environ import Block, ConcreteModel
from pyomo.network import Arc, Port
import pytest

from idaes_connectivity import (
    Connectivity,
    Mermaid,
    register_unit_icon,
    lookup_unit_icon,
)
from idaes_connectivity import icons


@pytest.mark.unit
@pytest.mark.parametrize("indexed", [False, True])
def test_arc_ports(indexed, monkeypatch):
    model = ConcreteModel()
    model.fs = Block()
    model.fs.source = Block()
    model.fs.source.outlet = Port()
    model.fs.dest = Block()
    model.fs.dest.inlet = Port()
    ends = dict(source=model.fs.source.outlet, destination=model.fs.dest.inlet)
    if indexed:
        model.fs.link = Arc([1, 2], rule=lambda b, i: ends.copy())
        names = ["fs.link[1]", "fs.link[2]"]
    else:
        model.fs.link = Arc(**ends)
        names = ["fs.link"]

        def indexed_only():
            pytest.fail("Scalar Arc was treated as indexed")

        # ScalarArc.values() happens to work in Pyomo; guard the wrong branch.
        monkeypatch.setattr(model.fs.link, "values", indexed_only)
    conn = Connectivity(input_model=model)
    assert conn.stream_ports == {name: ("outlet", "inlet") for name in names}
    assert set(conn.streams) == set(names)
    assert list(conn.connections.values()) == [["Unit_B", "Unit_C"]] * len(names)
    assert set(conn.units) == {"fs.source", "fs.dest"}
    assert Connectivity(input_data=conn.as_table()).stream_ports == {}


@pytest.mark.unit
@pytest.mark.parametrize("stream_labels", [False, True])
@pytest.mark.parametrize("stream_values", [False, True])
def test_mermaid_port_labels(stream_labels, stream_values):
    model = ConcreteModel()
    model.source = Block()
    model.dest = Block()
    model.source.outlet = Port(["O'Brien"])
    model.dest.inlet = Port()
    model.link = Arc(
        source=model.source.outlet["O'Brien"], destination=model.dest.inlet
    )
    conn = Connectivity(input_model=model)
    conn.set_stream_value("link", "flow", 42)
    options = dict(stream_labels=stream_labels, stream_values=stream_values)
    default = Mermaid(conn, **options).write(None)
    assert "outlet" not in default
    labeled = Mermaid(conn, port_labels=True, **options).write(None)
    assert "outlet[#quot;O'Brien#quot;] -> inlet" in labeled
    assert 'outlet["' not in labeled
    if stream_labels:
        assert "link" in labeled
    if stream_values:
        assert "flow = 42" in labeled


@pytest.mark.unit
@pytest.mark.parametrize("indexed", [False, True])
def test_mscontactor_ports(monkeypatch, tmp_path, indexed):
    monkeypatch.setattr(icons, "_registry", {})
    model = ConcreteModel()
    model.fs = FlowsheetBlock(dynamic=False)
    model.fs.properties = SaponificationParameterBlock()
    streams = {
        name: {"property_package": model.fs.properties}
        for name in ("aqueous", "organic")
    }
    if indexed:
        model.fs.units = MSContactor(
            [1, 2], number_of_finite_elements=2, streams=streams
        )
        source, dest = model.fs.units[1], model.fs.units[2]
    else:
        model.fs.source = MSContactor(number_of_finite_elements=2, streams=streams)
        model.fs.dest = MSContactor(number_of_finite_elements=2, streams=streams)
        source, dest = model.fs.source, model.fs.dest
    model.fs.links = Block()
    for name in streams:
        model.fs.links.add_component(
            name,
            Arc(
                source=getattr(source, f"{name}_outlet"),
                destination=getattr(dest, f"{name}_inlet"),
            ),
        )
    conn = Connectivity(input_model=model, shortened_names=True)
    assert conn.stream_ports == {
        f"fs.links.{name}": (f"{name}_outlet", f"{name}_inlet") for name in streams
    }
    assert set(conn.units) == {source.local_name, dest.local_name}
    svg = tmp_path / "contactor.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    sides = {"aqueous_inlet": "left", "organic_inlet": "top"}
    register_unit_icon(MSContactor, svg, ports=sides)
    assert conn.get_unit_icon(source.local_name).svg_path == svg
    assert conn.get_unit_icon(source.local_name).ports == sides
    assert lookup_unit_icon(source).svg_path == svg
    assert lookup_unit_icon(MSContactor).svg_path == svg
    # Exercise image output without starting the existing image server.
    diagram = Mermaid(conn)
    diagram._images = True
    text = diagram.write(None)
    encoded = base64.b64encode(svg.read_bytes()).decode("ascii")
    assert text.count(f"data:image/svg+xml;base64,{encoded}") == 2


@pytest.mark.unit
def test_icon_fallback_order(monkeypatch, tmp_path):
    monkeypatch.setattr(icons, "_registry", {})

    class Base:
        pass

    class CustomMixer(Base):
        pass

    unit = CustomMixer()
    assert lookup_unit_icon(unit).svg_path.name == "mixer.svg"
    assert lookup_unit_icon(Base).svg_path is None
    for key, filename in (
        (__name__, "module.svg"),
        (Base, "base.svg"),
        (CustomMixer, "class.svg"),
    ):
        path = tmp_path / filename
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        register_unit_icon(key, path, ports={"inlet": "left"})
        assert lookup_unit_icon(unit).svg_path == path
        assert lookup_unit_icon(CustomMixer).ports == {"inlet": "left"}
    with pytest.raises(ValueError, match="Port sides"):
        register_unit_icon(CustomMixer, path, ports={"inlet": "diagonal"})
    with pytest.raises(FileNotFoundError):
        register_unit_icon(CustomMixer, tmp_path / "missing.svg")
    assert lookup_unit_icon(unit).svg_path == path
