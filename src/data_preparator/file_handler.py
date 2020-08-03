import os
import shlex
from distutils.dir_util import copy_tree
from os import path
from subprocess import check_call


def encrypt(x):
    return x * 3 - 2015


def decrypt(y):
    (y + 2015) / 3


def find_and_copy(ids, src, dst):
    for cid in ids:
        for root, dirs, files in os.walk(src):
            found = [path.join(root, d) for d in dirs if (cid[:8] in d)]
            if any(found):
                for f in found:
                    idx = 0
                    dirname = f'{cid}_{path.basename(root)}'
                    dst_path = path.join(dst, dirname)
                    while os.path.exists(f'{dst_path}_{idx}'):
                        idx += 1
                    dst_path = f'{dst_path}_{idx}'
                    print(f'copy from \"{f}\" to \"{dst_path}\"')
                    # copy_tree(f, path.join(dst, dirname))


def to_skeleton(src, dst):
    print(f'src={src}, dst={dst}')
    open_pose_path = 'D:/TalBarami/openpose/openpose-1.5.0-binaries-win64-gpu-python-flir-3d_recommended'
    cwd = os.getcwd()
    print(f'cwd: {cwd}')
    os.chdir(open_pose_path)

    cmd = f'bin/OpenPoseDemo.exe --video "{src}" --display 0 --write_json "{dst}" --write_video "{dst}/result.avi"'
    print("About to run: {}".format(cmd))
    check_call(shlex.split(cmd), universal_newlines=True)
    os.chdir(cwd)


def convert_videos(vids, skeletons):
    for root, dirs, files in os.walk(vids):
        for f in files:
            src = path.join(root, f)
            dst = path.join(skeletons, os.path.basename(os.path.normpath(root)), os.path.splitext(f)[0])
            if not os.path.exists(dst):
                os.makedirs(dst)
            to_skeleton(src, dst)


if __name__ == '__main__':
    print('222109175'[:8])
    find_and_copy(['222109175'], 'Z:/NetBakData/ADOS weekly backups/NetBakData/User@CAMERACOMP/Disk C/RecordingsBackUp', 'D:/TalBarami/sample')
    # with open('D:/TalBarami/openpose/research/ids.txt') as f:
    #     ids = f.read().splitlines()
    # src = 'E:/ADOS_Video_New_System'
    # dst = 'D:/TalBarami/vids'
    # find_and_copy(ids, src, dst)
    # convert_videos('D:/TalBarami/vids', 'D:/TalBarami/skeletons')
