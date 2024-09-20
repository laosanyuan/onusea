import shutil
import os
import unittest
from unittest.mock import patch

from season_generator.video_winter_generator import VideoWinterGenerator


class TestVideoWinterGenerator(unittest.TestCase):

    def setUp(self):
        self._tmp_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp_folder')
        os.makedirs(self._tmp_folder, exist_ok=True)
        self._tmp_image = os.path.join(self._tmp_folder, 'tmp_image.jpg')
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../resources/test_image.jpg'), self._tmp_image)

    @patch('season_generator.video_winter_generator.VideoWinterGenerator._save_ai_image')
    def test_generate(self, mock_save_ai_image):
        mock_save_ai_image.return_value = self._tmp_image
        generator = VideoWinterGenerator()
        result = generator.generate('http://example.com/image', os.path.join(self._tmp_folder, 'output_video.mp4'))
        self.assertTrue(result)

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp_folder, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
