import cv2
import numpy as np
from skeleton_tools.openpose_layouts.body import COCO_LAYOUT
from skeleton_tools.openpose_layouts.face import PYFEAT_FACIAL
from skeleton_tools.skeleton_visualization.data_prepare.data_extract import PyfeatDataExtractor
# from skeleton_tools.skeleton_visualization.numpy_visualizer import MMPoseVisualizer
from skeleton_tools.skeleton_visualization.painters.base_painters import GlobalPainter, BlurPainter
from skeleton_tools.skeleton_visualization.painters.local_painters import GraphPainter, ScorePainter, BoxPainter
from skeleton_tools.utils.tools import read_pkl


class SkeletonVisualizer:
    def __init__(self, skeleton_path, org_resolution, blur_face=False):
        self.vis = MMPoseVisualizer(COCO_LAYOUT, blur_face=blur_face)
        self.skeleton_path = skeleton_path
        self.skeleton = read_pkl(skeleton_path)
        self.resolution = org_resolution
        self.user_adjust = self.auto_adjust

    def set_blurring(self, blur_face):
        self.vis.blur_face = blur_face

    def set_resolution(self, width, height):
        self.skeleton['keypoint'] /= np.array(self.resolution)
        self.resolution = (width, height)
        self.skeleton['keypoint'] *= np.array(self.resolution)

    def draw(self, frame, frame_number):
        i = frame_number - self.user_adjust()
        if i >= 0:
            frame = self.vis.draw_skeletons(frame,
                                            self.skeleton['keypoint'][:, i, :, :],
                                            self.skeleton['keypoint_score'][:, i, :],
                                            child_id=(self.skeleton['child_ids'][
                                                          i] if 'child_ids' in self.skeleton.keys() else None),
                                            thickness=2)
        return frame

    def auto_adjust(self):
        return self.skeleton['adjust']


class FacialVisualizer:
    def __init__(self, pyfeat_out_path, org_resolution, blur_face=False):
        self.pyfeat_out_path = pyfeat_out_path
        self.layout = PYFEAT_FACIAL
        self.eps = 0.985
        self.extractor = PyfeatDataExtractor(self.layout)
        self.data = self.extractor(pyfeat_out_path)
        self.blur_painter = BlurPainter(self.data, active=blur_face)
        self.score_painter = ScorePainter()
        local_painters = [GraphPainter(self.layout, epsilon=self.eps, alpha=0.4), BoxPainter(), self.score_painter]
        self.global_painters = [self.blur_painter] + [GlobalPainter(p) for p in local_painters]
        self.user_adjust = self.auto_adjust
        self.org_resolution = np.array(org_resolution)
        self.resolution = np.array(org_resolution)

    def set_blurring(self, blur_face):
        self.blur_painter.switch(blur_face)

    def set_resolution(self, width, height):
        new_resolution = np.array([width, height])
        for k in ['landmarks', 'boxes', 'face_boxes', 'blur_boxes']:
            if k in self.data.keys():
                self.data[k] = (self.data[k] / self.resolution * new_resolution).astype(int)
        self.score_painter.scale = (new_resolution / self.org_resolution)[0]
        self.resolution = new_resolution

    def draw(self, frame, frame_number):
        i = frame_number - self.user_adjust()
        paint_frame = frame.copy()
        for painter in self.global_painters:
            paint_frame = painter(paint_frame, self.data, i)
        return paint_frame

    def auto_adjust(self):
        return 0


class PlaceHolderVisualizer:
    def __init__(self):
        self.user_adjust = 0

    def auto_adjust(self):
        return 0

    def draw(self, frame, frame_number):
        return frame

    def set_resolution(self, width, height):
        pass

    def set_blurring(self, blur_face):
        pass