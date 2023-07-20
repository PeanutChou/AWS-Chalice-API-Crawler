from chalice import Chalice
from chalice import CORSConfig
from chalicelib.utils import utils_common
from chalicelib.components import setting

import traceback
import json
import requests
import datetime

app_name='NTPC-HillsideCommunity'
app = Chalice(app_name=app_name)

cors_config = CORSConfig(
    allow_origin='*',
    allow_headers=['X-Special-Header'],
    max_age=600,
    expose_headers=['X-Special-Header'],
    allow_credentials=True
)

@app.route('/info', methods=['GET'], cors=cors_config)
def community_info():
    return utils_common.get_community_info()

@app.route('/detail', methods=['GET'], cors=cors_config)
def community_detail():
    return utils_common.get_community_detail()

notify_url = "https://notify-api.line.me/api/notify"

@app.schedule('cron(2/10 * * * ? *)')
def check_internal_alert(event):
    this_str = utils_common.internal_notify_check()
    if this_str != "":
        data = {"message":this_str}
        notify_header = {"Authorization":"Bearer " + setting.config_notify_token["internal_notify_token"]}
        try:
            requests.post(notify_url, headers = notify_header, data=data)
        except Exception as e:
            print(e)
            print(traceback.format_exc())

@app.schedule('cron(2/10 * * * ? *)')
def check_criteria_alert(event):
    this_str = utils_common.criteria_notify_check()
    if this_str != "":
        data = {"message":this_str}
        notify_header = {"Authorization":"Bearer " + setting.config_notify_token["internal_notify_token"]}
        try:
            requests.post(notify_url, headers = notify_header, data=data)
        except Exception as e:
            print(e)
            print(traceback.format_exc())

        data = {"message":this_str}
        notify_header = {"Authorization":"Bearer " + setting.config_notify_token["alert_notify_token"]}
        try:
            requests.post(notify_url, headers = notify_header, data=data)
        except Exception as e:
            print(e)
            print(traceback.format_exc())

@app.schedule('cron(0/10 * * * ? *)')
def every_crawl(event):
    utils_common.crawl_community_data()