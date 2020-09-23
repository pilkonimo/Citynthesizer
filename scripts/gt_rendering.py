import bpy
import cv2
import bpycv
import os, time, importlib, logging, datetime
from shutil import copyfile
from . import pre_processing, post_processing, filtering
importlib.reload(pre_processing)
importlib.reload(post_processing)
importlib.reload(filtering)


def set_render_settings():
    scene = bpy.data.scenes[0]
    scene.render.engine = 'CYCLES'
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
    scene.cycles.device = "GPU"
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4


def render_gt(current_run_base_dir, data_dir, rendering_frames):
    """Renders GT for current for all frames and saves it in gt_base_dir"""
    bpy.types.ImageFormatSettings.color_depth = 16
    # gt rendering
    for i, frame in enumerate(rendering_frames):
        logging.info(f"Render GT frame {frame}  ({i+1}/{len(rendering_frames)})")
        bpy.context.scene.frame_set(frame)
        result = bpycv.render_data(render_image=False, render_annotation=True)
        cv2.imwrite(os.path.join(current_run_base_dir, "all", "semantic_segmentation", "semantic_segmentation" + str(frame) + ".png"),
                    result["inst"])
        disparity = post_processing.generate_disparity(result["depth"], result["inst"], data_dir)
        cv2.imwrite(os.path.join(current_run_base_dir, "all", "disparity", "disparity" + str(frame) + ".png"), disparity)
        # normalized depth
        # cv2.imwrite(os.path.join(current_run_base_dir, "all", "depth", "depth" + str(frame) + ".png"),
        #             result["depth"] / result["depth"].max() * 255)


def render_images(current_run_base_dir, frames, current_gt_categories):
    # image rendering
    for i, frame in enumerate(frames):
        bpy.context.scene.frame_set(frame)
        bpy.data.scenes[0].render.filepath = os.path.join(current_run_base_dir, "filtered", "image", "image" + str(frame) + ".png")
        logging.info(f'Render image frame {frame} ({i+1}/{len(frames)}) using: {bpy.data.scenes[0].render.engine}')
        bpy.ops.render.render(write_still=True)
        gt_files = [os.path.join(category, category + str(frame) + ".png")
                    for category in current_gt_categories if category != "image"]
        for gt_file in gt_files:
            copyfile(src=os.path.join(current_run_base_dir, "all", gt_file),
                     dst=os.path.join(current_run_base_dir, "filtered", gt_file))


def extract_gt(gt_base_dir, data_dir, blend_file_dir, rendering_frames, test_perc, val_perc, number_of_frames=None):
    """Extracts ground_truth for current run  and copies it to CityScapes-format.

    Parameters
    ----------
    gt_base_dir    :    str
        Path of ground_truth base directory.
    data_dir    :    str
        Path of data base directory with camera.json file.
    blend_file_dir  :   str
        Path of .blend file.
    rendering_frames    :   list of int
        List of frames to be rendered.
    test_perc    :    float
        Approximate percentage of current run used for testing. Used as weight in random choice.
    val_perc    :    float
        Approximate percentage of current run used for validation. Used as weight in random choice.
    number_of_frames    :    int
        Number of frames to render. None corresponds to the rendering of all frames.
    """
    start_time = time.time()
    current_run_base_dir = os.path.join(gt_base_dir, "current_run")
    current_gt_categories = ["image", "semantic_segmentation", "disparity", "semantic_segmentation_color"]
    city_scapes_gt_categories = ["gtFine", "disparity", "camera", "leftImg8bit"]
    pre_processing.create_ground_truth_dir(current_run_base_dir, current_gt_categories)
    pre_processing.set_up_semantic_segmentation(data_dir)
    set_render_settings()
    if number_of_frames:
        rendering_frames = rendering_frames[:number_of_frames]
    logging.info(f'Updated rendering_frames: {rendering_frames}')
    render_gt(current_run_base_dir, data_dir, rendering_frames)
    post_processing.swap_id_unlabeled_and_sky(os.path.join(current_run_base_dir, "all"), data_dir)
    post_processing.generate_color_images(os.path.join(current_run_base_dir, "all"), data_dir)
    allowed_frames = filtering.get_allowed_frames(os.path.join(current_run_base_dir, "all"), data_dir)
    logging.info(f'allowed frames: {allowed_frames}')
    if allowed_frames:
        bpy.ops.wm.open_mainfile(filepath=os.path.join(blend_file_dir, "current_city.blend"))
        logging.basicConfig(filename=os.path.join(data_dir, "runs.log"), filemode='a', level=logging.INFO)
        set_render_settings()
        render_images(current_run_base_dir, allowed_frames[:], current_gt_categories)
        post_processing.check_city_scapes_dirs(gt_base_dir, city_scapes_gt_categories)
        post_processing.store_current_run(gt_base_dir, data_dir, allowed_frames[:], city_scapes_gt_categories,
                                          current_gt_categories, test_perc, val_perc)
    logging.info(f'Rendered ground truth and {len(allowed_frames)} images - execution time: {round(time.time() - start_time)} s')
    print(f'Rendered ground truth and {len(allowed_frames)} images\nExecution time: {round(time.time() - start_time)} s')


if __name__ == "__main__":
    pass
