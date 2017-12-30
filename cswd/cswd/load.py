import pandas as pd
import pkg_resources

def load_csv(csv_name, sub_dir_name = None, kwargs = {}):
    """读取单个文件"""
    path_ = csv_name if sub_dir_name is None else '{}/{}'.format(sub_dir_name, csv_name)
    full_path = 'resources/{}'.format(path_)
    file_name = pkg_resources.resource_filename(__name__, full_path)
    return pd.read_csv(file_name, **kwargs)