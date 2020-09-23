import cv2
import numpy as np
from skimage import segmentation as sgmnt
import os, importlib, re
from . import pre_processing
importlib.reload(pre_processing)


def frame_shows_edge(base_dir, frame, data_dir):
    """Return True if edge between sky and road in frame. In class_id_legend unlabeled and sky swapped."""
    sem_seg = cv2.imread(os.path.join(base_dir, "semantic_segmentation/semantic_segmentation"+str(frame)+".png"), -1)
    class_id_dict = pre_processing.get_dict_from_file(data_dir, "class_id_legend.txt")
    sky = np.copy(sem_seg)
    sky[sky != int(class_id_dict["unlabeled"])] = 0
    road = np.copy(sem_seg)
    road[road != int(class_id_dict["road"])] = 0
    sky_bound = sgmnt.find_boundaries(sky)
    road_bound = sgmnt.find_boundaries(road)
    return np.count_nonzero(sky_bound * road_bound) > 0


def frame_shows_car(base_dir, frame, data_dir):
    """Return True if frame shows car. """
    sem_seg = cv2.imread(os.path.join(base_dir, "semantic_segmentation/semantic_segmentation" + str(frame) + ".png"),
                         -1)
    class_id_dict = pre_processing.get_dict_from_file(data_dir, "class_id_legend.txt")
    return int(class_id_dict['car']) in np.unique(sem_seg)


def get_allowed_frames(current_run_all_base_dir, data_dir):
    allowed_frames = []
    regex = re.compile(r'\d+')
    for filename in os.listdir(os.path.join(current_run_all_base_dir, "disparity")):
        frame = int(regex.search(filename).group(0))
        if frame_shows_edge(current_run_all_base_dir, frame, data_dir):
            continue
        if not frame_shows_car(current_run_all_base_dir, frame, data_dir):
            continue
        allowed_frames.append(frame)
    return allowed_frames
