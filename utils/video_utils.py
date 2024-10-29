import subprocess
import io
import os
import shutil
import random
import time
from datetime import datetime

import requests
import cv2
from pydub import AudioSegment
from PIL import Image


def get_video_duration(file_path: str) -> float:
    """获取媒体时长

    Args:
        file_path (str): 视频文件
    Returns:
        float: 视频时长
    """
    tmp_cmd = 'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "%s"' % file_path
    result = subprocess.run(tmp_cmd, shell=True,
                            capture_output=True, text=True)
    return float(result.stdout)


def get_video_size(video_path: str) -> tuple[int, int]:
    """获取视频size

    Args:
        video_path (str): 视频文件路径

    Returns:
        tuple[int, int]: width,height
    """
    video = cv2.VideoCapture(video_path)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video.release()

    return width, height


def add_decoration(input_path: str, output_path: str):
    width, height = get_video_size(input_path)
    decoration_file = './resources/decorations/decorations.mp4'

    cmd = f'ffmpeg -i "{input_path}" -i "{decoration_file}" -filter_complex "\
        [1:v]scale={width}:{height},split=2[mask1][mask2];\
        [mask1][mask2]alphamerge[mask];\
        [0:v][mask]overlay;\
        " -shortest -y "{output_path}"'
    subprocess.run(cmd, shell=True, check=True)


def add_bgm(input_path: str, output_path: str):
    audio_files = ['./resources/bgm/spring.mp3',
                   './resources/bgm/summer.mp3',
                   './resources/bgm/autumn.mp3',
                   './resources/bgm/winter.mp3']

    combined_audio = AudioSegment.silent(duration=0)

    tmp_mp3 = 'tmp_bgm.mp3'
    for audio_file in audio_files:
        duration = 1800
        audio = AudioSegment.from_file(audio_file)
        start_time = random.randint(0, len(audio) - duration)
        segment = audio[start_time:start_time + duration]

        # 添加渐入渐出效果
        fade_in_duration = 10  # 渐入时长
        fade_out_duration = 10  # 渐出时长
        segment = segment.fade_in(fade_in_duration).fade_out(fade_out_duration)

        combined_audio += segment

    bgm_audio = AudioSegment.from_file('./resources/bgm/bgm.mp3')
    bgm_audio = bgm_audio.apply_gain(-15)
    combined_audio = combined_audio.overlay(bgm_audio)

    combined_audio.export(tmp_mp3, format='mp3')

    cmd = f'ffmpeg -i "{input_path}" -i "{tmp_mp3}" -map 0:v -map 1:a -c:v copy -c:a aac -shortest "{output_path}" -y'
    subprocess.run(cmd, shell=True, check=True)

    if os.path.exists(tmp_mp3):
        os.remove(tmp_mp3)


def merge_transition_videos(video_files: list[str],  out_path: str, part_duration: float = 0.6, transition_duration: float = 0.15) -> None:
    """合并多个图片并在拼接处添加渐变转场效果"""
    edge_duration = part_duration + (transition_duration/2)
    normal_duration = part_duration + transition_duration

    tmp_folder = 'merge_folder'
    os.makedirs(tmp_folder, exist_ok=True)

    mp3 = "./resources/bgm/spring.mp3"
    current_video = None
    try:
        for i in range(len(video_files)-1, -1, -1):
            tmp_video_path = f'{tmp_folder}/part_{i}.mp4'
            tmp_image_path = _save_ai_image(video_files[i], tmp_folder)
            tmp_duration = edge_duration if i == len(video_files) - 1 or i == 0 else normal_duration
            cmd = f'ffmpeg -loop 1 -i "{tmp_image_path}" -t {tmp_duration} -vf "setpts=PTS-STARTPTS" -r 30 -pix_fmt yuv420p -c:v libx264 -preset slow -crf 22 "{tmp_video_path}" -y'
            subprocess.run(cmd, shell=True, check=True)
            if i == len(video_files)-1:
                current_video = tmp_video_path
                continue
            current_video_path = f'{tmp_folder}/current_video_{i}.mp4'
            cmd = f'ffmpeg -i "{tmp_video_path}" -i "{current_video}" -filter_complex "xfade=transition=fade:duration={transition_duration}:offset={tmp_duration - transition_duration},format=yuv420p,setpts=PTS-STARTPTS" -c:v libx264 -preset slow -crf 22 -c:a aac -b:a 192k -y "{current_video_path}"'
            subprocess.run(cmd, shell=True, check=True)
            current_video = current_video_path
    finally:
        cmd = f'ffmpeg -i "{current_video}" -i "{mp3}" -map 0:v -map 1:a -c:v copy -c:a aac -shortest "{out_path}" -y'
        subprocess.run(cmd, shell=True, check=True)
        shutil.rmtree(tmp_folder, ignore_errors=True)


def _save_ai_image(url: str, tmp_folder: str) -> str:
    # 使用 datetime 获取当前时间并格式化
    image_path = f'{tmp_folder}/{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.png'

    # 最多重试3次下载图片
    max_retries = 3
    for retry in range(max_retries):
        try:
            with requests.Session() as session:
                session.trust_env = False
                response = session.get(url)
                response.raise_for_status()  # 检查响应状态
                image_data = response.content

                # 检查图片数据是否有效
                try:
                    Image.open(io.BytesIO(image_data))
                except:
                    raise Exception("无效的图片数据")

                # 保存图片文件
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                return image_path

        except Exception as e:
            print(f'第{retry+1}次下载图片失败: {e}')
            if retry == max_retries - 1:
                return None
            time.sleep(1)  # 失败后等待1秒再重试

    return None
