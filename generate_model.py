import cadquery as cq
import argparse
import yaml
import os

def main():
    parser = argparse.ArgumentParser(description="Generate STL model from sensor info")
    parser.add_argument('--sensor_info', type=str, default='sensor_1.yaml', help='Path to the sensor info YAML file')
    args = parser.parse_args()

    # Read parameters from the YAML file
    with open(args.sensor_info, 'r') as f:
        sensor_data = yaml.safe_load(f)
        
    if 'sensor' not in sensor_data:
        raise ValueError("No corresponding parameter found: 'sensor'")
    sensor = sensor_data['sensor']

    try:
        shape = sensor.get('shape', 'rectangular')
        size_x = sensor['size_x']
        size_y = sensor['size_y']
        
        if shape == 'rectangular':
            size_x_sensor = sensor['size_x_sensor']
            size_y_sensor = sensor['size_y_sensor']
        elif shape == 'circular':
            sensor_diameter = sensor['diameter']
            
        height = sensor['height']
        base_height = sensor['base_height']
        
        mounting_holes = sensor_data['mounting_holes']
        hole_diameter = mounting_holes['diameter']
        hole_positions = mounting_holes['positions']
        
        magnets = sensor_data['magnets']
        magnet_top_to_surface = magnets['top_to_surface']
        magnet_diameter = magnets['diameter']
        magnet_positions = magnets['positions']
        magnet_height = magnets['height']
        
        port_cutout = sensor_data['port_cutout']
        port_cutout_width = port_cutout['width']
        port_cutout_height = port_cutout['height']
        
        observation_window = sensor_data.get('observation_window', {})
        observation_window_width = observation_window.get('width', 0)
    except KeyError as e:
        raise ValueError(f"No corresponding parameter found: {e.args[0]}")

    # Extrude a base box
    base_box = cq.Workplane("front").rect(size_x + 6, size_y + 6).extrude(height - magnet_top_to_surface + 3)

    # Extrude cut: (size_x, size_y, base_height)
    # .faces(">Z") selects the top face of the box.
    # .workplane() creates a new workplane on that face, centered by default.
    # .cutBlind(-base_height) cuts into the box by the base_height specified.
    mold1 = base_box.faces(">Z").workplane().rect(size_x, size_y).cutBlind(-base_height)

    # Second cut: from the floor of the previous cut
    # Depth is height - base_height
    mold1_cut = mold1.faces(">Z").workplane(offset=-base_height)
    if shape == 'rectangular':
        mold1_cut = mold1_cut.rect(size_x_sensor, size_y_sensor)
    elif shape == 'circular':
        mold1_cut = mold1_cut.circle(sensor_diameter / 2)
    mold1 = mold1_cut.cutBlind(-(height - magnet_top_to_surface - base_height))

    # Extrude cylinders for mounting holes from the top (going down)
    mold1 = mold1.faces(">Z").workplane().pushPoints(hole_positions).circle(hole_diameter / 2).extrude(-(height- magnet_top_to_surface))

    # Extrude cylinders from the bottom up (starting at height 3)
    mold1 = mold1.faces("<Z").workplane(offset=-3).pushPoints(magnet_positions).circle(magnet_diameter / 2).extrude(-magnet_height)

    # Extrude box centered at (0, size_y/2 - port_cutout.height/2), starting at height 3, with dimensions (port_cutout.width, port_cutout.height, height - magnet_top_to_surface)
    mold1 = mold1.faces("<Z").workplane(offset=-3).center(0, size_y / 2 - port_cutout_height / 2).rect(port_cutout_width, port_cutout_height).extrude(-(height - magnet_top_to_surface))

    # Output the result stl model
    yaml_name = os.path.splitext(os.path.basename(args.sensor_info))[0]
    output_filename = f"{yaml_name}_mold1.stl"
    cq.exporters.export(mold1, output_filename)

    # start mold2
    # First a base box with dimensions (size_x + 6, size_y + 6, height + 3)
    mold2 = cq.Workplane("front").rect(size_x + 6, size_y + 6).extrude(height + 3)

    # Then cut a box with dimensions (size_x, size_y, height) at center from the top
    mold2 = mold2.faces(">Z").workplane().rect(size_x, size_y).cutBlind(-height)

    # Extrude cylinders for mounting holes from the top (going down) with the same positions and diameter as before
    mold2 = mold2.faces(">Z").workplane().pushPoints(hole_positions).circle(hole_diameter / 2).extrude(-height)

    # Extrude box centered at (0, size_y/2 - port_cutout.height/2), starting at height 3, with dimensions (port_cutout.width, port_cutout.height, height)
    mold2 = mold2.faces("<Z").workplane(offset=-3).center(0, size_y / 2 - port_cutout_height / 2).rect(port_cutout_width, port_cutout_height).extrude(-height)

    output_filename2 = f"{yaml_name}_mold2.stl"
    cq.exporters.export(mold2, output_filename2)

    # start mold 3
    # first base box with dimensions (size_x+12, size_y + 12, 2) at center
    mold3 = cq.Workplane("front").rect(size_x + 12, size_y + 12).extrude(2)
    # then another box with dimensions (size_x - 0.8, size_y -0.8, sensor.height-sensor.base_height) at center from the top
    mold3 = mold3.faces(">Z").workplane().rect(size_x - 0.8, size_y - 0.8).extrude(height - base_height)
    # then extrude cut from the new top at 2+sensor.height-sensor.base_height down to the bottom
    mold3_cut = mold3.faces(">Z").workplane()
    if shape == 'rectangular':
        mold3_cut = mold3_cut.rect(size_x_sensor, size_y_sensor)
    elif shape == 'circular':
        mold3_cut = mold3_cut.circle(sensor_diameter / 2)
    mold3 = mold3_cut.cutBlind(-(2 + height - base_height))
    # Extrude box cut centered at (0, size_y/2 - (port_cutout.height+0.8)/2), starting at top height 2+sensor.height-sensor.base_height, with dimensions (port_cutout.width+0.8, port_cutout.height+0.8, sensor.height-sensor.base_height) down
    mold3 = mold3.faces(">Z").workplane().tag("top")
    mold3 = mold3.workplaneFromTagged("top").center(0, size_y / 2 - (port_cutout_height + 0.8) / 2).rect(port_cutout_width + 0.8, port_cutout_height + 0.8).cutBlind(-(height - base_height))

    # Extrude box cut centered at (0, -(size_y+12)/4)), starting at bottom height (0), with dimensions (observation_window_width, (size_y+12)/2, 2) up
    mold3 = mold3.faces("<Z").workplane(centerOption="CenterOfBoundBox").center(0, (size_y + 12) / 4).rect(observation_window_width, (size_y + 12) / 2).cutBlind(-2)
    
    # extrude cut cylinders for mounting holes from the top (going down) with the same positions as before, but diameter is hole_diameter + 0.8 for tolerance, and depth is the full height of 2+sensor.height-sensor.base_height
    mold3 = mold3.workplaneFromTagged("top").pushPoints(hole_positions).circle((hole_diameter + 0.8) / 2).cutBlind(-(2 + height - base_height))
    
    output_filename3 = f"{yaml_name}_mold3.stl"
    cq.exporters.export(mold3, output_filename3)
    
    # print output info
    print(f"Mold 1 Model successfully exported to {output_filename}")
    print(f"Mold 2 Model successfully exported to {output_filename2}")
    print(f"Mold 3 Model successfully exported to {output_filename3}")

    #Start sesnor model, put it into assembly with magnets for visualization
    sensor_model = cq.Workplane("front").rect(size_x, size_y).extrude(base_height)
    
    sensor_top = sensor_model.faces(">Z").workplane()
    if shape == 'rectangular':
        sensor_model = sensor_top.rect(size_x_sensor, size_y_sensor).extrude(height - base_height)
    elif shape == 'circular':
        sensor_model = sensor_top.circle(sensor_diameter / 2).extrude(height - base_height)

    # Extrude cut box centered at (0, size_y/2 - port_cutout.height/2), starting at bottom, with dimensions (port_cutout.width, port_cutout.height, height)  cut through all height
    sensor_model = sensor_model.faces("<Z").workplane().tag("bottom")
    sensor_model = sensor_model.workplaneFromTagged("bottom").center(0, size_y / 2 - port_cutout_height / 2).rect(port_cutout_width, port_cutout_height).cutBlind(-height)
    
    sensor_model = sensor_model.workplaneFromTagged("bottom").pushPoints(hole_positions).circle(hole_diameter / 2).cutBlind(-height)
    
    #Start magnets model
    #just extrude a cylinder of magnet_diameter and magnet_height
    magnets_model = cq.Workplane("front").circle(magnet_diameter / 2).extrude(magnet_height)

    #start assembly
    #put sensor model at origin, then put magnets at the corresponding magnet positions and height(the top of the magnet cylinder surface is at magnet_top_to_surface from the top of the sensor inside of the sensor model. Then visualize the assembly with plotly. Sensor model is green transparent, and magnets are solid red.)
    
    import plotly.graph_objects as go
    
    def get_mesh3d(cq_solid, color, opacity=1.0):
        # tessellate returns vertices and triangular faces (indices)
        vertices, faces = cq_solid.val().tessellate(0.1)
        x = [v.x for v in vertices]
        y = [v.y for v in vertices]
        z = [v.z for v in vertices]
        i = [f[0] for f in faces]
        j = [f[1] for f in faces]
        k = [f[2] for f in faces]
        return go.Mesh3d(
            x=x, y=y, z=z, i=i, j=j, k=k, 
            color=color, opacity=opacity, flatshading=False,
            lighting=dict(ambient=0.4, diffuse=0.8, specular=0.3, roughness=0.5, fresnel=0.2),
            lightposition=dict(x=100, y=200, z=500)
        )

    fig = go.Figure()

    display_height = 30
    
    # Add mold models
    fig.add_trace(get_mesh3d(mold1.translate((0, 0, -display_height)), color='lightgrey', opacity=1.0))
    fig.add_trace(get_mesh3d(mold2.translate((0, 0, 0)), color='lightgrey', opacity=1.0))
    fig.add_trace(get_mesh3d(mold3.rotate((0, 0, 0), (0, 1, 0), 180).rotate((0, 0, 0), (0, 0, 1), 180).translate((0, 0, display_height)), color='lightgrey', opacity=1.0))
    
    sensor_position = 90
    # Add sensor model (transparent gray), shifted by (0, sensor_position, 0)
    fig.add_trace(get_mesh3d(sensor_model.translate((0, sensor_position, 0)), color='gray', opacity=0.3))
    
    # Evaluate where magnets go
    magnet_base_z = height - magnet_top_to_surface - magnet_height

    # Add each magnet translated to its position (shifted by y=60 to match sensor, solid black)
    for pos in magnet_positions:
        placed_magnet = magnets_model.translate((pos[0], pos[1] + sensor_position, magnet_base_z))
        fig.add_trace(get_mesh3d(placed_magnet, color='black', opacity=1.0))
        
    fig.update_layout(
        scene=dict(aspectmode='data'),
        title="All Models Assembly Visualization",
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.0,
                xanchor="left",
                y=0.95,
                yanchor="top",
                showactive=True,
                buttons=[
                    dict(
                        label="Grid On",
                        method="relayout",
                        args=[{
                            "scene.xaxis.visible": True, "scene.yaxis.visible": True, "scene.zaxis.visible": True
                        }]
                    ),
                    dict(
                        label="Grid Off",
                        method="relayout",
                        args=[{
                            "scene.xaxis.visible": False, "scene.yaxis.visible": False, "scene.zaxis.visible": False
                        }]
                    )
                ]
            )
        ]
    )
    
    html_name = f"{yaml_name}_assembly.html"
    fig.write_html(html_name)
    print(f"Assembly visualization generated to {html_name}")

if __name__ == "__main__":
    main()
