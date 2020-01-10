import numpy as np
import shlex
import json
import cv2
import os
from subprocess import check_call
from os import listdir
from os.path import isfile, join
from json.decoder import JSONDecodeError

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
            pid = p['person_id'] + 1
            p = p['pose_keypoints_2d']

            c = [(int(p[i]), int(p[i + 1])) for i in range(0, len(p), 3)]
            for v1, v2 in POSE_COCO_PAIRS:
                if not (c[v1][0] + c[v1][1] == 0 or c[v2][0] + c[v2][1] == 0):
                    color = (255 * (pid & 4 > 0), 255 * (pid & 2 > 0), 255 * (pid & 1 > 0))
                    cv2.line(frame, c[v1], c[v2], color, 3)


def read_json(file):
    try:
        with open(file, 'r') as j:
            return json.loads(j.read())
    except (OSError, UnicodeDecodeError, JSONDecodeError) as e:
        print(f'Error while reading json file: {file}')
        print(e)
        return


def write_json(j, dst):
    with open(dst, 'w') as f:
        json.dump(j, f)


# def distance(p1, p2):
#     k1 = np.array([float(c) for c in p1['pose_keypoints_2d']])
#     k2 = np.array([float(c) for c in p2['pose_keypoints_2d']])
#     epsilon = 1e-3
#     xy1 = []
#     xy2 = []
#     for i in range(0, len(p1['pose_keypoints_2d']), 3):
#         if k1[i + 2] < epsilon or k2[i + 1] < epsilon:
#             continue
#         xy1 += [k1[i], k1[i + 1]]
#         xy2 += [k2[i], k2[i + 1]]
#
#     return np.sum(np.power(np.array(xy1) - np.array(xy2), 2))

def distance(p1, p2):
    x1, y1 = center_of_mass(p1)
    x2, y2 = center_of_mass(p2)

    if not any([x for x in [x1, x2, y1, y2] if x is np.NaN]):
        return np.sqrt(np.power(x1 - x2, 2) + np.power(y1 - y2, 2))
    else:
        return np.inf


def center_of_mass(p):
    k = np.array([float(c) for c in p['pose_keypoints_2d']])
    coords = [c for c in zip(k[::3], k[1::3], k[2::3])]
    threshold = 0.1

    x = np.array([c[0] for c in coords if c[2] > threshold]).mean()
    y = np.array([c[1] for c in coords if c[2] > threshold]).mean()

    return x, y


def find_closest(p, prevs):
    ids = set([pi['person_id'] for pi in prevs])
    id_weights = dict([(i, []) for i in ids])
    for pi in prevs:
        d = distance(p, pi)
        id_weights[pi['person_id']].append(d)

    for i in ids:
        id_weights[i] = np.mean(id_weights[i])

    if len(id_weights) > 0:
        selected_id = min(id_weights, key=id_weights.get)
        selected_weight = id_weights[selected_id]
    else:
        selected_id = 0
        selected_weight = 0
    return selected_id, selected_weight


def match_frames(ps, prevs):
    def gen_id(ps):
        ids = [p['person_id'] for p in ps]
        i = 0
        while i in ids:
            i += 1
        return i

    found = {}
    for p in ps:
        new_id, d_new = find_closest(p, prevs)
        if new_id in found:
            p_old, d_old = found[new_id]
            generated_id = gen_id(prevs + [v[0] for v in found.values()])
            if d_old < d_new:
                new_id = generated_id
            else:
                p_old['person_id'] = generated_id
                found[generated_id] = (p_old, d_old)
                p['person_id'] = new_id
        p['person_id'] = new_id
        found[new_id] = (p, d_new)


def set_person_id(json_src, n=5, verbose=10000):
    file_names = [f for f in listdir(json_src) if isfile(join(json_src, f)) and f.endswith('json')]

    def src_path(i):
        return join(json_src, file_names[i])

    def dst_path(i):
        return join(json_src, file_names[i])

    jsons = [read_json(src_path(0))]
    for idx, p in enumerate(jsons[0]['people']):
        p['person_id'] = idx
    write_json(jsons[0], dst_path(0))

    for i in range(1, len(file_names)):
        jsons.append(read_json(src_path(i)))
        people = jsons[i]['people']

        prevs = []
        for j in range(min(n, i)):
            for p in jsons[j]['people']:
                prevs.append(p)

        match_frames(people, prevs)

        write_json(jsons[i], dst_path(i))

        if i % verbose == 0:
            print(f'frame: {i}')


if __name__ == '__main__':
    l = []
    for root, dirs, files in os.walk('D:/TalBarami/skeletons'):
        if not dirs:
            l.append(root)
    for s in l:
        print(f'handling person-id: {s}')
        set_person_id(s)
