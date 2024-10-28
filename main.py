import json
import requests
import shutil
import os
import time

from config_parser import config
from utils.video_utils import add_bgm, splicing_video, add_decoration


def get_ai_images(coze_token: str, coze_robot_id: str, flow_id: str, index: int, input_image: str = '') -> tuple[list[str], str, str]:
    images = []
    title = ''
    model_image = None

    url = 'https://api.coze.cn/v1/workflow/run'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {coze_token}'
    }
    payload = {
        'workflow_id': flow_id,
        'bot_id': coze_robot_id,
        'parameters': {
            'index': index,
            'model_image': input_image
        },
    }
    try:
        with requests.Session() as session:
            session.timeout = 900
            session.trust_env = False
            response = session.post(url, headers=headers, json=payload)
            response.raise_for_status()

            content = response.json()
            if 'data' in content:
                tmp_json = json.loads(content['data'])
                images.extend(tmp_json['images'])
                title = tmp_json['title']
                model_image = tmp_json['model_image']
            else:
                print(content['msg'])
    except requests.exceptions.RequestException as e:
        print(f'API调用失败: {e}')

    return (images, title, model_image)


if __name__ == '__main__':
    index = 0
    while (True):
        index += 1

        images = []
        title = ''
        try_times = 0
        input_image = ''
        while len(images) < 12:
            print(f"调用coze接口，尝试次数：{try_times+1}")
            tmp_images, title, model_image = get_ai_images(config.coze_token, config.coze_robot_id, config.coze_flow_id, len(images), input_image)
            tmp_images = [img for img in tmp_images if img.strip()]
            images.extend(tmp_images)
            if model_image:
                input_image = model_image
            try_times += 1
            if try_times > 10:
                raise ValueError('连续调用coze接口失败')

        tmp_folder = 'tmp_main_folder'
        os.makedirs(tmp_folder, exist_ok=True)
        # 合并图片
        tmp_splicing = f'{tmp_folder}/tmp_splicing.mp4'
        splicing_video(images, tmp_splicing)

        # 添加画面装饰
        tmp_decoration = f'{tmp_folder}/decoration.mp4'
        add_decoration(tmp_splicing, tmp_decoration)

        # 添加音频
        output = f'{config.output_folder}/{time.strftime("%Y%m%d_%H%M%S")}#{title}.mp4'
        add_bgm(tmp_decoration, output)
        print(f'生成成功：{output}')

        if os.path.exists(tmp_folder):
            shutil.rmtree(tmp_folder)

        if index >= config.generate_count:
            break
