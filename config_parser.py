import json
import os


class Config:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = self.load_config()

    @property
    def coze_token(self) -> str:
        return self._config.get('coze_token', '')

    @property
    def coze_flow_id(self) -> str:
        return self._config.get('coze_flow_id', '')

    @property
    def coze_robot_id(self) -> str:
        return self._config.get('coze_robot_id', '')

    @property
    def output_folder(self) -> str:
        return self._config.get('output_folder', '')

    @property
    def generate_count(self) -> int:
        return self._config.get('generate_count', 10)

    def load_config(self) -> dict:
        """读取配置文件"""

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config


config = Config('configs/config.json')
