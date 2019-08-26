# EM-Renderer
A package for rendering EM images based on [Rhoana](https://github.com/Rhoana)'s rh_renderer.

## Preparation
+ A conda environment of python 2.7
+ [tinyr](https://github.com/HoraceKem/tinyr)
+ OpenCV 2.7(installed by pip)

## Installation
```
conda activate YOUR_ENV  
cd YOUR_PATH_TO_EM-Renderer/  
pip install -r requirements.txt  
python setup.py install  
```
## Usage
```
cd YOUR_PATH_TO_EM-renderer/scripts/  
python 3d_render_driver.py [parameter1][parameter2]... [tiles_dir]  
```
