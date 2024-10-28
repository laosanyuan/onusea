import subprocess
import cv2
import os
import shutil
import random
from pydub import AudioSegment
import requests
from datetime import datetime


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


def merge_transition_videos(video_files: list[str], out_path: str) -> None:
    """直接拼接多个视频"""

    tmp_folder = 'merge_folder'
    os.makedirs(tmp_folder, exist_ok=True)

    try:
        video_list_file = f'{tmp_folder}/video_list.txt'
        with open(video_list_file, 'w') as f:
            for video_file in video_files:
                video_file = os.path.relpath(video_file, start=tmp_folder)
                f.write(f"file '{video_file}'\n")

        cmd = f'ffmpeg -f concat -safe 0 -i "{video_list_file}" -c copy -y "{out_path}"'
        subprocess.run(cmd, shell=True, check=True)

    finally:
        shutil.rmtree(tmp_folder, ignore_errors=True)


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


def splicing_video(images: list[str], output_path: str):
    """拼接图片为视频"""

    tmp_folder = 'tmp_splicing_folder'
    if os.path.exists(tmp_folder):
        shutil.rmtree(tmp_folder)
    os.makedirs(tmp_folder, exist_ok=True)

    try:
        image_list_file = f'{tmp_folder}/image_list.txt'
        with open(image_list_file, 'w') as f:
            for image in images:
                tmp_image = _save_ai_image(image, tmp_folder)
                tmp_image = os.path.basename(tmp_image)
                f.write(f"file '{tmp_image}'\n")
                f.write("duration 0.6\n")
        cmd = f'ffmpeg -f concat -safe 0 -i "{image_list_file}" -vf "setpts=PTS-STARTPTS" -pix_fmt yuv420p -c:v libx264 -preset slow -crf 22 -r 30 "{output_path}" -y'
        subprocess.run(cmd, shell=True, check=True)
    finally:
        shutil.rmtree(tmp_folder, ignore_errors=True)


def _save_ai_image(url: str, tmp_folder: str) -> str:
    # 使用 datetime 获取当前时间并格式化
    image_path = f'{tmp_folder}/{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.png'
    # 保存图片文件, 代理原因必须提前保存文件
    try:
        with requests.Session() as session:
            session.trust_env = False
            image_data = session.get(url).content
            with open(image_path, 'wb') as f:
                f.write(image_data)
    except Exception as e:
        print(f'保存图片失败: {e}')
        return None

    return image_path
