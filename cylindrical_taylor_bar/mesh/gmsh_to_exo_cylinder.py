import sys
import subprocess
import gmsh
import exodus
import numpy as np

def create_gmsh_cylinder(height, radius, mesh_size, out_file_base):
    # Initialize gmsh
    gmsh.initialize()
    
    # Create a new model
    gmsh.model.add("Cylinder")
    
    # Add a cylinder
    cylinder_tag = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, height, radius)
    
    # Synchronize the CAD kernel with the Gmsh model
    gmsh.model.occ.synchronize()
    
    # Set the mesh size for the points at the bottom and top faces
    # Get the points of the bottom and top circle
    bottom_circle = gmsh.model.getEntitiesInBoundingBox(-radius, -radius, 0, radius, radius, 0, 0)
    top_circle = gmsh.model.getEntitiesInBoundingBox(-radius, -radius, height, radius, radius, height, 0)
    
    # Combine the points and filter for dimension 0 (points)
    points = [pt for pt in bottom_circle + top_circle if pt[0] == 0]
    
    # Set mesh size at the points
    for point in points:
        gmsh.model.mesh.setSize([point], mesh_size)
    
    # Define a physical group for the whole cylinder
    gmsh.model.addPhysicalGroup(3, [cylinder_tag], tag=1)
    gmsh.model.setPhysicalName(3, 1, "Cylinder")
    
    # Generate a 3D mesh
    gmsh.model.mesh.generate(3)
    
    # Save the mesh to a file
    gmsh.write(out_file_base+".msh")
    
    # Finalize the gmsh API
    gmsh.finalize()

def convert_gmsh_to_exo(out_file_base):
    # Convert the Gmsh mesh to ExodusII format using meshio
    subprocess.run(["meshio", "convert", out_file_base+".msh", out_file_base+"_meshio.e"])
    
def add_nodeset_and_fix_exo(out_file_base):
    in_file = out_file_base+"_meshio.e"
    out_file = out_file_base+".exo"

    # Open the existing ExodusII file
    # Struggled to add nodesets to meshio file, so just grab the nodes and connectivity and create a new file
    exo_in = exodus.exodus(in_file, mode='r')
    
    # Get the coordinates of all nodes
    points = np.array(exo_in.get_coords()).T  # Transpose to get (n_nodes, 3)
    
    # Leading face nodes
    nodeset_nodes = np.where(points[:, 2] == 0)[0] + 1  # Convert to 1-based indexing
    
    # Element connectivity
    elements = np.array(exo_in.get_elem_connectivity(0)[0])
    num_elements = exo_in.num_elems()
    
    # Create an ExodusII file and write the mesh data
    exo_out = exodus.exodus(out_file, mode='w',
                            array_type='numpy', title="Cylinder Mesh",
                            numDims=3, numNodes=points.shape[0],
                            numElems=num_elements, numBlocks=1,
                            numNodeSets=1)
    
    # Write coordinates
    exo_out.put_coords(points[:, 0], points[:, 1], points[:, 2])
    
    # Write element block info
    exo_out.put_elem_blk_info(1, "TET4", num_elements, 4, 0)
    exo_out.put_elem_connectivity(1, elements.flatten())
    
    # Write nodeset info
    exo_out.put_set_params('EX_NODE_SET', 1, nodeset_nodes.shape[0], 0)
    exo_out.put_node_set(1, nodeset_nodes)
    
    # Add names to the element block and nodeset
    exo_out.put_names("EX_ELEM_BLOCK", ["block_1"])
    exo_out.put_names("EX_NODE_SET", ["nodeset_1"])
    
    # Close the ExodusII files
    exo_out.close()
    exo_in.close()
    
    print(f"ExodusII file '{out_file}' created successfully.")

if __name__ == "__main__":

    # Define the parameters
    mesh_size = 0.01  # Define the desired mesh size
    height = 0.2346
    radius = 0.0391

    out_file_base = "cylinder"+str(mesh_size).replace('.','p')

    create_gmsh_cylinder(height, radius, mesh_size, out_file_base)

    convert_gmsh_to_exo(out_file_base)

    add_nodeset_and_fix_exo(out_file_base)

