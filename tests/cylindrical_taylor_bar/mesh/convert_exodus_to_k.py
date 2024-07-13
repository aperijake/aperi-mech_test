import exodus
import numpy as np

## not sure this works. needs testing

def convert_exodus_to_lsdyna(exodus_file, dyna_file):
    # Open the Exodus file
    exo = exodus.exodus(exodus_file, mode='r')
    
    # Get the nodes
    num_nodes = exo.num_nodes()
    print(f"Number of nodes: {num_nodes}")
    node_coords = exo.get_coords()
    node_ids = exo.get_node_id_map()

    # Get the elements
    num_elems = exo.num_elems()
    print(f"Number of elements: {num_elems}")
    elem_blk_ids = exo.get_elem_blk_ids()
    elem_blocks = {}
    for blk_id in elem_blk_ids:
        elem_blocks[blk_id] = {
            'num_elem': exo.num_elems_in_blk(blk_id),
            'num_nodes_per_elem': exo.num_nodes_per_elem(blk_id),
            'connectivity': exo.get_elem_connectivity(blk_id),
            'ids': exo.get_elem_id_map()
        }

    # Get node sets
    node_set_ids = exo.get_node_set_ids()
    node_sets = {}
    for set_id in node_set_ids:
        node_sets[set_id] = exo.get_node_set_nodes(set_id)

    # Open the LS-DYNA keyword file for writing
    with open(dyna_file, 'w') as f:
        f.write("*KEYWORD\n")
        
        # Write the nodes
        f.write("*NODE\n")
        for i in range(num_nodes):
            f.write(f"{node_ids[i]:>8}{node_coords[0][i]:>16.8e}{node_coords[1][i]:>16.8e}{node_coords[2][i]:>16.8e}\n")
        
        # Write the elements
        for blk_id, blk_data in elem_blocks.items():
            f.write("*ELEMENT_SOLID\n")
            for i in range(blk_data['num_elem']):
                elem_id = blk_data['ids'][i]
                # Assuming blk_data['connectivity'] is a tuple where the first item is the connectivity array
                connectivity_array = blk_data['connectivity'][0]  # Extract the connectivity array
                # Now index into connectivity_array
                connectivity = [connectivity_array[j] for j in range(i*blk_data['num_nodes_per_elem'], (i+1)*blk_data['num_nodes_per_elem'])]
                f.write(f"{elem_id:>8}{'1':>8}" + "".join([f"{node_id:>8}" for node_id in connectivity]) + "\n")

        # Write the node sets
        nodes_per_line = 8
        for set_id, nodes in node_sets.items():
            f.write("*SET_NODE_LIST_TITLE\n")
            f.write("NODESET(SPC) 1\n")
            f.write(f"{1:>10}\n")
            for i, node in enumerate(nodes, start=1):
                f.write(f"{node:>10}")
                if i % nodes_per_line == 0:
                    f.write("\n")
            if len(nodes) % nodes_per_line != 0:
                f.write("\n")  # Ensure there's a newline at the end if the last line isn't full
        
        f.write("*END\n")
    
    # Close the Exodus file
    exo.close()

# Example usage
convert_exodus_to_lsdyna("cylinder0p01.exo", "cylinder0p01.k")

