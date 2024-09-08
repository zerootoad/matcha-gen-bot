import os
import json

class ConfigHandler:
    def __init__(self) -> None:
        current_dir = os.path.dirname(__file__)
        bot_dir = os.path.dirname(current_dir)

        self.cfgs_folder = os.path.join(bot_dir, 'assets', 'cfgs')
        self.default_cfg = os.path.join(bot_dir, 'assets', 'default.cfg')
        self.output_cfgs_folder = os.path.join(bot_dir, 'data', 'cfgs')
        
        if not os.path.exists(self.output_cfgs_folder):
            os.makedirs(self.output_cfgs_folder)

    def generate_cfg_file(self, file_name, prediction_x, prediction_y, smoothness, sensitivity):
        cfg_file = os.path.join(self.cfgs_folder, f'{file_name}.cfg')
        if not os.path.exists(cfg_file):
            cfg_file = self.default_cfg

        with open(cfg_file, 'r') as file:
            config_data = json.load(file)

        config_data['prediction'] = True
        config_data['prediction_x'] = float(prediction_x)
        config_data['prediction_y'] = float(prediction_y)
        
        if smoothness > 0:
            config_data['aimtype'] = 0
            config_data['smoothness_x'] = smoothness
            config_data['smoothness_y'] = smoothness
            config_data['smoothness'] = True
        else:
            config_data['smoothness_x'] = 1
            config_data['smoothness_y'] = 1
            config_data['smoothness'] = False
        
        config_data['sensitivity'] = sensitivity

        output_cfg_file = os.path.join(self.output_cfgs_folder, f'{file_name}.cfg')
        with open(output_cfg_file, 'w') as file:
            json.dump(config_data, file, separators=(',', ':'))

        return output_cfg_file
