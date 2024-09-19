import json
import requests
import random
import subprocess
import shutil
import os
import time

from pydub import AudioSegment

from config_parser import config
from season_generator.video_spring_generator import VideoSpringGenerator
from season_generator.video_summer_generator import VideoSummerGenerator
from season_generator.video_autumn_generator import VideoAutumnGenerator
from season_generator.video_winter_generator import VideoWinterGenerator


def get_ai_images(coze_token: str, flow_id: str) -> list[str]:
    result = []

    url = 'https://api.coze.cn/v1/workflow/run'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {coze_token}'
    }
    payload = {
        'workflow_id': flow_id,
    }
    try:
        with requests.Session() as session:
            session.timeout = 900
            session.trust_env = False
            response = session.post(url, headers=headers, json=payload)
            response.raise_for_status()
            tmp_json = json.loads(response.json()['data'])
            seasons = ['spring', 'summer', 'autumn', 'winter']
            result.extend(tmp_json[season] for season in seasons)
    except requests.exceptions.RequestException as e:
        print(f'API调用失败: {e}')

    return result


def merge_transition_videos(video_files: list[str],  out_path: str) -> None:
    """合并多个视频并在拼接处添加转场效果"""

    transitions = ['fade', 'smoothleft', 'smoothright', 'smoothup', 'smoothdown', 'circleopen', 'circleclose',
                   'vertopen', 'vertclose', 'horzopen', 'horzclose', 'dissolve', 'pixelize', 'diagtl', 'diagtr', 'diagbl', 'diagbr']

    tmp_folder = 'merge_folder'
    os.makedirs(tmp_folder, exist_ok=True)

    try:
        current_offset = 3
        current_video = video_files[0]
        for i, video_file in enumerate(video_files):
            if i == 0:
                continue

            tmp_video_path = f'{tmp_folder}/{time.strftime("%Y%m%d_%H%M%S")}.mp4'
            tmp_transition = random.choice(transitions)
            # 添加音频流处理
            cmd = f'ffmpeg -i "{current_video}" -i "{video_file}" -filter_complex "xfade=transition={tmp_transition}:duration=1:offset={current_offset},format=yuv420p,setpts=N/FRAME_RATE/TB" -c:v libx264 -preset slow -crf 22 -c:a aac -b:a 192k -y "{tmp_video_path}"'
            subprocess.run(cmd, shell=True, check=True)

            current_offset += 4
            current_video = tmp_video_path

        shutil.copyfile(current_video, out_path)
    finally:
        shutil.rmtree(tmp_folder, ignore_errors=True)


def add_bgm(input_path: str, output_path: str):
    audio_files = ['./resources/bgm/spring.mp3',
                   './resources/bgm/summer.mp3',
                   './resources/bgm/autumn.mp3',
                   './resources/bgm/winter.mp3']

    combined_audio = AudioSegment.silent(duration=0)

    tmp_mp3 = 'tmp_bgm.mp3'
    for index, audio_file in enumerate(audio_files):
        duration = 4000
        if index == 0 or index == len(audio_files)-1:
            duration = 3500
        audio = AudioSegment.from_file(audio_file)
        start_time = random.randint(0, len(audio) - duration)
        segment = audio[start_time:start_time + duration]

        # 添加渐入渐出效果
        fade_in_duration = 300  # 渐入时长
        fade_out_duration = 300  # 渐出时长
        segment = segment.fade_in(fade_in_duration).fade_out(fade_out_duration)

        combined_audio += segment

    combined_audio.export(tmp_mp3, format='mp3')

    cmd = f'ffmpeg -i "{input_path}" -i "{tmp_mp3}" -map 0:v -map 1:a -c:v copy -c:a aac -shortest "{output_path}" -y'
    subprocess.run(cmd, shell=True, check=True)

    if os.path.exists(tmp_mp3):
        os.remove(tmp_mp3)


if __name__ == '__main__':
    seasons = {
        'spring': VideoSpringGenerator(),
        'summer': VideoSummerGenerator(),
        'autumn': VideoAutumnGenerator(),
        'winter': VideoWinterGenerator()
    }

    index = 0
    while (True):
        index += 1

        images = get_ai_images(config.coze_token, config.coze_flow_id)
        if not images:
            raise ValueError('没有获取到有效图片')

        tmp_folder = 'tmp_main_folder'
        os.makedirs(tmp_folder, exist_ok=True)

        tmp_videos = []
        for index, (season, generator) in enumerate(seasons.items()):
            tmp_video = f'{tmp_folder}/tmp_{season}.mp4'
            generator.generate(images[index], tmp_video)
            tmp_videos.append(tmp_video)

        tmp_transition = f'{tmp_folder}/transition.mp4'
        merge_transition_videos(tmp_videos, tmp_transition)

        output = f'{config.output_folder}/{time.strftime("%Y%m%d_%H%M%S")}.mp4'
        add_bgm(tmp_transition, output)
        print(f'生成成功：{output}')

        if os.path.exists(tmp_folder):
            shutil.rmtree(tmp_folder)

        if index >= config.generate_count:
            break
