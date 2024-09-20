import subprocess

def get_duration(file_path: str) -> float:
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