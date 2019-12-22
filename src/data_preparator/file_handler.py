import os
import glob

from os.path import join, splitext, isfile
from shutil import copy2
from distutils.dir_util import copy_tree

def encrypt(x):
    return x * 3 - 2015


def decrypt(y):
    (y + 2015) / 3


# def search(directory, name):
#     result = []
#     for root, dirs, files in os.walk(directory):
#         found = [join(root, f) for f in files if splitext(f) == name]
#         result += found
#     return result

# def search(directory, name):
#     for root, dirs, files in os.walk(directory):
#         result = []
#         found = [join(root, d) for d in dirs if d == name]
#         if len(found) > 0:
#             result += [glob.glob(f'{f}/**', recursive=True) for f in found]
#         return result
#
#
# def collect_files(ids):
#     for cid in ids:
#         matches = search('', cid)
#         for file in matches:
#             if isfile(file):
#                 copy2(file, join('some_path', cid))  # TODO: Make sure we don't get the same file name twice.


def find_and_copy(ids, src, dst):
    for cid in ids:
        for root, dirs, files in os.walk(src):
            found = [join(root, d) for d in dirs if d == cid]
            if any(found):
                for f in found:
                    dst_path = join(dst, cid)
                    if os.path.exists(dst_path):
                        dst_path += _
                    print(f'copy from {f} to {join(dst, cid)}')
                    copy_tree(f, join(dst, cid))

if __name__ == '__main__':
    with open('D:/TalBarami/openpose/research/ids.txt') as f:
        ids = f.read().splitlines()
    src = 'E:/ADOS_Video_New_System'
    dst = 'D:/TalBarami/vids'
    find_and_copy(ids, src, dst)