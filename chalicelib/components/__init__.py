from chalicelib.components.configuration import get_config_setting
import os
import datetime

setting = get_config_setting()

def get_now_dt_string():
    dt_object       = datetime.datetime.now()
    datetime_string = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    return datetime_string
