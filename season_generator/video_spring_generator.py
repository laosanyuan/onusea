import subprocess
import os

from .base_season_generator import BaseSeasonGenerator


class VideoSpringGenerator(BaseSeasonGenerator):

    def generate(self, url: str, output_path: str, duration: float = 4) -> bool:
        ai_image = self._save_ai_image(url)
        if not ai_image or not os.path.exists(ai_image):
            return False
        
        try:
            cmd = f'ffmpeg -loop 1 -i "{ai_image}" -t {duration} -y "{output_path}" -reset_timestamps 1'
            subprocess.run(cmd, shell=True, check=True)
        finally:
            if os.path.exists(ai_image):
                os.remove(ai_image)

        return os.path.exists(output_path)
