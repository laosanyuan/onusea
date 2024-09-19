from abc import ABC, abstractmethod
import time

import requests


class BaseSeasonGenerator(ABC):
    @abstractmethod
    def generate(self, url: str, output_path: str, duration: float = 2.5) -> bool:
        pass

    def _save_ai_image(self, url: str) -> str:
        image_path = f'{time.strftime("%Y%m%d_%H%M%S")}.png'
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
