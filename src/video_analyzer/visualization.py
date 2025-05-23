# from pathlib import Path
# from os import path as osp
#
# import numpy as np
# import pandas as pd
# from skeleton_tools.openpose_layouts.body import COCO_LAYOUT
# from skeleton_tools.openpose_layouts.face import PYFEAT_FACIAL
# from skeleton_tools.skeleton_visualization.data_prepare.data_extract import PyfeatDataExtractor, MMPoseDataExtractor
# from skeleton_tools.skeleton_visualization.paint_components.frame_painters.base_painters import BlurPainter, GlobalPainter
# from skeleton_tools.skeleton_visualization.paint_components.frame_painters.local_painters import ScorePainter, GraphPainter, BoxPainter
#
#
# class Visualizer:
#     def __init__(self, model_output_path, data_layout, extractor_initializer, epsilon, org_resolution, blur_face):
#         self.model_output_path = model_output_path
#         self.layout = data_layout
#         self.eps = epsilon
#         self.extractor = extractor_initializer(self.layout)
#         filepath = Path(model_output_path)
#         self.data = self.extractor({'paths': {'processed': str(filepath.parents[2])}, 'name': osp.splitext(filepath.name)[0]})
#         self.blur_painter = BlurPainter(self.data, active=blur_face)
#         self.score_painter = ScorePainter()
#         local_painters = [GraphPainter(self.layout, epsilon=self.eps, alpha=0.4, color=[(159, 180, 255), (255, 211, 110), (153, 255, 205), (255, 245, 109)])]
#         # local_painters = [GraphPainter(self.layout, epsilon=self.eps, alpha=0.4), BoxPainter()]
#         self.global_painters = [self.blur_painter] + [GlobalPainter(p) for p in local_painters]
#         self.user_adjust = self.auto_adjust
#         self.org_resolution = np.array(org_resolution)
#         self.resolution = np.array(org_resolution)
#
#     def set_blurring(self, blur_face):
#         self.blur_painter.switch(blur_face)
#
#     def set_resolution(self, width, height):
#         new_resolution = np.array([width, height])
#         for k in ['landmarks', 'boxes', 'face_boxes', 'blur_boxes']:
#             if k in self.data.keys():
#                 self.data[k] = (self.data[k] / self.resolution * new_resolution).astype(int)
#         self.score_painter.scale = (new_resolution / self.org_resolution)[0]
#         self.resolution = new_resolution
#
#     def draw(self, frame, frame_number):
#         i = frame_number - self.user_adjust()
#         paint_frame = frame.copy()
#         for painter in self.global_painters:
#             paint_frame = painter(paint_frame, self.data, i)
#         return paint_frame
#
#     def auto_adjust(self):
#         return 0
#
#
#
# class SkeletonVisualizer(Visualizer):
#     def __init__(self, skeleton_path, org_resolution, blur_face=False):
#         super().__init__(skeleton_path, COCO_LAYOUT, MMPoseDataExtractor, 0.4, org_resolution, blur_face)
#
#
# class FacialVisualizer(Visualizer):
#     def __init__(self, pyfeat_out_path, org_resolution, blur_face=False):
#         super().__init__(pyfeat_out_path, PYFEAT_FACIAL, PyfeatDataExtractor, 0.98, org_resolution, blur_face)
#
#
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