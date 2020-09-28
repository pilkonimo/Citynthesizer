# Citynthesizer
##### A Blender-based data generation pipeline for urban driving. 
## Requirements
* Blender (v2.82a) with python (v3.7.4)
* Requirements for blender internal python version under /others/blender_python_requirements.txt
* SceneCity (v1.7.0)
## Installation

* Setup blender and its internal python according to /others/blender_python_requirements.txt with 
```shell
path/to/blender_python$ pip install -r blender_python_requirements.txt
``` 
* Install OpenEXR (see https://excamera.com/sphinx/articles-openexr.html) and add python bindings to blender's python
* Either manually install SceneCity in blender, or optionally move it under the name 'SceneCity.zip' to /others and uncomment the installation lines in setup.py.
## Usage 
Define the parameters of the desired city in setup.py. Run setup.py on standard.blend with
```shell
path/to/blender$ ./blender path/to/Citynthesizer/standard.blend -b -P path/to/Citynthesizer/setup.py 
```

The generated ground_truth is stored under /ground_truth/current_run and additionally copied to /ground_truth/CityScapes_format. 

Alternatively, ./multiple_runs.sh can be used to execute multiple such runs. In this case data is only accumulated in the CityScapes format.
## Similarity of Data to CityScapes

Every run is additionally saved in a format similar to CityScapes (https://www.cityscapes-dataset.com/).
The city is called 'scenecity' and every run corresponds to one sequence. 
To which split ('train', 'test', 'val') a data set belongs is determined by random choice weighted with percentages 
(Default for 'test' and 'val': 0.0). 

The camera setting (/data/camera.json) is taken from CityScapes (originally: aachen_000000_000019_camera.json) and 
used to calculate disparity- from depth-maps. It is additionally copied to comply with the CityScapes format.
Because stereo-imaging is as of now not available only the intrinsic parameters are implemented in blender.   

## Modification Guidelines

#### Adding a carmodel
1. Provide Model in .blend file with one parent object (from now on referred to as main_object), for all meshes. For convenience save it under /models/cars.
1. The name of all MESHES should contain the corresponding CityScapes-label. (At the moment only 'car', 'truck' supported.)
1. In setup.py in car_models_info provide the information needed for Citynthesizer to process the model:
    * file path
    * scaling factor 
    * name of the main_object
    * position of the camera relative to the car
 
