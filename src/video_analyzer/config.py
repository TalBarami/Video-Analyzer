from pathlib import Path
from os import path as osp
from omegaconf import OmegaConf
from argparse import ArgumentParser
import pandas as pd
import os

from skeleton_tools.utils.constants import REAL_DATA_MOVEMENTS
from skeleton_tools.utils.tools import init_directories, collect_labels

from video_analyzer.visualization import SkeletonVisualizer, FacialVisualizer

parser = ArgumentParser()
parser.add_argument("-mode", "--mode")
parser.add_argument("-homedir", "--detections_homedir")
parser.add_argument("-annotations", "--annotations_file")
parser.add_argument("-name", "--model_name")
args = vars(parser.parse_args())

_skeleton_cfg = {
    'net_name': 'JORDI',
    'columns': ['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'movement', 'calc_date', 'annotator'],
    'actions': REAL_DATA_MOVEMENTS[:-1],
    'no_act': REAL_DATA_MOVEMENTS[-1],
    'movement_col': 'movement',
    'ann_extension': 'annotations',
    'detection_file_extension': '.pkl'
}
_facial_cfg = {
    'net_name': 'BARNI',
    'columns': ['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'emotion', 'annotator'],
    'actions': ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise'],
    'no_act': 'neutral',
    'movement_col': 'emotion',
    'ann_extension': 'emotions',
    'detection_file_extension': '_groups.pkl'
}

_vis_init = {
    'skeleton': lambda path, res: SkeletonVisualizer(path, res),
    'facial': lambda path, res: FacialVisualizer(path, res),
}
_configs = {
    'skeleton': _skeleton_cfg,
    'facial': _facial_cfg,
}

# with open(args['config_path'], 'r') as f:
#     config = OmegaConf.load(f)
config = OmegaConf.create(args)

PROJECT_DIR = Path(__file__).parent.parent.parent
RESOURCES_DIR = osp.join(PROJECT_DIR, 'resources')
init_directories(RESOURCES_DIR)

config = OmegaConf.merge(config, OmegaConf.create(_configs[config['mode']]))
visualizer = _vis_init[config['mode']]
mv_col = config['movement_col']