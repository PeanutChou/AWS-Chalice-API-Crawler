from chalicelib.components import do_transaction_pg
from chalicelib.components import setting
import pandas as pd
import requests
import datetime
import pytz
import json

tz = pytz.timezone('Asia/Taipei')

def get_community_info():
    sql = '''SELECT jsonb_build_object(\
        'type',     'FeatureCollection',\
        'features', jsonb_agg(features.feature)\
        ) FROM (\
        SELECT jsonb_build_object(\
            'type',       'Feature',\
            'id',         serial_no,\
            'geometry',   ST_AsGeoJSON(geom)::jsonb,\
            'properties', to_jsonb(inputs) - 'geom'\
        ) AS feature\
    FROM (SELECT serial_no, commu_no, name, device_no, district, lat, lon, warning_status, geom, x_mean, x_max, x_min, y_mean, y_max, y_min FROM community.community_info where api_status = true) inputs ) features ;'''
    result = do_transaction_pg.get_dict_data_from_database(setting.config_db, sql_string=sql)[0]["jsonb_build_object"]
    return json.dumps(result, ensure_ascii=False)

def get_community_detail():
    sql = '''SELECT jsonb_build_object(\
            'type',     'FeatureCollection',\
            'features', jsonb_agg(features.feature)\
            ) FROM (\
            SELECT jsonb_build_object(\
                'type',       'Feature',\
                'id',         serial_no,\
                'geometry',   ST_AsGeoJSON(geom)::jsonb,\
                'properties', to_jsonb(inputs) - 'geom'\
            ) AS feature\
        FROM (SELECT * FROM community.community_info where api_status = true) inputs ) features ;'''
    result = do_transaction_pg.get_dict_data_from_database(setting.config_db, sql_string=sql)[0]["jsonb_build_object"]
    return json.dumps(result, ensure_ascii=False)

def crawl_community_data():
    query_sql = "SELECT * FROM community.community_info;"
    last_community_info = pd.DataFrame(do_transaction_pg.get_dict_data_from_database(setting.config_db, sql_string=query_sql))
    sql = ""
    for idx, row in last_community_info.iterrows():
        try:
            if row["api_status"]: last_api_status = 'true'
            else: last_api_status = 'false'
            if row["alive_3h"]: alive_3h = 'true'
            else: alive_3h = 'false'
            sql += f'''UPDATE community.community_info SET last_api_status = '{last_api_status}', last_alive_3h = '{alive_3h}', last_warning_status = '{json.dumps(row["warning_status"], ensure_ascii=False)}' WHERE device_no = '{row["device_no"]}';'''
            data = requests.get("http://210.242.161.205/ntpcom/Hillside.aspx?StnId="+str(row["device_no"])).text
            if data == "":
                sql += f'''UPDATE community.community_info SET api_status = false, api_status_note = '資料斷線' WHERE device_no = '{row["device_no"]}';'''
            else:
                data = json.loads(data)
                obs_time = datetime.datetime.strptime(data[0]["time"], "%Y-%m-%dT%H:%M:%S")
                timelag = datetime.datetime.now().replace(tzinfo=pytz.UTC) - obs_time.replace(tzinfo=tz)
                # 平台展示用(7天以上乾脆不顯示在平台了)
                if timelag < datetime.timedelta(days = 7):
                    api_status = 'true'
                    api_string = '資料正常'
                    timelag_string = ''
                else:
                    api_status = 'false'
                    api_string = '資料斷線'
                    timelag_string = f'：{timelag}'
                # 數據斷線用(超過3小時視為斷線)
                if timelag < datetime.timedelta(hours = 3):
                    alive_3h = 'true'
                else:
                    alive_3h = 'false'

                sql += f'''UPDATE community.community_info SET api_status = {api_status}, alive_3h = {alive_3h}, last_record_time = '{obs_time.strftime("%Y-%m-%dT%H:%M:%S")}', api_status_note = '最新一筆資料時間：{obs_time.strftime("%Y-%m-%dT%H:%M:%S")}；{api_string}{timelag_string}' WHERE device_no = '{row["device_no"]}';'''
                res = requests.get(f'''http://210.242.161.205/ntpcom/Hillside.aspx?StnId={row["device_no"]}''').text
                if res != '[]':
                    data = pd.read_json(res)[0:18]
                    x_filtered = data[ (data['incline_X'] - row['x_mean'] >= row['x_max']) | (data['incline_X'] - row['x_mean'] <= row['x_min']) ]
                    y_filtered = data[ (data['incline_Y'] - row['y_mean'] >= row['y_max']) | (data['incline_Y'] - row['y_mean'] <= row['y_min']) ]
                    x_zero = data[ data['incline_X'] == 0 ]
                    y_zero = data[ data['incline_Y'] == 0 ]
                    this_warning = {}
                    if len(x_filtered) == 18:
                        this_warning.update({"x":"異常"})
                    else:
                        this_warning.update({"x":"正常"})
                    if len(y_filtered) == 18:
                        this_warning.update({"y":"異常"})
                    else:
                        this_warning.update({"y":"正常"})
                    sql += "UPDATE community.community_info SET warning_status = '"+ json.dumps(this_warning, ensure_ascii=False) +"' where device_no = '" + str(row["device_no"]) + "';"
        except Exception as e:
            print(e)
    do_transaction_pg.do_transaction_command_manage(setting.config_db, sql_string=sql, return_serial=False)

def internal_notify_check():
    now_time = datetime.datetime.now().replace(tzinfo=tz)
    query_sql = "SELECT * FROM community.community_info;"
    last_community_info = pd.DataFrame(do_transaction_pg.get_dict_data_from_database(setting.config_db, sql_string=query_sql))
    last_community_info = last_community_info[last_community_info["api_status"]]
    result = ""
    for idx, row in last_community_info.iterrows():
        if row["last_alive_3h"] == row["alive_3h"]:
            result += ""
            log = "===狀態未改變==="
        else:
            if row["alive_3h"]:
                result += f'''\n🟢 {row["name"]}({row["device_no"]}) 監測已恢復。'''
                log = "===!!狀態改變，恢復上線並推播==="
            else:
                result += f'''\n⚠️ {row["name"]}({row["device_no"]}) 已斷線超過3H，請查看設備監測情形。'''
                log = "===!!狀態改變，有斷線設備並推播==="
        print(log, result)
    return result

def criteria_notify_check():
    now_time = datetime.datetime.now().replace(tzinfo=tz)
    query_sql = "SELECT * FROM community.community_info;"
    last_community_info = pd.DataFrame(do_transaction_pg.get_dict_data_from_database(setting.config_db, sql_string=query_sql))
    last_community_info = last_community_info[last_community_info["api_status"]]
    result = ""
    for idx, row in last_community_info.iterrows():
        if row["last_warning_status"] == row["warning_status"]:
            result += ""
            log = "===狀態未改變==="
        else:
            if row["warning_status"] == {"x": "正常","y": "正常"}:
                result += f'''\n🟢 {row["name"]}({row["device_no"]}) 監測數據已恢復正常。'''
                log = "===!!狀態改變，恢復上線並推播==="
            else:
                result += f'''\n⚠️ {row["name"]}({row["device_no"]}) 監測數據異常，請協助檢查。'''
                log = "===!!狀態改變，有監測異常並推播==="
        print(log, result)
    return result