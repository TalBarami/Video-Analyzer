import numpy as np
import shlex
import json
import cv2
from subprocess import check_call
from os import listdir
from os.path import isfile, join

POSE_COCO_BODY_PARTS = {
    0: "Nose",
    1: "Neck",
    2: "RShoulder",
    3: "RElbow",
    4: "RWrist",
    5: "LShoulder",
    6: "LElbow",
    7: "LWrist",
    8: "MidHip",
    9: "RHip",
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


def visualize_frame(frame, json_path):
    if not isfile(json_path):
        print(f'Error: no such file {json_path}')
        return
    with open(json_path, 'r') as json_file:
        skeletons = json.loads(json_file.read())
        for idx, p in enumerate(skeletons['people']):
            p = p['pose_keypoints_2d']
            c = [(int(p[i]), int(p[i + 1])) for i in range(0, len(p), 3)]
            for v1, v2 in POSE_COCO_PAIRS:
                if not (c[v1][0] + c[v1][0] == 0 or c[v2][0] + c[v2][0] == 0):
                    color = (255 * (idx & 1 > 0), 255 * (idx & 2 > 0), 255 * (idx & 4 > 0))
                    cv2.line(frame, c[v1], c[v2], color, 3)


def read_json(file):
    with open(file, 'r') as j:
        return json.loads(j.read())


def write_json(j, dst):
    with open(dst, 'w') as f:
        json.dump(j, f)


def distance(k1, k2):
    k1 = np.array(k1)
    k2 = np.array(k2)
    return np.sum(np.power(k1 - k2, 2))


def set_person_id(json_src, json_dst, n_prevs):
    # jsons = [read_json(join(json_src, f)) for f in listdir(json_src) if isfile(join(json_src, f))]
    file_names = [f for f in listdir(json_src) if isfile(join(json_src, f))]
    src_path = lambda i: join(json_src, file_names[i])
    dst_path = lambda i: join(json_dst, file_names[i])

    jsons = [read_json(src_path(0))]
    for idx, p in enumerate(jsons[0]['people']):
        p['person_id'] = idx

    for i in range(1, len(file_names)):
        jsons.append(read_json(src_path(i)))

        p_prev = jsons[i - 1]['people']
        prev_ids = set([p['person_id'] for p in p_prev])
        curr_ids = []
        p_curr = jsons[i]['people']

        print(f'frame {i}')
        distances = np.zeros()
        for p in p_curr:
            found_id = str(np.argmin([distance(p['pose_keypoints_2d'], pj['pose_keypoints_2d']) for pj in p_prev]))
            if found_id not in curr_ids:
                curr_ids.append(found_id)
                p['person_id'] = found_id
            else:
                new_id = np.max(np.max(prev_ids), np.max(curr_ids))
                p['person_id'] = new_id
        if not (len([pi['person_id'] for pi in p_curr]) == len(set([pi['person_id'] for pi in p_curr]))):
            print(f'CRITICAL ERROR: 2 people with the same id in frame {i}')
        write_json(jsons[i], dst_path(i))


if __name__ == '__main__':
    set_person_id('C:/Users/Tal Barami/Desktop/jsons/1', 'C:/Users/Tal Barami/Desktop/jsons/a/1', 5)
