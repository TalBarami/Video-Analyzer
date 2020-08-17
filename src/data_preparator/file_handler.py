import os
import shlex
import pandas as pd
import numpy as np
from os import path
from subprocess import check_call
from pathlib import Path
from shutil import copyfile

def encrypt(x):
    return str(int(x) * 3 - 2015)

def decrypt(y):
    return str((int(y) + 2015) / 3)


def find_and_copy(ids, src, dst):
    for cid in ids:
        encrypted_cid = encrypt(cid[:8])
        for root, dirs, files in os.walk(src):
            found = [path.join(root, d) for d in dirs if (cid[:8] in d)]
            if any(found):
                for d in found:
                    dst_path = path.join(dst, encrypted_cid)
                    print(f'copy from \"{d}\" to \"{dst_path}\"')

                    first_time = True
                    for file in os.listdir(d):
                        parts = [str(x) for x in file.split('_')]
                        parts[0] = encrypted_cid

                        if len(parts) < 5:
                            i = 0
                            while first_time and path.isdir(path.join(dst_path, str(i))):
                                i += 1
                            dst_dir = str(i)
                            first_time = False
                        else:
                            dst_dir = f'{parts[-3]}_{parts[-4]}'

                        if path.isdir(path.join(dst_path, dst_dir)):
                            print(f'Directory exists: {path.join(dst_path, dst_dir)}')
                        dst_file = path.join(dst_path, dst_dir, '_'.join(parts))
                        if path.isfile(dst_file):
                            print(f'Error: file already exists: {dst_file}')
                            continue
                        print(f'cp {path.join(d, file)} -> {path.join(dst_path,dst_dir, dst_file)}')
                        Path(path.join(dst_path, dst_dir)).mkdir(parents=True, exist_ok=True)
                        copyfile(path.join(d, file), dst_file)

    df.to_csv('D:/TalBarami/sample/users.csv', index=False)


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
    df = pd.read_excel('D:/TalBarami/Tal_27_07_2020.xlsx')
    df = df[df['patient_id'] > 0]
    ids = df['patient_id'].unique().astype(str)

    ids = ids[np.where(ids == '338678907')[0][0]:] # resume after failure
    for id in ids:
        print(id)

    # find_and_copy(ids, 'Z:/NetBakData/ADOS weekly backups/NetBakData/User@CAMERACOMP/Disk C/RecordingsBackUp', 'Z:/Tal_Barami_Temporary')

    # find_and_copy(, 'Z:/NetBakData/ADOS weekly backups/NetBakData/User@CAMERACOMP/Disk C/RecordingsBackUp', 'D:/TalBarami/sample')
    # find_and_copy(['222109175'], 'Z:/NetBakData/ADOS weekly backups/NetBakData/User@CAMERACOMP/Disk C/RecordingsBackUp', 'D:/TalBarami/sample')
    # with open('D:/TalBarami/openpose/research/ids.txt') as f:
    #     ids = f.read().splitlines()
    # src = 'E:/ADOS_Video_New_System'
    # dst = 'D:/TalBarami/vids'
    # find_and_copy(ids, src, dst)
    # convert_videos('D:/TalBarami/vids', 'D:/TalBarami/skeletons')
