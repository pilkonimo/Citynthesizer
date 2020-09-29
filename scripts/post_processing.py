import os, importlib, random, json, logging, re, time
from datetime import datetime
from pathlib import Path
from shutil import copyfile
import cv2
import numpy as np
from . import pre_processing
importlib.reload(pre_processing)


def corrected_depth(depth):
    """bpycv returns depth, with values over above LIMIT_DEPTH = 1e8 set to 0. Here again set to np.inf.
    Bug in Scenecity sets grid.cell_size to 1m real life scale is 10m"""
    depth[depth == 0] = np.inf
    depth = depth*10
    return depth


def disparity_from_depth(depth, data_dir):
    """Returns disparity in px in image space."""
    with open(os.path.join(data_dir, "camera.json")) as f:
        camera_data = json.load(f)
    base_line = camera_data['extrinsic']['baseline']
    focal_length = camera_data['intrinsic']['fx'] + camera_data['intrinsic']['fy'] / 2
    disparity = (base_line * focal_length) / depth
    return disparity


def disparity_float_to_16_bit(disparity_float):
    disparity_16bit = np.round(disparity_float*256 + 1)
    # treat clipped values as invalid measurements
    disparity_16bit[disparity_16bit > np.iinfo(np.uint16).max] = 0
    return disparity_16bit.astype(np.uint16)


def disparity_filter_ego_vehicle(disparity, sem_seg, data_dir):
    """Most CS disparity maps show measurements for the ego vehicle to be invalid (== 0)"""
    class_id_dict = pre_processing.get_dict_from_file(data_dir, "class_id_legend.txt")
    disparity[sem_seg == int(class_id_dict['ego vehicle'])] = 0
    return disparity


def generate_disparity(depth, sem_seg, data_dir):
    """Corrects depth, generates disparity, converts and filters it according to CityScapes."""
    depth = corrected_depth(depth)
    disparity_float = disparity_from_depth(depth, data_dir)
    disparity_16bit = disparity_float_to_16_bit(disparity_float)
    disparity_filtered = disparity_filter_ego_vehicle(disparity_16bit, sem_seg, data_dir)
    return disparity_filtered


def swap_id_unlabeled_and_sky(current_run_base_dir, data_dir):
    """Blender is unable to assign Sky as HDRI an inst_id, defaults to 0. Therefore swapped with unlabeled in class_id_dict.
    Now swap ids according to CityScapes"""
    sem_seg_base_dir = os.path.join(current_run_base_dir, "semantic_segmentation")
    class_id_dict = pre_processing.get_dict_from_file(data_dir, "class_id_legend.txt")
    for filename in os.listdir(sem_seg_base_dir):
        img_path = os.path.join(sem_seg_base_dir, filename)
        img = cv2.imread(img_path, 0)
        mask_sky = img == int(class_id_dict['unlabeled'])
        mask_unlabeled = img == int(class_id_dict['sky'])
        img[mask_sky] = int(class_id_dict['sky'])
        img[mask_unlabeled] = int(class_id_dict['unlabeled'])
        cv2.imwrite(img_path, img)


def generate_color_images(current_run_base_dir, data_dir):
    sem_seg_base_dir = os.path.join(current_run_base_dir, "semantic_segmentation")
    color_base_dir = os.path.join(current_run_base_dir, "semantic_segmentation_color")
    id_color_dict = pre_processing.get_dict_from_file(data_dir, "id_color_legend.txt")
    for label, color in id_color_dict.items():
        id_color_dict[label] = tuple(int(color[1:-1].split(',')[i]) for i in range(3))
    for filename in os.listdir(sem_seg_base_dir):
        regex = re.compile(r'\d+')
        frame_number = int(regex.search(filename).group(0))
        sem_seg_path = os.path.join(sem_seg_base_dir, filename)
        color_path = os.path.join(color_base_dir, "semantic_segmentation_color" + str(frame_number) + ".png")
        sem_seg = cv2.imread(sem_seg_path, 0)
        color = np.zeros(sem_seg.shape + (3,))
        for label_id in np.unique(sem_seg):
            color[sem_seg == label_id] = id_color_dict[str(label_id)]
        color = color.astype(np.uint8)
        cv2.imwrite(color_path, cv2.cvtColor(color, cv2.COLOR_RGB2BGR))


def check_city_scapes_dirs(gt_base_dir, categories):
    """Checks CityScapes directories for existence."""
    category_base_dirs = [os.path.join(gt_base_dir, "CityScapes_format", category) for category in categories]
    split_dirs = ["train", "test", "val"]
    for path_str in [os.path.join(base_dir, split_dir, "scenecity") for base_dir in category_base_dirs for split_dir in split_dirs]:
        Path(path_str).mkdir(parents=True, exist_ok=True)


def get_highest_sequence_number(city_scapes_paths, splits):
    """Returns highest sequence number over all CityScapes-categories."""
    split_dirs = [os.path.join(path, split, "scenecity") for key, path in city_scapes_paths.items() for split in splits]
    sequence_nr = 0
    for split_dir in split_dirs:
        for filename in os.listdir(split_dir):
            sequence_nr = max(int(filename.split('_')[1]), sequence_nr)
    return sequence_nr


def store_current_run(gt_base_dir, data_dir, allowed_frames, city_scapes_gt_categories, current_gt_categories, test_perc=0.0, val_perc=0.0):
    """Stores GT of current run in CityScapes-format. By default all data used for training.

    Parameters
    ----------
    gt_base_dir    :    str
        Path of ground_truth base directory.
    data_dir    :    str
        Path of data base directory with camera.json file.
    allowed_frames  :   list of int
        List of frames that were rendered as images.
    city_scapes_gt_categories    :    list of str
        List of CityScapes-categories in which the GT is saved.
    current_gt_categories    :    list of str
        List of GT categories generated for current run.
    test_perc    :    float
        Approximate percentage of current run used for testing. Used as weight in random choice.
    val_perc    :    float
        Approximate percentage of current run used for validation. Used as weight in random choice.
    """
    splits = ["train", "test", "val"]
    current_run_paths = {gt_category: os.path.join(gt_base_dir, "current_run", "filtered", gt_category)
                         for gt_category in current_gt_categories}
    city_scapes_paths = {gt_category: os.path.join(gt_base_dir, "CityScapes_format", gt_category)
                         for gt_category in city_scapes_gt_categories}
    sequence_nr = get_highest_sequence_number(city_scapes_paths, splits) + 1
    splits = random.choices(splits, weights=[100 * (1 - test_perc - val_perc), 100 * test_perc, 100 * val_perc], k=len(allowed_frames))
    logging.info(f'About to store {allowed_frames}')
    for i, frame in enumerate(allowed_frames):
        current_files = {current_gt_category: os.path.join(current_run_paths[current_gt_category],
                                                           current_gt_category + str(frame) + ".png")
                         for current_gt_category in current_gt_categories}
        current_files["camera"] = os.path.join(data_dir, "camera.json")
        from_split = os.path.join(splits[i], "scenecity")
        city_scapes_file_name = '_'.join(["scenecity", str(sequence_nr).zfill(6), str(frame).zfill(6)])
        logging.info(f'storing frame {frame} under {city_scapes_file_name}\ncurrent file names: {current_files} ')
        # copy to gtFine
        copyfile(current_files["image"],
                 os.path.join(city_scapes_paths["leftImg8bit"], from_split, city_scapes_file_name + "_leftImg8bit.png"))
        copyfile(current_files["semantic_segmentation"],
                 os.path.join(city_scapes_paths["gtFine"], from_split, city_scapes_file_name + "_gtFine_labelIds.png"))
        copyfile(current_files["semantic_segmentation_color"],
                 os.path.join(city_scapes_paths["gtFine"], from_split, city_scapes_file_name + "_gtFine_color.png"))
        copyfile(current_files["disparity"],
                 os.path.join(city_scapes_paths["disparity"], from_split, city_scapes_file_name + "_disparity.png"))
        copyfile(current_files["camera"],
                 os.path.join(city_scapes_paths["camera"], from_split, city_scapes_file_name + "_camera.json"))
        logging.info(f"stored frame {frame} in CityScapes-format")
    os.rename(src=os.path.join(gt_base_dir, "current_run", "filtered"),
              dst=os.path.join(gt_base_dir, "current_run", "filtered" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S")))
    logging.info(f'Stored {len(allowed_frames)} in CityScapes-format under sequence-nr. {sequence_nr}')


if __name__ == "__main__":
    pass
