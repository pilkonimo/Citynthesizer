import bpy
import re, time, random, copy, importlib, logging
from . import blender_car_interface
from . import grid_interface
from . import path_interface
from . import filtering
importlib.reload(blender_car_interface)
importlib.reload(grid_interface)
importlib.reload(path_interface)
importlib.reload(filtering)
"""Script to add and animate cars in city defined in /data/grid.pkl"""


def get_car_pool(car_models_info):
    """Creates pool of Car objects from userdefined metadata.

    Parameters
    ----------
    car_models_info    :   list of dict
        Each dict contains "file path" to .blend file of model, "main object name" of top parent and "scaling factor"
        and "camera_pos" .


    Returns
    -------
    list of Car
        Returns list of initialized Car-objects.
    """
    return [Car(info['file path'], info['main object name'], info['scaling factor'], info['camera_pos'])
            for info in car_models_info]


class Car:
    """Class that bundles user-defined-metadata about car, instantiates, if necessary and saves movement in city.

    Attributes
    ----------
    file_path   :   str
        Path to .blend-file containing the car-model.
    main_object_name    :   str
        Name of top-parent of blender-object, that is responsible for scaling, translation and rotation.
    scaling_factor  :   float
        Factor by which the model is scaled to fit into the city.
    camera_pos:
        Location of camera relative to the car's center.
    main_object :   blender object
        Top-parent of the car-model.
    curve   :   blender object
        Curve on which car is animated.
    camera  :   blender object
        Camera bound to car to generate groundtruth.
    nodes   :   list of Node
        Ordered list containing nodes with coord and momentum to model car's animation.
    grid_path_coordinates   :
        Grid coordinates of path.
    frames_per_node :   int
        Number of frames the car needs to pass one node of its path with constant velocity.


    Methods
    -------
    append()
        Appends the model from the .blend-file in file_path to current scene and set main_object.
    get_frames_for_pos(node_index)
        Returns interval of frames, in which the car will be in the node of given index of its path
    get_pos_for_frame(frame)
        Returns index of path-node the car is in in given frame
    update_grid_path()
        Sets grid path taken from nodes' coordinates.
    predict_movement_at_pos(pos)
        Returns direction as str, depending on momenta of node with index pos and pos+1
    """
    def __init__(self, path_to_blendfile, main_object_name, scaling_factor, camera_pos):
        self.file_path = path_to_blendfile
        self.main_object_name = main_object_name
        self.scaling_factor = scaling_factor
        self.camera_pos = camera_pos
        self.main_object = None
        self.curve = None
        self.camera = None
        self.nodes = None
        self.grid_path_coordinates = None
        self.frames_per_node = random.randint(1, 5)

    def append(self):
        with bpy.data.libraries.load(self.file_path) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects]   # if name.startswith("Chocofur")]

        # link them to scene
        main_object = None
        scene = bpy.context.scene
        for obj in data_to.objects:
            if obj is not None:
                scene.collection.objects.link(obj)
                if re.match(r"^" + self.main_object_name + r"(\.\d{3})?$", obj.name):
                    self.main_object = obj
        self.main_object.scale = tuple([self.scaling_factor for _ in range(3)])
        return self.main_object

    def get_frames_for_pos(self, node_index):
        """Returns interval of frames, in which the car will be in the node of given index of its path"""
        # Definite frames by linear velocity approximation
        frames = [self.frames_per_node * node_index + i for i in range(self.frames_per_node)]
        # puffer frames
        #frames.insert(0, frames[0]-1)
        #frames.insert(len(frames), frames[len(frames)-1]+1)
        return frames

    def get_pos_for_frame(self, frame):
        """Returns index of node of path the car is in given frame"""
        return frame // self.frames_per_node

    def update_grid_path(self):
        """Set grid path from nodes"""
        if not self.nodes:
            return
        self.grid_path_coordinates = [node.coord.data for node in self.nodes]

    def predict_movement_at_pos(self, pos):
        """Position is given as index of nodes. Turn is determined via cross product of momenta."""
        if pos + 1 > len(self.nodes) - 1:
            raise RuntimeError("Nothing to predict at end of path.")
        z_comp_cross_product = self.nodes[pos].momentum.z_comp_cross_product(self.nodes[pos + 1].momentum)
        if z_comp_cross_product < 0:
            return "right"
        if z_comp_cross_product > 0:
            return "left"
        return "straight"


def add_cars_to_city(car_models_info, data_dir, number_cars=5, min_number_cars=4, min_path_length=5, render_steps=1):
    """Randomly chosen cars are randomly animated along streets of city, defined by grid.

    Parameters
    ----------
    car_models_info : list of dict
        Each dict contains "file path" to .blend file of model, "main object name" of top parent and "scaling factor".
    data_dir    : str
        Path to folder of .pkl file containing grid_data.
    number_cars : int
        Number of cars that should be animated.
    min_number_cars : int
        Minimum number of cars that should be animated.
    min_path_length :   int
        Minimum path-length of camera holding car.
    render_steps    :   int
        Steps in which frames are rendered.

    Returns
    -------
    bool
        True if implemented cars exceed minimum number and half of the initially available start points.
    list of int
        List containing frames, with one frame per node, to be rendered.
    """
    logging.info('Start add_cars_to_city')
    start_time = time.time()
    # evaluating street setup
    grid = grid_interface.get_grid_from_data(data_dir)
    border_streets = grid_interface.get_border_streets(grid)
    available_start_points = border_streets[:]
    number_start_points = len(available_start_points)
    logging.info(f'available_start_points: {available_start_points}')

    # choosing and implementing cars from car_pool
    car_pool = get_car_pool(car_models_info)
    cars = [copy.deepcopy(car) for car in random.choices(car_pool, k=number_cars)]
    # test to accelerate generation
    cars[0].frames_per_node = 3

    # set random paths
    for i, car in enumerate(cars):
        car.nodes = path_interface.create_random_path(available_start_points, border_streets, grid)
        car.update_grid_path()

        logging.info(f'added car {car.main_object_name}, '
                     f'frames_per_node: {car.frames_per_node}, '
                     f'{len(car.nodes)} nodes, '
                     f'path coord: {[node.coord.data for node in car.nodes]}, '
                     f'momentum coord: {[node.momentum.data for node in car.nodes]}, '
                     f'at frames: {[car.get_frames_for_pos(i) for i in range(len(car.nodes))]}, '
                     f'takes turns: {[car.predict_movement_at_pos(i) for i in range(1,len(car.nodes)-1)]}')

        if not available_start_points:
            break

    # reduce list to cars with paths
    cars = [car for car in cars if car.nodes]
    logging.info(f'{len(cars)} cars with paths before avoid collisions')

    # truncate to avoid collisions
    for i, car in enumerate(cars[1:], start=1):
        avoid_collisions(car, [prev_car for prev_car in cars[:i] if len(car.nodes) > 1])

    # reduce to cars with a minimal path length of 2
    cars = [car for car in cars if len(car.nodes) > 1]
    logging.info(f'{len(cars)} cars with paths after avoid collisions')

    # check if scene is worth to render
    if len(cars) < min_number_cars or len(cars) <= number_start_points / 2 or len(cars[0].nodes) <= min_path_length or \
            all(["straight" == cars[0].predict_movement_at_pos(i) for i in range(1, len(cars[0].nodes)-1)]):
        # return render_worth_it, rendering_frames
        return False, []

    render_worth = True

    # animate cars, first implemented car carries only camera in the scene
    for i, car in enumerate(cars):
        blender_path_coordinates = [grid_interface.get_blender_street_coord(node, grid) for node in car.nodes]
        blender_path_weights = [1 for _ in car.nodes]
        start_point, end_point = grid_interface.get_start_end_point(car, grid)
        blender_car_interface.animate_car(blender_path_coordinates, start_point, end_point, blender_path_weights,
                                          car.main_object_name + "Path", car, data_dir, with_camera=i == 0)
        if i == 0:
            blender_car_interface.set_camera_car(car)

    # create rendering frames, render till last turn to avoid depicting the city edge
    end_frame = cars[0].frames_per_node * (len(cars[0].nodes)) - cars[0].frames_per_node
    nodes_of_turns = [i for i in range(1, len(cars[0].nodes) - 1) if cars[0].predict_movement_at_pos(i) != "straight"]
    if nodes_of_turns:
        end_frame = nodes_of_turns[-1]*cars[0].frames_per_node
    logging.info(f'end_frame: {end_frame}, nodes of turns: {nodes_of_turns}')
    rendering_frames = list(range(cars[0].frames_per_node, end_frame, render_steps))

    # set end-frame to end-frame of car carrying camera
    bpy.data.scenes[0].frame_end = end_frame
    logging.info(f'set last frame to {bpy.data.scenes[0].frame_end}')
    logging.info(f'{len(cars)} cars added to city - execution Time: {time.time() - start_time} s')
    print(f'{len(cars)} cars added to city - execution Time: {time.time() - start_time} s')
    return render_worth, rendering_frames


def avoid_collisions(car, prev_cars):
    """If main_car collides (same grid-cell) with any implemented cars, its path is truncated before first collision"""
    #logging.info(f'Avoid collisions for {car.main_object_name} with path {car.grid_path_coordinates}')
    while collision(car, prev_cars):
        car.nodes = car.nodes[:len(car.nodes) - 1]
        car.update_grid_path()
        #logging.info('truncated')
        if len(car.nodes) == 1:
            break


def collision(car, prev_cars):
    """True if car collides with any previously checked cars."""
    if stops_not_correct(car, prev_cars):
        # check that car does not stops in the path of previously checked cars
        #logging.info('stops_not_correct: true')
        return True
    if drives_not_correct_standing(car, prev_cars):
        # check that car does not drive through already stopped cars
        #logging.info('drives_not_correct_standing: true')
        return True
    if drives_not_correct_driving(car, prev_cars):
        #logging.info('drives_not_correct_driving: true')
        return True
    return False


def stops_not_correct(car, driving_cars):
    """True if car stops in any path of driving_car before it has passed."""
    #logging.info('start stops_not_correct')
    stop_point = car.grid_path_coordinates[len(car.grid_path_coordinates) - 1]
    stop_frame = (len(car.nodes) - 1) * car.frames_per_node
    #logging.info(f'car {car.main_object_name} stops at {stop_point} during frame {stop_frame}')
    for driving_car in driving_cars:
        #logging.info(f'checking driving car {driving_car.main_object_name} with path {driving_car.grid_path_coordinates}')
        if stop_point not in driving_car.grid_path_coordinates:
            continue
        #logging.info(f'drives through stop point')
        driving_car_frames = [driving_car.get_frames_for_pos(i) for i, coord in enumerate(driving_car.grid_path_coordinates)
                              if coord == stop_point]
        flattened_driving_car_frames = set([frame for frame_interval in driving_car_frames for frame in frame_interval])
        #logging.info(f'frames driving car is at stop point {flattened_driving_car_frames}')
        if any([driving_frame >= stop_frame for driving_frame in flattened_driving_car_frames]):
            return True
    return False


def drives_not_correct_standing(car, prev_cars):
    """True if car drives through already stopped prev_car."""
    #logging.info(f'start drives_not_correct_standing')
    for prev_car in prev_cars:
        if stops_not_correct(prev_car, [car]):
            return True
    return False


def drives_not_correct_driving(car, prev_cars):
    """True if car drives through driving prev_car. Prev_car always has priority."""
    #logging.info(f'start drives_not_correct_driving')
    for prev_car in prev_cars:
        shared_coords = list(set(prev_car.grid_path_coordinates).intersection(car.grid_path_coordinates))
        #logging.info(f'car {car.main_object_name} and prev_car {prev_car.main_object_name} share coords {shared_coords} ')
        for shared_coord in shared_coords:
            if get_first_collision_at_coord(prev_car, car, shared_coord):
                return True
    return False


def get_first_collision_at_coord(car, main_car, shared_coord):
    """If the cars collide, returns tuple with occurence/index of shared_coord in path of main_car and shared coord

    Parameters
    ----------
    car     :    Car
        Previously implemented car.
    main_car    :   Car
        Car whose path might get truncated.
    shared_coord    :   tuple
        Shared coord of both cars.

    Returns
    -------
    tuple or None
        Tuple with occurrence of coord and coord of first collision or None if cars don't collide.
    """
    #logging.info(f'get first collision at shared_coord {shared_coord}')
    # list of frame_intervals during which car is in vicinity of given coord already ordered in terms of occurrences
    main_car_frames = [main_car.get_frames_for_pos(i) for i, coord in enumerate(main_car.grid_path_coordinates) if
                       coord == shared_coord]
    #logging.info(f'{main_car.main_object_name} is at shared coord during frames {main_car_frames}')
    # set of frames when previously implemented car is at coord
    car_frames = [car.get_frames_for_pos(i) for i, coord in enumerate(car.grid_path_coordinates) if coord == shared_coord]
    flattened_car_frames = set([frame for frame_interval in car_frames for frame in frame_interval])
    #logging.info(f'{car.main_object_name} is at {shared_coord} during {flattened_car_frames}')
    for i, frame_interval in enumerate(main_car_frames):
        #logging.info(f'frame_interval {frame_interval}')
        shared_frame = None
        for frame in frame_interval:
            if frame in flattened_car_frames:
                shared_frame = frame
                break
        if not shared_frame:
            continue
        if shared_frame < 0:
            shared_frame = 0
        #logging.info(f'shared_frame {shared_frame}')
        main_car_pos_at_frame = main_car.get_pos_for_frame(shared_frame)
        car_pos_at_frame = car.get_pos_for_frame(shared_frame)
        # cars collide if at end of path
        if car_pos_at_frame + 2 > len(car.nodes) or main_car_pos_at_frame + 2 > len(main_car.nodes):
            return i, shared_coord
        # else check if movements comply
        if no_collision_while_driving(car, car_pos_at_frame, main_car, main_car_pos_at_frame):
            #logging.info('no_collision')
            continue
        return i, shared_coord


def no_collision_while_driving(car, car_pos_at_frame, main_car, main_car_pos_at_frame):
    """True if directions of car and main_car do not comply. Car always has priority.

    Parameters
    ----------
    car    :    Car
        Previously implemented car.
    car_pos_at_frame:
        Index of node of possible encounter for car.
    main_car    :    Car
        Car whose path might get truncated.
    main_car_pos_at_frame:
        Index of node of possible encounter for main_car.

    Returns
    -------
    bool
        True if directions do not comply.
    """
    #logging.info(f'start no collision')
    car_movement = car.predict_movement_at_pos(car_pos_at_frame)
    main_car_movement = main_car.predict_movement_at_pos(main_car_pos_at_frame)
    car_momentum_after_pos = car.nodes[car_pos_at_frame + 1].momentum
    main_car_momentum_after_pos = main_car.nodes[main_car_pos_at_frame + 1].momentum
    car_momentum_at_pos = car.nodes[car_pos_at_frame].momentum
    #logging.info(f'{car.main_object_name} is going {car_movement}')
    #logging.info(f'{main_car.main_object_name} is going {main_car_movement}')
    if main_car_momentum_after_pos.is_parallel_to(car_momentum_after_pos):
        # both cars end up in same street
        #logging.info('both cars end up in same street')
        return False
    if car_movement == "right":
        #logging.info('car_movement == "right"')
        return True
    if (car_movement == "left" or car_movement == "straight") and main_car_movement == "right" and car_momentum_at_pos.is_anti_parallel_to(main_car_momentum_after_pos):
        # main_car takes right turn into street car comes from
        #logging.info("main_car takes right turn into street car comes from")
        return True
    if car_momentum_after_pos.is_anti_parallel_to(main_car_momentum_after_pos) and main_car_movement == "straight" and car_movement == "straight":
        # both cars pass each other
        #logging.info("both cars pass each other")
        return True
    return False


if __name__ == "__main__":
    pass
