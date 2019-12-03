import numpy as np
import shlex
import json
import cv2
from subprocess import check_call

POSE_COCO_BODY_PARTS = {
    0:  "Nose",
    1:  "Neck",
    2:  "RShoulder",
    3:  "RElbow",
    4:  "RWrist",
    5:  "LShoulder",
    6:  "LElbow",
    7:  "LWrist",
    8:  "MidHip",
    9:  "RHip",
    10: "RKnee",
    11: "RAnkle",
    12: "LHip",
    13: "LKnee",
    14: "LAnkle",
    15: "REye",
    16: "LEye",
    17: "REar",
    18: "LEar",
    19: "LBigToe",
    20: "LSmallToe",
    21: "LHeel",
    22: "RBigToe",
    23: "RSmallToe",
    24: "RHeel",
    25: "Background"
}
POSE_COCO_PAIRS = [(0, 1), (1, 8),
                   (1, 2), (2, 3), (3, 4),
                   (1, 5), (5, 6), (6, 7),
                   (8, 9), (9, 10), (10, 11), (11, 22), (11, 24), (22, 23),
                   (8, 12), (12, 13), (13, 14), (14, 21), (14, 19), (19, 20),
                   (0, 15), (15, 17), (0, 16), (16, 18)]


def make_skeleton(open_pose, vid_path, skeleton_dst):
    cmd = f'"{open_pose}" --video "{vid_path}" --write_json "{skeleton_dst}" --display 0 --render_pose 0'
    print("About to run: {}".format(cmd))
    check_call(shlex.split(cmd), universal_newlines=True)


def visualize_frame(json_path):
    img_size = (1024, 1024, 3)
    img = np.zeros(img_size) * 255
    with open(json_path, 'r') as json_file:
        skeletons = json.loads(json_file.read())
        for idx, p in enumerate(skeletons['people']):
            p = p['pose_keypoints_2d']
            print(len(p))
            c = [(int(p[i]), int(p[i+1])) for i in range(0, len(p), 3)]
            for v1, v2 in POSE_COCO_PAIRS:
                if not (c[v1][0] + c[v1][0] == 0 or c[v2][0] + c[v2][0] == 0):
                    color = np.array([idx % 3 == 1, idx % 3 == 0, idx % 3 == 0]) * 255
                    cv2.line(img, c[v1], c[v2], [int(c) for c in color], 3)
    cv2.imshow("foo", img)
    cv2.waitKey()


if __name__ == '__main__':
    visualize_frame('C:/Users/talba/Dropbox/1-13/1-13_000000000000_keypoints.json')
    # make_skeleton('C:/research/openpose-1.5.0-binaries-win64-gpu-python-flir-3d_recommended/bin/OpenPoseDemo.exe',
    #               'C:/Users/Tal Barami/Desktop/code_test/1-12.avi',
    #               'C:/Users/Tal Barami/Desktop/code_test/1-12')
