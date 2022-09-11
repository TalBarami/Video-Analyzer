import numpy as np
from skeleton_tools.openpose_layouts.body import COCO_LAYOUT
from skeleton_tools.skeleton_visualization.numpy_visualizer import MMPoseVisualizer
from skeleton_tools.skeleton_visualization.pyfeat_visualizer import PyfeatVisualizer
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
        self.vis = PyfeatVisualizer(blur_face=blur_face)
        self.pyfeat_out_path = pyfeat_out_path
        self.groups = read_pkl(self.pyfeat_out_path)
        for g in self.groups.values():
            g['FaceRectX'] += (g['FaceRectWidth'] / 2)
            g['FaceRectY'] += (g['FaceRectHeight'] / 2)
        self.user_adjust = self.auto_adjust
        self.org_resolution = org_resolution
        self.resolution = org_resolution
        self.last_frame = 0

    def set_blurring(self, blur_face):
        self.vis.blur_face = blur_face

    def set_resolution(self, width, height):
        self.resolution = (width, height)
        for g in self.groups.values():
            g[['FaceRectX', 'FaceRectY', 'FaceRectWidth', 'FaceRectHeight']] /= np.array(
                self.org_resolution + self.org_resolution)
            g[['FaceRectX', 'FaceRectY', 'FaceRectWidth', 'FaceRectHeight']] *= np.array(
                self.resolution + self.resolution)
        # self.df[['FaceRectX', 'FaceRectY', 'FaceRectWidth', 'FaceRectHeight']] /= np.array(self.resolution + self.resolution)
        # self.resolution = (width, height)
        # self.df[['FaceRectX', 'FaceRectY', 'FaceRectWidth', 'FaceRectHeight']] *= np.array(self.resolution + self.resolution)
        # self.groups = {i: g for i, g in self.df.groupby('frame')}
        self.last_frame = min(self.groups.keys())

    def draw(self, frame, frame_number):
        i = frame_number - self.user_adjust()
        if i in self.groups.keys():
            self.last_frame = i
        frame = self.vis.draw_facebox(frame, self.groups[self.last_frame])
        return frame

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