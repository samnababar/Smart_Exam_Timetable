def greedy_graph_coloring(adjacency, subject_order):
    """Greedy coloring for an undirected graph.

    subject_order is a list of subject IDs in the order to process.
    """
    color_map = {}
    for subject_id in subject_order:
        used_colors = {color_map.get(neighbor) for neighbor in adjacency.get(subject_id, []) if neighbor in color_map}
        used_colors.discard(None)
        color = 0
        while color in used_colors:
            color += 1
        color_map[subject_id] = color
    return color_map
