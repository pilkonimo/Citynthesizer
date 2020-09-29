# Citynthesizer
##### A Blender-based data generation pipeline for urban driving. 
This data generation pipeline generates data for image recognition research in the context of urban driving. 
It is based on Blender [[1]](#1), its rendering-engine Cycles [[2]](#2), and the Blender Add-On SceneCity [[3]](#3). 
As of now, the pipeline supports ground truth for disparity maps and semantic segmentation and is heavily oriented along 
the CityScapes [[4]](#4) dataset. 

**Results**

| image  | disparity | semantic segmentation |
| ------------- | ------------- | ------------- |
| ![](examples/scenecity_000119_000029_leftImg8bit.png)  | ![](examples/scenecity_000119_000029_disparity.png)    | ![](examples/scenecity_000119_000029_gtFine_color.png)    |
| ![](examples/scenecity_000045_000010_leftImg8bit.png)  | ![](examples/scenecity_000045_000010_disparity.png)    | ![](examples/scenecity_000045_000010_gtFine_color.png)    |

## Table of Contents
[Citynthesizer](#citynthesizer)
  * [Requirements](#requirements)
  * [Installation](#installation)
  * [Initial Configuration](#initial-configuration)
  * [Usage](#usage)
  * [Similarity of Data to CityScapes](#similarity-of-data-to-cityscapes---4----4-)
  * [Modification Guidelines](#modification-guidelines)
      - [Adding Models of Cars](#adding-models-of-cars)
      - [Adding Models of Buildings](#adding-models-of-buildings)
  * [References](#references)

## Requirements
* Blender (v2.82a) with python (v3.7.4)
* Requirements for blender internal python version under [./others/blender_python_requirements.txt](others/blender_python_requirements.txt)
* SceneCity (v1.7.0) (Blender Add-On)
* HDRI sky map
* Models of vehicles to be incorporated
## Installation

* Setup blender and its internal python according to [./others/blender_python_requirements.txt](others/blender_python_requirements.txt) with 
```shell
path/to/blender_python$ pip install -r blender_python_requirements.txt
``` 
* Install OpenEXR (see https://excamera.com/sphinx/articles-openexr.html) and add python bindings to blender's python
* Either manually install SceneCity in blender, or optionally move it under the name 'SceneCity.zip' 
  to [./others](others) and uncomment the installation lines in [./setup.py](setup.py).
## Initial Configuration
Citynthesizer does not ship with sky HDRIs nor with models of vehicles due to licensing. 
Both are needed for a fully functional pipeline.
Models of cars can for instance be acquired via [Chocofur](https://store.chocofur.com/search/cars).

##### HDRIs
Provide an HDRI depicting a sky or the like and save it under ./HDRI/example.hdr.
Specify the name of the desired HDRI under sky_HDRI in [./setup.py](setup.py).

##### Car Models
To fully function at least one carmodel has to be provided, to do this see [Adding Models of Cars](#Adding-Models-of-Cars).
## Usage 
Define the parameters of the desired city in [./setup.py](setup.py). Run [./setup.py](setup.py) on [./standard.blend](standard.blend) with
```shell
path/to/blender$ ./blender path/to/Citynthesizer/standard.blend -b -P path/to/Citynthesizer/setup.py 
```

The generated ground_truth is stored under ./ground_truth/current_run and additionally copied to
/ground_truth/CityScapes_format. 

Alternatively, [./multiple_runs.sh](multiple_runs.sh) can be used to execute multiple such runs. 
In this case data is only accumulated in the CityScapes format.
## Similarity of Data to CityScapes [[4]](#4)

Every run is saved in a format similar to CityScapes [[4]](#4).
The city is called 'scenecity' and every run corresponds to one sequence. 
To which split ('train', 'test', 'val') a data set belongs is determined by random choice weighted with percentages 
(Default for 'test' and 'val': 0.0). 

The camera setting ([./data/camera.json](data/camera.json)) is taken from CityScapes [[4]](#4) 
(originally: aachen_000000_000019_camera.json) and used to calculate disparity- from depth-maps. 
It is additionally copied to comply with the CityScapes [[4]](#4) format.
Because stereo-imaging is not available only the intrinsic parameters are implemented in blender.

**Labeling Conflicts**

At the moment mainly two labeling conflicts arise with respect to the CityScapes dataset [[4]](#4), 
if used out-of-the-box with SceneCity [[3]](#3).
* Sidewalks are labeled as roads
* Front- and backside of traffic signs are both labeled as such     

## Modification Guidelines

#### Adding Models of Cars
1. Provide model in .blend file with one parent object (from now on referred to as main_object), for all meshes. For convenience save it under [./models/cars](models/cars).
1. The name of all meshes should contain the corresponding CityScapes-label. (At the moment only 'car', 'truck' supported.)
1. In [./setup.py](setup.py) under car_models_info provide the information needed for Citynthesizer to process the model:
    * file path
    * scaling factor 
    * name of the main_object
    * position of the camera relative to the car

#### Adding Models of Buildings
Buildings are incorporated via SceneCity and need to be linked manually to the scene. 
Efforts to incorporated easy asset ingestion are to be undertaken. 
Best practice to add custom models is, as of now, to save them under [./models/buildings](models/buildings), 
link them under link_assets(), and add their main parent object in buildings_bl_objects 
both to be found in [./scripts/city_handler.py](scripts/city_handler.py).

## References
<a id="1">[1]</a> 
Blender website. 
URL https://www.blender.org/ 


<a id="2">[2]</a> 
Cycles website. 
URL https://www.cycles-renderer.org/ 

<a id="3">[3]</a> 
SceneCity website. 
URL https://www.cgchan.com/

<a id="4">[4]</a> 
Cordts, Marius, et al. 
"The cityscapes dataset for semantic urban scene understanding." 
Proceedings of the IEEE conference on computer vision and pattern recognition. 2016.
