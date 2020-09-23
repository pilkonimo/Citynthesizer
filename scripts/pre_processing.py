import bpy
import os, shutil
from pathlib import Path


def set_up_semantic_segmentation(data_dir):
    city_object_class_dict = get_dict_from_file(data_dir, "city_object_class_legend.txt")
    class_id_dict = get_dict_from_file(data_dir, "class_id_legend.txt")
    vehicles = ['Car', 'Truck']
    for i, obj in enumerate(bpy.data.objects, start=1):
        if obj.type in ("MESH", "CURVE") and 'CarPath' in obj.name:
            continue
        if obj.type in ("MESH", "CURVE") and any([vehicle in obj.name for vehicle in vehicles]):
            if obj.name.startswith("CameraCar"):
                obj["inst_id"] = int(class_id_dict['ego vehicle'])
            elif 'Truck' in obj.name:
                obj["inst_id"] = int(class_id_dict['truck'])
            else:
                obj["inst_id"] = int(class_id_dict['car'])
        if obj.type in ("MESH", "CURVE") and obj.name in city_object_class_dict:
            obj["inst_id"] = int(class_id_dict[city_object_class_dict[obj.name]])


def get_dict_from_file(data_dir, file_name):
    with open(os.path.join(data_dir, file_name), "r") as f:
        return_dict = {line.split(';')[0].rstrip(): line.split(';')[1].rstrip() for line in f.readlines()}
    return return_dict


def clear_folder(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def create_ground_truth_dir(base_dir, sub_dirs):
    for path_str in [os.path.join(base_dir, top, sub_dir) for sub_dir in sub_dirs for top in ["all", "filtered"]]:
        Path(path_str).mkdir(parents=True, exist_ok=True)
        clear_folder(path_str)
