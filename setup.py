import bpy
import importlib, sys, os, logging
from datetime import datetime

blend_file_dir = os.path.dirname(bpy.data.filepath)
if blend_file_dir not in sys.path:
    sys.path.append(blend_file_dir)

import scripts.city_handler as city_handler
import scripts.car_handler as car_handler
import scripts.gt_rendering as gt_rendering






#path_scene_city = os.path.join(blend_file_dir, "others", "SceneCity.zip")
#bpy.ops.preferences.addon_install(filepath=path_scene_city)
bpy.ops.preferences.addon_enable(module='scenecity')


# force reload
importlib.reload(city_handler)
importlib.reload(car_handler)
importlib.reload(gt_rendering)

data_dir = os.path.join(blend_file_dir, "data")
logging.basicConfig(filename=os.path.join(data_dir, "runs.log"), filemode='a', level=logging.INFO)
logging.info('Started run at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

# create city
HDRI_base_dir = os.path.join(blend_file_dir, "HDRI")
sky_HDRI = "CGSkies_0342_free.hdr"

city_handler.create_city(grid_size=(20, 20), road_bl_objects=city_handler.road_bl_objects,
                         buildings_bl_objects=city_handler.buildings_bl_objects, data_dir=data_dir,
                         HDRI_base_dir=HDRI_base_dir, sky_HDRI=sky_HDRI)

# define metadata for car models works in loop if structure is ./models/cars/Car0x/Car0x.blend for every car
cars_base = os.path.join(blend_file_dir, "models", "cars")

car_models_info = [
    {'file path': os.path.join(cars_base, "Car01.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Car_01", 'camera_pos': (0, 0, 0.15)},
    {'file path': os.path.join(cars_base, "Car02.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Car_02", 'camera_pos': (0, 0, 0.15)},
    {'file path': os.path.join(cars_base, "Car03.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Car_03", 'camera_pos': (0, 0, 0.15)},
    {'file path': os.path.join(cars_base, "Car04.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Car_06", 'camera_pos': (0, 0, 0.15)},
    {'file path': os.path.join(cars_base, "Car05.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Car_07", 'camera_pos': (0, 0, 0.15)},
    {'file path': os.path.join(cars_base, "Car06.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Car_08", 'camera_pos': (0, 0, 0.2)},
    {'file path': os.path.join(cars_base, "Car07.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Car_09", 'camera_pos': (0, 0, 0.15)},
    {'file path': os.path.join(cars_base, "Car08.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Truck_12", 'camera_pos': (0, 0, 0.15)},
    {'file path': os.path.join(cars_base, "Car09.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Car_11", 'camera_pos': (0, 0.02, 0.17)},
    {'file path': os.path.join(cars_base, "Car10.blend"), 'scaling factor': 0.11, 'main object name': "Chocofur_Car_15", 'camera_pos': (0, 0.15, 0.15)},
    {'file path': os.path.join(cars_base, "Car11.blend"), 'scaling factor': 0.08, 'main object name': "Chocofur_Free_Car_01", 'camera_pos': (0, 0, 0.15)},
    {'file path': os.path.join(cars_base, "Car12.blend"), 'scaling factor': 0.12, 'main object name': "Chocofur_Free_Car_02", 'camera_pos': (0, 0, 0.15)}]


render_worth, rendering_frames = car_handler.add_cars_to_city(car_models_info=car_models_info, data_dir=data_dir,
                                                              number_cars=10, min_number_cars=5)

logging.info(f'render_worth: {render_worth}')
logging.info(f'rendering_frames: {rendering_frames}')
if render_worth:
    # save created city as .blend
    bpy.ops.wm.save_mainfile(filepath=os.path.join(blend_file_dir, "current_city.blend"))
    logging.info('saved city under .current_city.blend')

    # setup and render ground truth (gt)
    gt_base_dir = os.path.join(blend_file_dir, "ground_truth")
    gt_rendering.extract_gt(gt_base_dir=gt_base_dir, data_dir=data_dir, blend_file_dir=blend_file_dir,
                            rendering_frames=rendering_frames, test_perc=0.5, val_perc=0.0, number_of_frames=None)

logging.info('Finished run at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n')
