import numpy as np
import shlex
import json
import cv2
import os
from subprocess import check_call
from os import listdir
from os.path import isfile, join, basename, splitext
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

COLORS_ARRAY = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 0), (128, 128, 128), (42, 42, 165)]

def make_skeleton(open_pose_path, vid_path, skeleton_dst):
    cwd = os.getcwd()
    os.chdir(open_pose_path)

    cmd = f'bin/OpenPoseDemo.exe --video "{vid_path}" --model_pose COCO --write_json "{skeleton_dst}" --display 0 --render_pose 0'
    print("About to run: {}".format(cmd))
    check_call(shlex.split(cmd), universal_newlines=True)

    os.chdir(cwd)


def visualize_frame(frame, json_path):
    if not isfile(json_path):
        print(f'No such file: {json_path}')
        return
    with open(json_path, 'r') as json_file:
        skeletons = json.loads(json_file.read())
        for p in skeletons['people']:
            pid = p['person_id']
            p = p['pose_keypoints_2d']

            c = [(int(p[i]), int(p[i + 1])) for i in range(0, len(p), 3)]
            for v1, v2 in POSE_COCO_PAIRS:
                if not (c[v1][0] + c[v1][1] == 0 or c[v2][0] + c[v2][1] == 0):
                    color = COLORS_ARRAY[pid] if pid < len(COLORS_ARRAY) else (255, 255, 255)
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


def pre_process(video, dst, resolution=(340, 526)):
    cap = cv2.VideoCapture(video)
    cap.set(cv2.CAP_PROP_FPS, 30.0)
    # fourcc = cv2.VideoWriter_fourcc(*'XVID') # For AVI?
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # fourcc = 0x00000021 # For MP4?
    out = cv2.VideoWriter(dst, fourcc, 30.0, (340, 526))
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, resolution)
            out.write(frame)
        else:
            cap.release()
            out.release()


def post_process(skeleton_folder, dst_folder, resolution=(340, 526)):
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

    unprocessed_video_path = join(video_path, video_name)
    processed_video_path = join(result_path, video_name)
    skeleton_path = join(result_path, video_name_no_ext)

    pre_process(unprocessed_video_path, processed_video_path)
    make_skeleton(openpose, processed_video_path, skeleton_path)
    post_process(skeleton_path, join(result_path, video_name_no_ext))

def play_skeleton(json_path):
    jsons = [f for f in listdir(json_path)]
    img_size = (900, 900)

    for j in jsons:
        img = np.zeros(img_size)
        visualize_frame(img, join(json_path, j))
        cv2.imshow("foo", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if __name__ == '__main__':
    # play_skeleton('D:/research/Ados Recordings/225202662/225202662_ADOS_021218_0935_2')
    set_person_id("D:/research/Ados Recordings/225202662/0")
    # s = 'C:/Users/TalBarami/Desktop/test'
    # t = 'C:/Users/TalBarami/Desktop/res'
    # v = '0aidJ-1R7Ds.mp4'
    #
    # preparation_pipepline(v, s, t)

    # cap = cv2.VideoCapture(s)
    # print(cap.get(cv2.CAP_PROP_FPS))
    # cap.set(cv2.CAP_PROP_FPS, 20.0)
    # print(cap.get(cv2.CAP_PROP_FPS))
    # print(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    # print(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # cap.release()
    # post_process(s)
    # pre_preocss(s, 'D:/research')

    # l = []
    # for root, dirs, files in os.walk('D:/research/Ados Recordings/225202662'):
    #     if not dirs:
    #         l.append(root)
    # l = l[51:]
    # for s in l:
    #     print(f'handling person-id: {s}')
    #     set_person_id(s)
