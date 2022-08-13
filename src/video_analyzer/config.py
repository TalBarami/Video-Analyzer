from pathlib import Path
from os import path as osp
from omegaconf import OmegaConf
from skeleton_tools.utils.constants import REAL_DATA_MOVEMENTS
from skeleton_tools.utils.tools import init_directories

from video_analyzer.visualization import SkeletonVisualizer, FacialVisualizer

_skeleton_cfg = {
    'net_name': 'JORDI',
    'columns': ['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'movement', 'calc_date', 'annotator'],
    'actions': REAL_DATA_MOVEMENTS[:-1],
    'no_act': REAL_DATA_MOVEMENTS[-1],
    'movement_col': 'movement',
    'file_extension': '.pkl'
}
_facial_cfg = {
    'net_name': 'BARNI',
    'columns': ['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'emotion', 'annotator'],
    'actions': ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise'],
    'no_act': 'neutral',
    'movement_col': 'emotion',
    'file_extension': '_groups.pkl'
}

_vis_init = {
    'skeleton': lambda path, res: SkeletonVisualizer(path, res),
    'facial': lambda path, res: FacialVisualizer(path, res),
}
_configs = {
    'skeleton': _skeleton_cfg,
    'facial': _facial_cfg,
}

with open(r'Z:\Users\TalBarami\va_configuration\facial_config.yaml', 'r') as f:
    config = OmegaConf.load(f)
PROJECT_DIR = Path(__file__).parent.parent.parent
RESOURCES_DIR = osp.join(PROJECT_DIR, 'resources')
init_directories(RESOURCES_DIR)

config = OmegaConf.merge(config, OmegaConf.create(_configs[config['mode']]))
visualizer = _vis_init[config['mode']]
mv_col = config['movement_col']
no_act = config['no_act']
