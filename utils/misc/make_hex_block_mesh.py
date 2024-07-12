# TODO(jake): This needs work. It won't run as is. It's a starting point for creating a hexahedral mesh.
import exodus
import numpy as np

def create_hexahedron_mesh_exodus(N, M):
    # Create a new Exodus file
    exo = exodus.exodus("hexahedron_mesh.exo", mode='w', array_type="numpy", title="Hexahedral Mesh")

    # Define the coordinates of the nodes
    node_coords_x = []
    node_coords_y = []
    node_coords_z = []
    for k in range(M + 1):
        for j in range(N + 1):
            for i in range(N + 1):
                node_coords_x.append(i)
                node_coords_y.append(j)
                node_coords_z.append(k)

    # Write the coordinates to the Exodus file
    exo.put_coords(np.array(node_coords_x), np.array(node_coords_y), np.array(node_coords_z))

    # Define the connectivity (elements)
    elem_conn = []
    for k in range(M):
        for j in range(N):
            for i in range(N):
                elem_conn.append([
                    i + j * (N + 1) + k * (N + 1) * (N + 1),
                    i + 1 + j * (N + 1) + k * (N + 1) * (N + 1),
                    i + 1 + (j + 1) * (N + 1) + k * (N + 1) * (N + 1),
                    i + (j + 1) * (N + 1) + k * (N + 1) * (N + 1),
                    i + j * (N + 1) + (k + 1) * (N + 1) * (N + 1),
                    i + 1 + j * (N + 1) + (k + 1) * (N + 1) * (N + 1),
                    i + 1 + (j + 1) * (N + 1) + (k + 1) * (N + 1) * (N + 1),
                    i + (j + 1) * (N + 1) + (k + 1) * (N + 1) * (N + 1)
                ])

    # Write the connectivity to the Exodus file
    num_elements = len(elem_conn)
    exo.put_elem_blk_info(1, "HEX", num_elements, 8)
    exo.put_elem_connectivity(1, np.array(elem_conn))
    # help(exo)

    # Define the surface sideset
    surface_nodes = []
    for k in range(M + 1):
        for j in range(N + 1):
            for i in range(N + 1):
                if k == 0:  # nodes on the face with normal pointing in negative z-direction
                    surface_nodes.append(i + j * (N + 1) + k * (N + 1) * (N + 1))

    # Write the sideset to the Exodus file
    num_surface_nodes = len(surface_nodes)
    surface_nodes_ids = np.array(surface_nodes, dtype=np.int32)
    exo.put_node_set_params("surface_1", num_surface_nodes)
    exo.put_node_set(surface_nodes_ids)

    # Close the Exodus file
    exo.close()

# Example usage:
N = 4  # Number of elements along x and y axes
M = 12  # Number of elements along z axis
create_hexahedron_mesh_exodus(N, M)

