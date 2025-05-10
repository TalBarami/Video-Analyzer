from argparse import ArgumentParser
from os import path as osp
from pathlib import Path

from asdhub.constants import USERS_ROOT
from omegaconf import OmegaConf
from taltools.io.files import init_directories

from video_analyzer.visualization import PlaceHolderVisualizer

parser = ArgumentParser()
parser.add_argument("-mode", "--mode")
parser.add_argument("-homedir", "--detections_homedir")
parser.add_argument("-annotations", "--annotations_file")
parser.add_argument("-name", "--model_name")
parser.add_argument("-a", "--annotate", action="store_true")
args = vars(parser.parse_args())

# _skeleton_cfg = {
#     'net_name': 'JORDI',
#     'columns': ['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'movement', 'calc_date', 'annotator'],
#     'actions': REAL_DATA_MOVEMENTS[:-1],
#     'no_act': REAL_DATA_MOVEMENTS[-1],
#     'movement_col': 'movement',
#     'ann_extension': 'annotations',
#     'detection_file_extension': '.pkl'
# }
_facial_cfg = {
    'net_name': 'BARNI',
    'columns': ['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'emotion', 'annotator'],
    'actions': ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise', 'neutral', 'other', 'directed'],
    'no_act': 'neutral',
    'movement_col': 'emotion',
    'ann_extension': 'et=0.6_ft=0.985_annotations',
    'detection_file_extension': '.pkl'
}

_assessment_cfg = {
    'net_name': 'SEGMENTATION',
    'columns': ['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'segment', 'calc_date', 'annotator'],
    'actions': ['Assembling a Puzzle', 'Name Response', 'Miniature Toys - Alone', 'Miniature Toys - Clinician', 'Free Talk', 'Free Play',
                'Brush Teeth', 'Describing Picture', 'Reading a Book', 'Joint Attention', 'Birthday Party', 'Snack Time', 'Blowing Bubbles',
                'Baloon', 'Comics', 'Interview', 'Invent a Story', 'Other'],
    'no_act': 'Unknown',
    'movement_col': 'segment',
    'ann_extension': 'annotations',
    'detection_file_extension': '.pkl'
}

_interactions_cfg = {
    'net_name': 'INTERACTIONS',
    'columns': ['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'action', 'calc_date', 'annotator'],
    'actions': ['Giving', 'Showing', 'Pointing', 'Gestures', 'Turn Towards', 'Turn Away', 'Low Confidence'],
    'no_act': 'no_act',
    'movement_col': 'action',
    'ann_extension': 'annotations',
    'detection_file_extension': '.pkl',
    'ann_dir': osp.join(USERS_ROOT, 'TalBarami', 'social_movements', 'manual_annotations', 'annotations')
}

_vis_init = {
    # 'smm': lambda path, res: SkeletonVisualizer(path, res),
    # 'facial': lambda path, res: FacialVisualizer(path, res),
    'interactions': lambda path, res: PlaceHolderVisualizer()
}
_configs = {
    # 'smm': _skeleton_cfg,
    'facial': _facial_cfg,
    'interactions': _interactions_cfg
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
NET_NAME = config['net_name']