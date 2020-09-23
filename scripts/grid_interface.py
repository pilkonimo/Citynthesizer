import numpy as np
import pickle, os, importlib
from . import path_interface
importlib.reload(path_interface)
"""Interface to grid stored in /data/grid.pkl . With various coordinate transformations."""


class Grid:
    """Grid class adapted from SceneCity/nodes/__init__.py"""
    def __init__(self, data, size, cell_size=1):
        self.data = data
        self.grid_size = size
        self.cell_size = cell_size


def get_grid_from_file(data_base_dir, grid_file):
    """Help function that gets grid data from file."""
    return pickle.load(open(os.path.join(data_base_dir, grid_file), "rb"))


def get_grid_from_data(data_dir):
    """Help function that returns Grid object from file. Due to bug in SceneCity cell_size always 1."""
    grid_data = np.array(get_grid_from_file(data_dir, "grid.pkl"))
    grid_size = grid_data.shape
    return Grid(grid_data, grid_size)


# coordinate transformations and functions
def coordtransform_grid_to_blender(grid_coord, grid):
    """Transforms grid_coord to corresponding blender coord in city."""
    (x, y) = grid_coord
    blender_coord = ((x - grid.grid_size[0] / 2) * grid.cell_size, (y - grid.grid_size[1]/2) * grid.cell_size, 0)
    return blender_coord


def coordtransform_blender_to_grid(blender_coord, grid):
    """Transforms blender_coord to corresponding grid coord in city."""
    (i, j, k) = blender_coord
    grid_coord = (i / grid.cell_size + grid.grid_size[0] / 2, j / grid.cell_size + grid.grid_size[1] / 2)
    return grid_coord


def get_blender_street_coord(node, grid):
    """Returns blender coord for car moving on the right street side by 0.15m from middle"""
    blender_coord = coordtransform_grid_to_blender(node.coord.data, grid)
    if (0, 0) != node.momentum.data:
        offset_x_y = node.momentum.swap_axis() * 0.15 * grid.cell_size / len(node.momentum)  # type: Vector
    else:
        offset_x_y = path_interface.Vector((0, 0))
    blender_street_coord = (
    blender_coord[0] + offset_x_y.data[0], blender_coord[1] - offset_x_y.data[1], blender_coord[2])
    return blender_street_coord


def get_border_streets(grid):
    """Returns list of tuples representing the streets on the city border in grid coordinates."""
    border_streets = [(0, j) for j, grid_dict in enumerate(grid.data[0, :]) if 'road' in grid_dict]
    border_streets.extend([(i, 0) for i, grid_dict in enumerate(grid.data[:, 0]) if 'road' in grid_dict])
    border_streets.extend(
        [(grid.grid_size[0] - 1, j) for j, grid_dict in enumerate(grid.data[grid.grid_size[0] - 1, :]) if 'road' in grid_dict])
    border_streets.extend(
        [(i, grid.grid_size[1] - 1) for i, grid_dict in enumerate(grid.data[:, grid.grid_size[1] - 1]) if 'road' in grid_dict])
    return border_streets


def get_start_end_point(car, grid):
    start_point_coord = car.nodes[0].coord - car.nodes[1].momentum
    zero_momentum = path_interface.Vector((0, 0))
    start_point = path_interface.Node(start_point_coord, zero_momentum)
    end_point = path_interface.Node(car.nodes[-1].coord + car.nodes[-1].momentum/len(car.nodes[-1].momentum), zero_momentum)
    start_point_blender = get_blender_street_coord(start_point, grid)
    end_point_blender = get_blender_street_coord(end_point, grid)
    return start_point_blender, end_point_blender


if __name__=="__main__":
    pass