import random
"""Interface that handles space- and velocity-information of the paths for each car."""


class Vector:
    """2D Vector allowing elementwise addition, subtraction, multiplication with scalar"""
    def __init__(self, x_y):
        if len(x_y) == 2:
            self.data = x_y
        else:
            raise RuntimeError("Only 2D vectors supported.")

    def __getitem__(self, key):
        if key > 1:
            raise RuntimeError("Index not in range for 2D vector.")
        return self.data[key]

    def __mul__(self, scalar):
        if not isinstance(scalar, float) and not isinstance(scalar, int):
            raise RuntimeError("Only scalar multiplication.")
        return Vector((scalar*self.x(), scalar*self.y()))

    def __truediv__(self, scalar):
        if not isinstance(scalar, float) and not isinstance(scalar, int):
            raise RuntimeError("Only scalar multiplication.")
        if scalar == 0:
            raise RuntimeError("Division by ")
        return Vector((self.x()/scalar, self.y()/scalar))

    def __add__(self, other):
        if not isinstance(other, Vector):
            raise RuntimeError("Only vectoraddition")
        return Vector((self.x() + other.x(), self.y() + other.y()))

    def __sub__(self, other):
        if not isinstance(other, Vector):
            raise RuntimeError("Only vectoraddition")
        return Vector((self.x() - other.x(), self.y() - other.y()))

    def is_parallel_to(self, other) -> bool:
        """Definition: Every vector parallel to origin."""
        if len(self) == 0 or len(other) == 0:
            return True
        return (other/len(other)).data == (self/len(self)).data

    def is_anti_parallel_to(self, other) -> bool:
        """Definition: Every vector parallel to origin."""
        if len(self) == 0 or len(other) == 0:
            return True
        return self.is_parallel_to(other * -1)

    def z_comp_cross_product(self, other):
        """Returns z component of the right hand cross product"""
        return self.data[0]*other.data[1] - self.data[1]*other.data[0]

    def swap_axis(self):
        return Vector((self.data[1], self.data[0]))

    def __len__(self):
        return abs(self.x()) + abs(self.y())

    def __str__(self):
        return '(' + str(self.x()) + ',' + str(self.y()) + ')'

    def x(self):
        return self.data[0]

    def y(self):
        return self.data[1]

    def data(self):
        return self.data


class Node:
    """Node of path with space and velocity information."""
    def __init__(self, coord, momentum):
        #if not isinstance(coord, Vector) or not isinstance(momentum, Vector):
        #    raise RuntimeError("Coordinate and momentum have to be 2D Vectors.")
        self.coord = coord
        self.momentum = momentum

    def __str__(self):
        return f"coord: {self.coord.data}, momentum:{self.momentum.data}"


def create_random_path(start_points, border_streets, grid):
    """Randomly create a path from border to border of city.

    Parameters
    ----------
    start_points    :   list
        List of possible start points in grid-coordinates.
    border_streets  :   list
        List of tuples as grid-coordinates of streets on city border.
    grid : Grid
        data attr is (nxm)-matrix with elements being dicts that contain the SceneCity key,value-pairs.

    Returns
    -------
    list of Node
        List containing nodes with coord and momentum of cars on randomly chosen path in correct order.
    """
    # choose start point and remove from available start points
    start_point = random.choice(start_points)
    start_points.remove(start_point)
    nodes = [Node(Vector(start_point), Vector((0, 0)))]
    directions = [Vector((1, 0)), Vector((-1, 0)), Vector((0, 1)), Vector((0, -1))]
    next_node = Node(Vector((grid.grid_size[0]/2, grid.grid_size[1]/2)), Vector((0, 0)))  # middle node not on border
    while next_node.coord.data not in border_streets:
        if len(nodes) <= 1:
            previous_node = Node(Vector(grid.grid_size), Vector((0, 0)))  # definitely not on grid
        else:
            previous_node = nodes[-2]
        current_node = nodes[-1]
        #print('current_node', current_node.coord.data, coordtransform_grid_to_blender(current_node.coord.data, grid))
        # get neighbouring nodes and filter non-street nodes
        neighbours = [Node(coord=current_node.coord + direction, momentum=direction)
                      for direction in directions]
        #print('neighbours', [(neighbour.coord.data, coordtransform_grid_to_blender(neighbour.coord.data, grid)) for neighbour in neighbours])
        neighbours = [node for node in neighbours if 0 <= node.coord.x() < grid.grid_size[0]
                      and 0 <= node.coord.y() < grid.grid_size[1]]
        neighbours = [node for node in neighbours if 'road' in grid.data[node.coord[0]][node.coord[1]]
                      and node.coord.data != previous_node.coord.data]
        #print('filtered neighbours', [(neighbour.coord.data, coordtransform_grid_to_blender(neighbour.coord.data, grid)) for neighbour in neighbours])
        # add up momenta or introduce curve
        for node in neighbours:
            if current_node.momentum.is_parallel_to(node.momentum):
                node.momentum = current_node.momentum + node.momentum
            # ToDo-me: else add more nodes/increase weight (-> add as attr to Node) to get better curvature
        next_node = random.choice(neighbours)
        #print('next_node second', next_node.coord.data, coordtransform_grid_to_blender(next_node.coord.data, grid))
        nodes.append(next_node)

    return nodes
