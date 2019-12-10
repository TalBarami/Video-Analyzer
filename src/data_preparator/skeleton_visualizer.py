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
        for p in skeletons['people']:
            pid = p['person_id']
            p = p['pose_keypoints_2d']
            c = [(int(p[i]), int(p[i + 1])) for i in range(0, len(p), 3)]
            for v1, v2 in POSE_COCO_PAIRS:
                if not (c[v1][0] + c[v1][0] == 0 or c[v2][0] + c[v2][0] == 0):
                    color = (255 * (pid & 1 > 0), 255 * (pid & 2 > 0), 255 * (pid & 4 > 0))
                    cv2.line(frame, c[v1], c[v2], color, 3)


def read_json(file):
    with open(file, 'r') as j:
        return json.loads(j.read())


def write_json(j, dst):
    with open(dst, 'w') as f:
        json.dump(j, f)


def center_of_mass(p):
    size = len(p['pose_keypoints_2d'])
    return np.sum([p['pose_keypoints_2d'][x] for x in range(0, size, 3)]) / (size / 3), np.sum([p['pose_keypoints_2d'][y] for y in range(1, size, 3)]) / (size / 3)


def distance(p1, p2):
    k1 = np.array(p1['pose_keypoints_2d'])
    k2 = np.array(p2['pose_keypoints_2d'])
    return np.sum(np.power(k1 - k2, 2))


def find_closest(p, prevs):
    ids = set([p['person_id'] for p in prevs])
    id_weights = dict([(i, 0) for i in ids])
    for pi in prevs:
        id_weights[pi['person_id']] += (1 / distance(p, pi))

    return max(id_weights, key=id_weights.get)


def set_person_id(json_src, json_dst, n=5):
    file_names = [f for f in listdir(json_src) if isfile(join(json_src, f))]
    src_path = lambda i: join(json_src, file_names[i])
    dst_path = lambda i: join(json_dst, file_names[i])

    jsons = [read_json(src_path(0))]
    for idx, p in enumerate(jsons[0]['people']):
        p['person_id'] = idx

    for i in range(1, len(file_names)):
        jsons.append(read_json(src_path(i)))

        prevs = []
        for j in range(np.min(n, i)):
            for p in jsons[j]['people']:
                prevs.append(p)

        jsons[i]['person_id'] = find_closest(jsons[i], prevs)

        a = list(set([p['person_id'] for p in prevs]))
        b = [p['person_id'] for p in jsons[i]['people']]
        a.sort()
        b.sort()
        if not a == b:
            print("CRITICAL ERROR!!! NOT ENOUGH PREVS! 2 PEOPLE WITH THE SAME ID")
            print(a)
            print(b)

        write_json(jsons[i], dst_path(i))


if __name__ == '__main__':
    set_person_id('E:/jsons/1', 'E:/jsons/1/a')
