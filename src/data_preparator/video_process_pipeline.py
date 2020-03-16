import json
import os
import shlex
from json.decoder import JSONDecodeError
from os import listdir
from os.path import isfile, join, basename, splitext
from subprocess import check_call

import cv2
import numpy as np


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


def make_skeleton(open_pose_path, vid_path, skeleton_dst):
    cwd = os.getcwd()
    os.chdir(open_pose_path)

    cmd = f'bin/OpenPoseDemo.exe --video "{vid_path}" --model_pose COCO --write_json "{skeleton_dst}" --display 0 --render_pose 0'
    print("About to run: {}".format(cmd))
    check_call(shlex.split(cmd), universal_newlines=True)

    os.chdir(cwd)


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


def pre_process(video, dst, resolution=(340, 512)):
    cap = cv2.VideoCapture(video)
    cap.set(cv2.CAP_PROP_FPS, 30.0)
    # fourcc = cv2.VideoWriter_fourcc(*'XVID') # For AVI?
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(dst, fourcc, 30.0, resolution)
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE), resolution)
            out.write(frame)
        else:
            cap.release()
            out.release()


def post_process(skeleton_folder, dst_folder, resolution=(340, 512)):
    file_names = [join(skeleton_folder, f) for f in os.listdir(skeleton_folder) if isfile(join(skeleton_folder, f)) and f.endswith('json')]
    result = {'data': [], 'label': 0, 'label_index': 0}  # TODO: Set labels and stuff

    for i in range(1, 300):
        frame_entry = {'frame_index': i, 'skeleton': []}
        if i < len(file_names):
            json = read_json(file_names[i])
            people = json['people']
            for p in people:
                k = np.array([float(c) for c in p['pose_keypoints_2d']])
                x = np.round(k[::3] / resolution[0], 3)
                y = np.round(k[1::3] / resolution[1], 3)
                s = np.round(k[2::3], 3)
                pose = [e for l in zip(x, y) for e in l]
                frame_entry['skeleton'].append({'pose': pose, 'score': s.tolist()})
        result['data'].append(frame_entry)

    write_json(result, join(dst_folder, f'{basename(skeleton_folder)}.json'))


def preparation_pipepline(video_name, video_path, result_path):
    openpose = 'C:/Users/TalBarami/PycharmProjects/openpose-1.5.1-binaries-win64-gpu-python-flir-3d_recommended/openpose'

    video_name_no_ext = splitext(video_name)[0]
    unprocessed_video_path = join(video_path, video_name)
    processed_video_path = join(result_path, video_name)
    skeleton_path = join(result_path, video_name_no_ext)

    pre_process(unprocessed_video_path, processed_video_path)
    make_skeleton(openpose, processed_video_path, skeleton_path)
    post_process(skeleton_path, result_path)

if __name__ == '__main__':
    preparation_pipepline('nicky.mp4', 'C:/Users/TalBarami/Desktop/New folder', 'C:/Users/TalBarami/Desktop/New folder/out')
