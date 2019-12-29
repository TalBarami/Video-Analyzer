import json
import shlex
import os

from subprocess import check_call
from os.path import join


class DataCollector:
    def __init__(self):
        self.labels = ['clapping', 'hurdling', 'parkour', 'triple jump', 'air drumming', 'finger snapping', 'headbanging', 'shaking head', 'swinging legs']
        self.train = self.load_data('train')
        self.test = self.load_data('test')
        self.validate = self.load_data('validate')

    def load_data(self, name):
        if not os.path.isfile(f'resources/kinetics_sample/{name}.json'):
            with open(f'resources/kinetics400/{name}.json') as json_file:
                data = {k: v for k, v in json.load(json_file).items() if v['annotations']['label'] in self.labels}
            with open(f'resources/kinetics_sample/{name}.json', 'w') as outfile:
                json.dump(data, outfile)
        else:
            with open(f'resources/kinetics_sample/{name}.json') as json_file:
                data = json.load(json_file)

        return data

    def download(self, video_url, path):
        ydl_opts = {
            'outtmpl': f'{path}/raw/%(id)s.%(ext)s',
            'source_addreacs': '0.0.0.0',
            'format': 'mp4'
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e:
            print(f'Error: {e}')

    def cut(self, video_name, time, path):
        ffmpeg_extract_subclip(join(f'{path}/raw', f'{video_name}.mp4'), time[0], time[1], targetname=os.path.join(f'{path}/cut', f'{video_name}.mp4'))

    def to_skeleton(self, video_name, path):
        open_pose_path = 'C:/Research/openpose-1.5.1-binaries-win64-gpu-python-flir-3d_recommended/openpose'
        path = os.path.abspath(path)

        cwd = os.getcwd()
        os.chdir(open_pose_path)

        src = join(path, 'cut', f'{video_name}.mp4')
        dst = join(path, 'skeletons', video_name)
        cmd = f'bin/OpenPoseDemo.exe --video "{src}" --write_json "{dst}" --display 0 --render_pose 0'
        print("About to run: {}".format(cmd))
        check_call(shlex.split(cmd), universal_newlines=True)

        os.chdir(cwd)

    def prepare_video(self, video, info, path):
        self.download(info['url'], path)

        self.cut(video, info['annotations']['segment'], path)

        raw_path = f'{path}/raw/{video}.mp4'
        if os.path.exists(raw_path):
            os.remove(raw_path)

        self.to_skeleton(video, path)


    def download_and_extract(self, data, path):
        for v, info in data.items():
            self.prepare_video(v, info, path)
            # url = info['url']
            # print(f'Now downloading: {url}')
            # try:
            #     with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            #         ydl.download([url])
            #     self.cut(v, info['annotations']['segment'], path)
            # except Exception as e:
            #     print(f'Error: {e}')
            # finally:
            #     raw_path = f'{path}/raw/{v}.mp4'
            #     if os.path.exists(raw_path):
            #         os.remove(raw_path)


if __name__ == "__main__":
    d = DataCollector()
    # d.download_and_extract(d.train, 'resources/kinetics_sample/train')
    d.to_skeleton('8bInVTYhNhk', 'resources/kinetics_sample/train')