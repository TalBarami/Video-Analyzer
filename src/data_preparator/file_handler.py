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


def find_and_copy(ids):
    for cid in ids:
        for root, dirs, files in os.walk('PATH_TO_BE_PASSED'):
            found = [join(root, d) for d in dirs if d == cid]
            if any(found):
                for f in found:
                    copy_tree(f, join('ANOTHER_PATH_TO_BE_PASSED', cid))

# name = 'a1'
# path = 'C:/Users/talba/Desktop/root'
# for root, dirs, files in os.walk(path):
#     found = [join(root, dir) for dir in dirs if dir == name]
#     if len(found) > 0:
#         result = [glob.glob(f'{f}/**', recursive=True) for f in found]