import json
import time
from os import listdir
from os.path import isfile, join

import cv2
import numpy as np

# POSE_BODY_25_MAP = {
#     0: "Nose",
#     1: "Neck",
#     2: "RShoulder",
#     3: "RElbow",
#     4: "RWrist",
#     5: "LShoulder",
#     6: "LElbow",
#     7: "LWrist",
#     8: "MidHip",
#     9: "RHip",
#     10: "RKnee",
#     11: "RAnkle",
#     12: "LHip",
#     13: "LKnee",
#     14: "LAnkle",
#     15: "REye",
#     16: "LEye",
#     17: "REar",
#     18: "LEar",
#     19: "LBigToe",
#     20: "LSmallToe",
#     21: "LHeel",
#     22: "RBigToe",
#     23: "RSmallToe",
#     24: "RHeel",
#     25: "Background"
# }
# POSE_BODY_25_PAIRS = [(0, 1), (1, 8),
#                       (1, 2), (2, 3), (3, 4),
#                       (1, 5), (5, 6), (6, 7),
#                       (8, 9), (9, 10), (10, 11), (11, 22), (11, 24), (22, 23),
#                       (8, 12), (12, 13), (13, 14), (14, 21), (14, 19), (19, 20),
#                       (0, 15), (15, 17), (0, 16), (16, 18)]
from src.data_preparator.video_process_pipeline import read_json

POSE_COCO_MAP = {
    0: "Nose",
    1: "Neck",
    2: "RShoulder",
    3: "RElbow",
    4: "RWrist",
    5: "LShoulder",
    6: "LElbow",
    7: "LWrist",
    8: "RHip",
    9: "RKnee",
    10: "RAnkle",
    11: "LHip",
    12: "LKnee",
    13: "LAnkle",
    14: "REye",
    15: "LEye",
    16: "REar",
    17: "LEar"
}
POSE_COCO_PAIRS = [(0, 1),
                   (1, 2), (2, 3), (3, 4),
                   (1, 5), (5, 6), (6, 7),
                   (1, 8), (8, 9), (9, 10),
                   (1, 11), (11, 12), (12, 13),
                   (0, 15), (15, 17), (0, 14), (14, 16)]

COLORS_ARRAY = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 0), (128, 128, 128), (42, 42, 165)]


def draw_skeleton(image, pose, score, joint_colors, edge_color=(255, 255, 255), skeleton_type=None, epsilon=1e-3):
    if skeleton_type is None:
        skeleton_type = POSE_COCO_PAIRS
    for (v1, v2) in skeleton_type:
        if score[v1] > epsilon and score[v2] > epsilon:
            cv2.line(image, pose[v1], pose[v2], edge_color, thickness=3)
    for i, (x, y) in enumerate(pose):
        cv2.circle(image, (x, y), 2, joint_colors[i], thickness=2)


def visualize_frame_pre_processed(json, image, frame_index, width=320, height=240):
    v = json['data']

    colors = np.ones(shape=(len(POSE_COCO_MAP), 3)) * 255
    f = v[frame_index]
    for s in f['skeleton']:
        x = np.array(s['pose'][0::2]) * width
        y = np.array(s['pose'][1::2]) * height
        s['pose'] = [int(np.round(item, 1)) for sublist in zip(x, y) for item in sublist]

        draw_skeleton(image, [x for x in zip(s['pose'][0::2], s['pose'][1::2])], s['score'], colors)


# def visualize_frame_pre_processed(frame, json_path, skeleton_type):
#     if not isfile(json_path):
#         print(f'No such file: {json_path}')
#         return
#     with open(json_path, 'r') as json_file:
#         skeletons = json.loads(json_file.read())
#         for p in skeletons['people']:
#             pid = p['person_id']
#             p = p['pose_keypoints_2d']
#             pose = [(int(p[i]), int(p[i + 1])) for i in range(0, len(p), 3)]
#             score = [p[i] for i in range(2, len(p), 3)]
#             color = COLORS_ARRAY[pid] if pid < len(COLORS_ARRAY) else (255, 255, 255)
#
#             draw_skeleton(frame, pose, score, color, skeleton_type)


def visualize_frame_post_processed(frame, video_data, frame_number, skeleton_type):
    if frame_number not in range(0, len(video_data)):
        print(f'Invalid frame number: {frame_number}. Expected between: 0 and {len(video_data)}')

    for p in video_data[frame_number]['skeleton']:
        draw_skeleton(frame, [x for x in zip(p['pose'][0::2], p['pose'][1::2])], p['score'], (255, 255, 255), skeleton_type)


def visualize_frame_tensor(frame, M, frame_number, skeleton_type):
    P, F, T, V = M.shape  # People, Features, Time, Vertices
    P = 1  # TODO: Currently supports only 1 person
    for p in range(P):
        pose = [(M[p][0][frame_number][i], M[p][1][frame_number][i]) for i in range(V)]
        score = [M[p][2][frame_number][i] for i in range(V)]
        draw_skeleton(frame, pose, score, (255, 255, 255), skeleton_type)


def play_skeleton(skeleton, method, resolution=(340, 512)):
    def pre_processed(jsons_dir):
        jsons = [f for f in listdir(jsons_dir)]
        return len(jsons), lambda img, i: visualize_frame_pre_processed(img, join(jsons_dir, jsons[i]), POSE_COCO_PAIRS)

    def post_processed(json_path):
        if not isfile(json_path):
            print(f'No such file: {json_path}')
            return
        with open(json_path, 'r') as json_file:
            # img_size = (1200, 1200, 3)
            video_data = json.loads(json_file.read())['data']
            for i in range(len(video_data)):
                for p in video_data[i]['skeleton']:
                    for k in range(len(p['pose'])):
                        p['pose'][k] = int(p['pose'][k] * resolution[k % 2])
        return len(video_data), lambda img, i: visualize_frame_post_processed(img, video_data, i, POSE_COCO_PAIRS)

    def tensor(M):
        scale = 30
        P, F, T, V = M.shape  # People, Features, Time, Vertices
        for i in range(P):
            M[i][0] += np.abs(M[i][0].min())
            M[i][0] *= scale
            M[i][1] += np.abs(M[i][1].min())
            M[i][1] *= scale * (resolution[1] / resolution[0])
        return T, lambda img, i: visualize_frame_tensor(img, M, i, POSE_COCO_PAIRS)

    methods = {'pre-processed': pre_processed,
               'post-processed': post_processed,
               'tensor': tensor}

    frames, f = methods[method](skeleton)
    img_size = (1200, 1200, 3)
    for i in range(frames):
        img = np.zeros(img_size)
        f(img, i)
        cv2.imshow("foo", img)
        time.sleep(0.01)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def visualize_features(M, filename):
    P, F, T, V = M.shape  # People, Features, Time, Vertices
    P = 1

    size = 20
    sepX = 0
    sepY = 10
    vertex_text = 100
    feature_sep = 50

    img_size = (F * (V * (size + sepY) + feature_sep), 2 * vertex_text + T * (size + sepX))
    img = np.zeros(img_size)
    for p in range(P):
        y = feature_sep
        for f in range(F):
            cv2.putText(img, f'feature {f}', (5 * size, y - size), cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=255, lineType=2)
            for v in range(V):
                cv2.putText(img, f'{POSE_COCO_MAP[v]}', (size, y + size), cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=255, lineType=2)
                cv2.putText(img, f'{POSE_COCO_MAP[v]}', (img_size[1] - vertex_text + size, y + size), cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=255, lineType=2)
                c = np.array(M[p][f]).T[v]
                c = np.nan_to_num((c - np.min(c)) / np.ptp(c))
                x = vertex_text
                for t in range(T):
                    cv2.rectangle(img, (x, y), (x + size, y + size), float(c[t]), cv2.FILLED)
                    x += size + sepX
                y += size + sepY
            y += feature_sep
    # cv2.imshow('foo', img)
    # cv2.waitKey(0)
    cv2.imwrite(f'{filename}.jpg', img * 255)


if __name__ == '__main__':
    print(1)

    # play_skeleton('C:/Users/TalBarami/PycharmProjects/Video-Analyzer/src/data_preparator/ac/nicky/nicky.json', 'post-processed')

    # play_skeleton(M, 'tensor')
    # play_skeleton('C:/Users/TalBarami/PycharmProjects/Video-Analyzer/src/data_preparator/ac/out/alon/alon.json', 'post-processed')

    # play_openpose_skeleton('C:/Users/TalBarami/PycharmProjects/Video-Analyzer/src/data_preparator/ac/out/alon')
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
