import subprocess
import os
import random

from .base_season_generator import BaseSeasonGenerator
from utils.image_utils import get_image_size
from utils.video_utils import get_duration


class VideoSummerGenerator(BaseSeasonGenerator):

    def generate(self, url: str, output_path: str, duration: float = 5) -> bool:
        ai_image = self._save_ai_image(url)
        if not ai_image or not os.path.exists(ai_image):
            return False
        
        try:
            width, height = get_image_size(ai_image)
            flowers_file = './resources/decorations/flowers.mp4'
            flowers_duration = get_duration(flowers_file)
            start_time = random.uniform(0,flowers_duration - duration)
            
            cmd = f'ffmpeg -loop 1 -i "{ai_image}" -i "{flowers_file}" -ss {start_time} -filter_complex "\
                [1:v]scale={width}:{height/2},chromakey=green:0.1:0.2[flowers];\
                [0:v]format=yuv420p,setpts=N/FRAME_RATE/TB[main];\
                [main][flowers]overlay=0:{height/2};\
                " -an -t {duration} -y "{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
        finally:
            if os.path.exists(ai_image):
                os.remove(ai_image)

        return os.path.exists(output_path)
