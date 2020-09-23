import bpy
import re, math, json, os
"""Interface to blender for car handling"""


# generalized blender-handler
def clear_cameras():
    cameras = [ob for ob in bpy.context.scene.objects if ob.type == 'CAMERA']
    bpy.ops.object.delete({"selected_objects": cameras})


def set_3d_cursor(position=(0, 0, 0)):
    bpy.context.area.ui_type = "VIEW_3D"
    bpy.context.area.type = "VIEW_3D"
    #print(bpy.context.area.spaces[0])
    bpy.context.scene.cursor.location = position


#  direct blender modifications
def add_curve(objname, curvename, vectors, start_point, end_point,weights, frames_per_node):
    curve_data = bpy.data.curves.new(name=curvename, type='CURVE')
    curve_data.dimensions = '3D'

    object_data = bpy.data.objects.new(objname, curve_data)
    object_data.location = (0, 0, 0)
    bpy.context.collection.objects.link(object_data)

    path = curve_data.splines.new('NURBS')
    path.points.add(len(vectors) + 1)
    path.points[0].co = start_point + (1,)
    for i, vector in enumerate(vectors, start=1):
        path.points[i].co = vector + (weights[i-1],)
    path.points[len(vectors) + 1].co = end_point + (1,)
    #path.order_u = len(path.points) - 1
    # set animation parameters for testing purposes
    curve_data.use_path = True
    curve_data.path_duration = len(vectors) * frames_per_node
    curve_data.eval_time = len(vectors) * frames_per_node

    return object_data


def append_car(filepath, main_name):
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if 'Car' in name or 'Truck' in name]

    # link them to scene
    main_object = None
    scene = bpy.context.scene
    for obj in data_to.objects:
        if obj is not None:
            scene.collection.objects.link(obj)
            if re.match(r"^" + main_name + r"(\.\d{3})?$", obj.name):
                main_object = obj
    main_object.scale = (0.09, 0.09, 0.09)
    return main_object


def set_camera_to_calibration_matrix(cam, data_dir):
    """Setting Camera Paramters acoording to calibration matrix.
    (https://www.rojtberg.net/1601/from-blender-to-opencv-camera-and-back/)"""
    with open(os.path.join(data_dir, "camera.json")) as f:
        camera_data = json.load(f)

    u_0 = camera_data["intrinsic"]["u0"]
    v_0 = camera_data["intrinsic"]["v0"]
    f_x = camera_data["intrinsic"]["fx"]
    f_y = camera_data["intrinsic"]["fy"]
    w = 2048
    h = 1024

    scene = bpy.context.scene
    sensor_width_in_mm = cam.sensor_width
    scene.render.resolution_x = w
    scene.render.resolution_y = h

    pixel_aspect = f_y / f_x
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = pixel_aspect

    cam.shift_x = -(u_0 / w - 0.5)
    cam.shift_y = (v_0 - 0.5 * h) * (pixel_aspect/w)

    cam.lens = f_x / w * sensor_width_in_mm


def add_camera(camera_name, camera_pos, data_dir):
    camera_data = bpy.data.cameras.new(name=camera_name)

    object_data = bpy.data.objects.new(camera_name, camera_data)
    object_data.location = camera_pos
    object_data.rotation_euler = (math.pi / 2, 0, 0)
    bpy.context.collection.objects.link(object_data)
    set_camera_to_calibration_matrix(camera_data, data_dir)

    return object_data


def add_constraint(object_to_be_bound, curve):
    """Bind object to follow path of curve."""
    # set origin to (0, 0, 0)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.context.scene.cursor.rotation_euler = (0, 0, 0)
    for obj in [object_to_be_bound, curve]:
        bpy.context.scene.objects[obj.name].select_set(True)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.context.scene.objects[obj.name].select_set(False)
    # add constraint
    constraint = object_to_be_bound.constraints.new('FOLLOW_PATH')
    constraint.target = curve
    constraint.use_curve_follow = True
    bpy.context.scene.objects[object_to_be_bound.name].select_set(True)
    bpy.context.view_layer.objects.active = object_to_be_bound
    override = {'constraint': constraint}
    bpy.ops.constraint.followpath_path_animate(override, constraint='Follow Path')


def set_camera_car(car):
    """Rename camera carrying car for labeling later."""
    children = car.main_object.children
    for child in children:
        child.name = "CameraCar" + child.name
    car.main_object.name = "CameraCar" + car.main_object.name
    car.main_object_name = car.main_object.name


def animate_car(vector_list, start_point, end_point, weights, curve_name, car, data_dir, with_camera=False):
    """Creates Curve through given weighted vectors and animates car following the curve. """
    car.append()
    car.curve = add_curve(curve_name + "Object", curve_name, vector_list, start_point, end_point, weights, car.frames_per_node)
    add_constraint(car.main_object, car.curve)
    if with_camera:
        car.camera = add_camera(car.main_object_name + "Camera", car.camera_pos, data_dir)
        bpy.data.scenes['Scene'].camera = car.camera
        add_constraint(car.camera, car.curve)
