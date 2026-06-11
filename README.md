# VisibleTouch
### Parametric CAD-to-Mold Pipeline

Automatically generates 3-part casting molds for tactile sensor bodies from a single YAML configuration file. Given sensor geometry and hardware specs, the pipeline produces three STL files (mold parts 1–3) and an interactive HTML assembly preview.

## Quick Start

```bash
pip install -r requirements.txt
python generate_model.py --sensor_info sensor_1.yaml
```

This outputs `sensor_1_mold1.stl`, `sensor_1_mold2.stl`, `sensor_1_mold3.stl`, and `sensor_1_assembly.html`.

## Mold Parts

| Part | Description |
|------|-------------|
| **Mold 1** | First-pour mold — defines the bottom geometry of the elastomer pad. Protrusions on its floor form blind cavities that seat the magnets in a later step. |
| **Mold 2** | Lower half of the second-pour mold — receives the partially-cured elastomer from Mold 1. Paired with Mold 3 to form the complete secondary cavity. |
| **Mold 3** | Upper half of the second-pour mold — clamped onto Mold 2 around the partially-cured elastomer. Includes a fill-line window so the elastomer level is visible during pouring. |

The split two-part design of Mold 2 + Mold 3 is necessary so the partially-cured elastomer can be loaded into the assembly; a single-piece mold of this geometry would not permit insertion.

## YAML Parameter Reference

All dimensions are in **millimeters**. The coordinate origin is at the center of the sensor footprint `(0, 0)`.

---

### `sensor`

Defines the physical dimensions of the sensor PCB/body.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `shape` | `"rectangular"` \| `"circular"` | Yes | Footprint shape of the sensor's active area |
| `size_x` | float | Yes | Overall sensor width (X), including the flat base flange |
| `size_y` | float | Yes | Overall sensor length (Y), including the flat base flange |
| `size_x_sensor` | float | If `shape: rectangular` | Active area width — the raised sensing region |
| `size_y_sensor` | float | If `shape: rectangular` | Active area length — the raised sensing region |
| `diameter` | float | If `shape: circular` | Diameter of the circular active area |
| `height` | float | Yes | Total sensor height from bottom to top of active area |
| `base_height` | float | Yes | Height of the flat base below the raised active area |

---

### `mounting_holes`

Through-holes for M-screws that align and clamp the mold halves together.

| Parameter | Type | Description |
|-----------|------|-------------|
| `diameter` | float | Hole diameter (add ~0.4 mm clearance over bolt shaft diameter) |
| `positions` | list of `[x, y]` | Hole center coordinates relative to sensor center |

---

### `magnets`

Cylindrical permanent magnets embedded in the sensor body for magnetic attachment. Mold 1 creates pockets accessible from the bottom; the lid (Mold 3) leaves clearance for insertion.

| Parameter | Type | Description |
|-----------|------|-------------|
| `diameter` | float | Magnet cylinder diameter |
| `height` | float | Magnet cylinder height (thickness) |
| `top_to_surface` | float | Distance from the top face of the magnet to the top surface of the sensor |
| `positions` | list of `[x, y]` | Magnet center coordinates relative to sensor center |

---

### `port_cutout`

A rectangular slot cut through the mold walls on the Y+ edge to route the sensor's cable or FPC connector.

| Parameter | Type | Description |
|-----------|------|-------------|
| `width` | float | Slot width (X direction) |
| `height` | float | Slot height (Z direction) |

---

### `observation_window`

A rectangular cutout in the side wall of Mold 3 that exposes the interior cavity, making the elastomer fill level visible during the second pour. The elastomer is poured until it reaches the bottom edge of this opening — that edge acts as the fill line.

| Parameter | Type | Description |
|-----------|------|-------------|
| `width` | float | Cutout width (X direction); the opening spans half the mold length in Y |

---

## Example Configurations

The repository includes three pre-configured sensors:

| File | Shape | Active Area | Magnets |
|------|-------|-------------|---------|
| `sensor_1.yaml` | Rectangular | 30.6 × 30.6 mm | 3 × 3 grid (9 magnets) |
| `sensor_2.yaml` | Circular | ⌀ 35 mm | 2 × 2 grid (4 magnets) |
| `sensor_3.yaml` | Rectangular | 35 × 23 mm | 2 × 3 grid (6 magnets) |

## Output Files

| File | Description |
|------|-------------|
| `<name>_mold1.stl` | Bottom mold half |
| `<name>_mold2.stl` | Top mold half |
| `<name>_mold3.stl` | Lid / alignment plate |
| `<name>_assembly.html` | Interactive 3D preview of all parts and sensor |

## Dependencies

See [requirements.txt](requirements.txt).
