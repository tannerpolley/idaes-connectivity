---
myst:
  substitutions:
    proj: 'IDAES Connectivity Tool'
---
# Making diagrams

Formatting of connectivity information as a diagram relies on external tools.
While this does require an extra step to install and run these tools, it also
provides flexibility and leverages the full power of the tools' user
communities.

Below are links an instructions for the supported tools, [](mermaid-tool) and
[](d2-tool). Both tools do roughly the same thing: create diagrams from text,
with automatic layout. Mermaid, written in JavaScript, has an online editor and
built-in support in GitHub and Jupyter notebooks whereas D2, written in Go, has
more flexible layout options and is easier to use in the console.

(mermaid-tool)=
## Mermaid
[Mermaid](https://mermaid.js.org/) describes itself as a "JavaScript based diagramming and charting tool that renders Markdown-inspired text definitions to create and modify diagrams dynamically".
The {{ proj }} can create Mermaid text definitions and also has a convenience function to help render Mermaid diagrams inside a Jupyter Notebook.

### Generate text definition
For example, to generate Mermaid text from connectivity data in the CSV file
*model_conn.csv*, you could run:

```
idaes-conn --to mermaid model_conn.csv -O "-"
```

This will print the text definition of the diagram to the console.

### Generate diagram

#### Jupyter / GitHub

You could then paste the output into a Jupyter Notebook markdown cell, or GitHub
markdown page, like this:

:::{code}
```mermaid
<PASTE TEXT HERE>
```
:::

#### Online Editor

You could also load these diagrams into the online
[Mermaid Live Editor](https://mermaid.live/).

#### Console
If you want to generate the diagram locally, and are willing and able to install
NodeJS packages on your machine, then follow these instructions:

First install the mermaid-cli with the
[Node Package Manager](https://www.npmjs.com/) (install that first if you don't
have it):
```
npm install @mermaid-js/mermaid-cli
```
This will install wherever you ran the command. Make sure you run the next
commands in the same directory.

Now, you can generate an image with the `idaes-conn` command by adding the
option `--mmdc`:
```
idaes-conn --to mermaid --mmdc model_conn.csv -O model_diagram.png
```

The `--to mermaid` is optional as Mermaid is the default.

## Registering unit icons

Register an SVG for a custom unit class or its fully qualified Python module
name before rendering. Registrations last for the Python process; registering
the same key again replaces it.

```python
from idaes_connectivity import Connectivity, Mermaid, register_unit_icon
from idaes.models.unit_models import MSContactor

register_unit_icon(MSContactor, "contactor.svg", ports={
    "aqueous_inlet": "left", "aqueous_outlet": "right",
    "organic_inlet": "top", "organic_outlet": "bottom",
})
conn = Connectivity(input_model=model)
icon = conn.get_unit_icon("fs.contactor")  # svg_path and ports
text = Mermaid(conn, component_images=True, port_labels=True).write(None)
```

Lookup tries the unit's class, its base classes in Python method resolution
order, then their module names in the same order, then the existing
`ComponentNames` mapping. If nothing matches, the unit remains a plain box
(`svg_path=None`). IDAES block classes and their data classes share a registration,
so an icon applies to both scalar units and indexed unit elements.
Registered paths are absolute; bundled filenames are relative
to Mermaid's component image directory. Registered SVGs are embedded in Mermaid
as data URLs. Port sides are optional hints for diagram consumers; Mermaid does
not position ports.

`conn.stream_ports` maps each model Arc name to a `(source_port, destination_port)`
tuple, with port names local to their parent units. CSV and tabular inputs have
no port metadata. Mermaid's `port_labels=True` adds these names to edges and can
be combined with `stream_labels=True`. Both options are off by default.

(d2-tool)=
## D2
[Declarative Diagramming (D2)](https://d2lang.com/) describes itself as "A
modern language that turns text to diagrams". Like Mermaid, D2 generates a SVG
diagram from a simple text description.

### Generate text definition
For example, to generate D2 text from connectivity data in the CSV file
*model_conn.csv*, you could run:
```
idaes-conn --to d2 model_conn.csv -O model_conn.d2
```

This will print the text definition of the diagram to the file *model_conn.d2*

### Generate diagram

To generate the diagram,
[install D2 on your computer](https://d2lang.com/tour/install) and then run the
`d2` command-line interface (CLI) with the file you generated above as input:
```
d2 model_conn.d2 model_conn.svg
```

There are numerous options to the `d2` CLI that can help modify layout and
style, as well as the program behavior. For example, specifying an output file
with ".png" as the suffix will generate a PNG image. Run `d2 -h` to see them
and/or visit the documentation on the website.

```{note}
Unlike Mermaid, D2 does not have an online editor or Jupyter integration. On the other hand, generating diagrams locally is straightforward.
```
