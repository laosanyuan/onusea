import subprocess
import os
import random

from season_generator.base_season_generator import BaseSeasonGenerator
from utils.image_utils import get_image_size
from utils.video_utils import get_duration


class VideoSpringGenerator(BaseSeasonGenerator):

    def generate(self, url: str, output_path: str, duration: float = 4) -> bool:
        ai_image = self._save_ai_image(url)
        if not ai_image or not os.path.exists(ai_image):
            return False

        try:
            width, height = get_image_size(ai_image)
            rain_file = './resources/decorations/rain.mp4'
            snow_duration = get_duration(rain_file)
            start_time = random.uniform(0,snow_duration - duration)

            cmd = f'ffmpeg -loop 1 -i "{ai_image}" -i "{rain_file}" -ss {start_time} -filter_complex "\
                [1:v]scale=-1:{height},crop={width}:{height},split=2[mask1][mask2];\
                [mask1][mask2]alphamerge,format=rgba,colorchannelmixer=1:1:1:0:1:1:1:0:1:1:1:0:0:0:0:1.5[mask];\
                [0:v][mask]overlay;\
                " -an -t {duration} -y "{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
        finally:
            if os.path.exists(ai_image):
                os.remove(ai_image)

        return os.path.exists(output_path)
