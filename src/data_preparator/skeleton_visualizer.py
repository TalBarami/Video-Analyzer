import shlex
from subprocess import check_call


def make_skeleton(open_pose, vid_path, skeleton_dst):
    cmd = f'"{open_pose}" --video "{vid_path}" --write_json "{skeleton_dst}" --display 0 --render_pose 0'
    print("About to run: {}".format(cmd))
    check_call(shlex.split(cmd), universal_newlines=True)


def visualize_frame(json):
    return 0

if __name__ == '__main__':
    make_skeleton('C:/research/openpose-1.5.0-binaries-win64-gpu-python-flir-3d_recommended/bin/OpenPoseDemo.exe',
                  'C:/Users/Tal Barami/Desktop/code_test/1-12.avi',
                  'C:/Users/Tal Barami/Desktop/code_test/1-12')
