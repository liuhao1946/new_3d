import os
import json

def config_file_check(file_path='config.json'):
    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 如果文件不存在，创建并写入默认值
        default_config = {
            "ser_baud": [
                2000000,
                921600,
                1000000,
                1152000,
                115200,
                941176,
                9600
            ],
            "refresh_rate": 1,
            "euler_own_cal": False,
            "get_cal_state_en": True,
            "display_angle_ref": False
        }
        with open(file_path, 'w') as config_file:
            json.dump(default_config, config_file, indent=4)
        print(f"Created default config file at {file_path}")
    else:
        print(f"Config file {file_path} already exists.")
