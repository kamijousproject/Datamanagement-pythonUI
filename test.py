import subprocess
import requests
import json
import glob
import os
import time
from datetime import datetime

SITE_CODE = "30044144"
SITE_NAME = "WITCORP PRODUCTS CO., LTD."
USERNAME = "gaiasolardev"
PASSWORD = "Passwordsolardev"


def run_all_devices():
    subprocess.run(["python", "emi.py"], check=True)
    subprocess.run(["python", "edmi.py"], check=True)
    subprocess.run(["python", "logger.py"], check=True)
    subprocess.run(["python", "pq_meter.py"], check=True)
    subprocess.run(["python", "inverter.py"], check=True)


def login():
    url = "https://gaia.pttdigital.com/authen-api/login"
    response = requests.post(
        url, json={"username": USERNAME, "password": PASSWORD})
    response.raise_for_status()
    return response.json()["access_token"]


def send_api(endpoint, token, payload):
    url = f"https://gaia.pttdigital.com/{endpoint}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=payload)

    # สร้าง log ใหม่ทุกครั้งที่รัน active_device.py
    if not hasattr(send_api, "log_filename"):
        send_api.log_filename = f"api_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    log_folder = "logs"
    os.makedirs(log_folder, exist_ok=True)
    log_file = os.path.join(log_folder, send_api.log_filename)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{endpoint}]\n")
        f.write(f"Status Code: {response.status_code}\n")
        f.write(
            f"Request Payload: {json.dumps(payload, ensure_ascii=False)}\n")
        f.write(f"Response: {response.text}\n")
        f.write(f"{'-'*60}\n")

    # print(f"[{endpoint}] -> {response.status_code} {response.text}")


def parse_txt(path):
    result = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                key, val = map(str.strip, line.split(":", 1))
                if val.lower() == "no data":
                    continue
                try:
                    val = float(val)
                except:
                    pass
                result[key] = val
    return result


def send_all_data(token):
    folder_map = {
        "emi": "receive-data-solar-information",
        "edmi": "receive-data-solar-revenuemeter",
        "inverter": "receive-data-solar-inverter",
        "pq_meter": "receive-data-solar-pq-meter",
        "smartlogger": "receive-data-solar-smartlogger"
    }

    for folder, endpoint in folder_map.items():
        files = sorted(glob.glob(f"{folder}/*.txt"), reverse=True)
        if not files:
            continue
        latest_file = files[0]

        if folder == "inverter":
            inverter_blocks = {}
            current_key = None
            with open(latest_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("inverter_"):
                        current_key = line
                        inverter_blocks[current_key] = {}
                    elif ":" in line and current_key:
                        key, val = map(str.strip, line.split(":", 1))
                        if val.lower() == "no data":
                            continue
                        try:
                            val = float(val)
                        except:
                            pass
                        inverter_blocks[current_key][key] = val

            for name, number in [("Inverter 1", 1), ("Inverter 2", 2), ("Inverter 3", 3)]:
                inv_key = f"inverter_{number}"
                inv_data = inverter_blocks.get(inv_key, {})
                inv_payload = {
                    "site_code": SITE_CODE,
                    "site_name": SITE_NAME,
                    "inverter_name": name,
                    "inverter_number": number,
                    "inverter_status": inv_data.get("32000", 0),
                    "energy_today": inv_data.get("32106", 0) / 1000,
                    "kwh_energy_product": inv_data.get("32114", 0) / 1000,
                    "ac_voltage_phase_a": inv_data.get("32016", 0),
                    "ac_voltage_phase_b": inv_data.get("32018", 0),
                    "ac_voltage_phase_c": inv_data.get("32020", 0),
                    "ac_current_phase_a": inv_data.get("32017", 0),
                    "ac_current_phase_b": inv_data.get("32019", 0),
                    "ac_current_phase_c": inv_data.get("32021", 0),
                    "total_dc_voltage": inv_data.get("32084", 0),
                    "total_dc_current": inv_data.get("32082", 0),
                    "total_dc_power": inv_data.get("32080", 0),
                    "active_power": inv_data.get("32085", 0),
                    "reactive_power": inv_data.get("32087", 0),
                    "apparent_power": inv_data.get("32089", 0),
                    "power_factor": inv_data.get("32025", 0),
                    "grid_frequency": 50,
                    "internal_temp": inv_data.get("32021", 0),

                    # Explicit PV mapping
                    "pv1_current": inv_data.get("32017", 0),
                    "pv1_voltage": inv_data.get("32016", 0),
                    "pv2_current": inv_data.get("32019", 0),
                    "pv2_voltage": inv_data.get("32018", 0),
                    "pv3_current": inv_data.get("32021", 0),
                    "pv3_voltage": inv_data.get("32020", 0),
                    "pv4_current": inv_data.get("32023", 0),
                    "pv4_voltage": inv_data.get("32022", 0),
                    "pv5_current": inv_data.get("32025", 0),
                    "pv5_voltage": inv_data.get("32024", 0),
                    "pv6_current": inv_data.get("32027", 0),
                    "pv6_voltage": inv_data.get("32026", 0),
                    "pv7_current": inv_data.get("32029", 0),
                    "pv7_voltage": inv_data.get("32028", 0),
                    "pv8_current": inv_data.get("32031", 0),
                    "pv8_voltage": inv_data.get("32030", 0),
                    "pv9_current": inv_data.get("32033", 0),
                    "pv9_voltage": inv_data.get("32032", 0),
                    "pv10_current": inv_data.get("32035", 0),
                    "pv10_voltage": inv_data.get("32034", 0),
                    "pv11_current": inv_data.get("32037", 0),
                    "pv11_voltage": inv_data.get("32036", 0),
                    "pv12_current": inv_data.get("32039", 0),
                    "pv12_voltage": inv_data.get("32038", 0),
                    "pv13_current": inv_data.get("32041", 0),
                    "pv13_voltage": inv_data.get("32040", 0),
                    "pv14_current": inv_data.get("32043", 0),
                    "pv14_voltage": inv_data.get("32042", 0),
                    "pv15_current": inv_data.get("32045", 0),
                    "pv15_voltage": inv_data.get("32044", 0),
                    "pv16_current": inv_data.get("32047", 0),
                    "pv16_voltage": inv_data.get("32046", 0),
                    "pv17_current": inv_data.get("32049", 0),
                    "pv17_voltage": inv_data.get("32048", 0),
                    "pv18_current": inv_data.get("32051", 0),
                    "pv18_voltage": inv_data.get("32050", 0),
                    "pv19_current": inv_data.get("32053", 0),
                    "pv19_voltage": inv_data.get("32052", 0),
                    "pv20_current": inv_data.get("32055", 0),
                    "pv20_voltage": inv_data.get("32054", 0)
                }

                send_api(endpoint, token, inv_payload)

        else:
            data = parse_txt(latest_file)
            payload = {
                "site_code": SITE_CODE,
                "site_name": SITE_NAME,
            }

            if folder == "emi":
                payload["information_name"] = "Weather"
                payload["information_number"] = 1
                payload["adam_irradiance"] = data.get("40033", 0)
                payload["module_temperature"] = data.get("40034", 0)
                payload["ambient_temperature"] = data.get("40031", 0)
                payload["wind_sensor"] = data.get("40035", 0)

            elif folder == "edmi":
                payload.update({
                    "revenue_name": "EDMI",
                    "revenue_number": 1,
                    "revenue_meter_check_lcd": data.get("revenue_meter_check_lcd", "good"),
                    "revenue_meter_current_date": data.get("revenue_meter_current_date", 0),
                    "revenue_meter_current_time": data.get("revenue_meter_current_time", 0),
                    "revenue_meter_date_to_reset_meter": data.get("revenue_meter_date_to_reset_meter", 0),
                    "revenue_meter_counting_reset": data.get("revenue_meter_counting_reset", 0),

                    # "revenue_meter_111_billing_total_wh_total": data.get("revenue_meter_111_billing_total_wh_total", 0),
                    "revenue_meter_111_billing_total_wh_total": (
                        data.get("revenue_meter_010_billing_total_wh_rate_a", 0) +
                        data.get("revenue_meter_020_billing_total_wh_rate_b", 0) +
                        data.get("revenue_meter_030_billing_total_wh_rate_c", 0)
                    ),
                    "revenue_meter_010_billing_total_wh_rate_a": data.get("revenue_meter_010_billing_total_wh_rate_a", 0),
                    "revenue_meter_020_billing_total_wh_rate_b": data.get("revenue_meter_020_billing_total_wh_rate_b", 0),
                    "revenue_meter_030_billing_total_wh_rate_c": data.get("revenue_meter_030_billing_total_wh_rate_c", 0),

                    "revenue_meter_050_previous_w_demand_rate_a": data.get("revenue_meter_050_previous_w_demand_rate_a", 0),
                    "revenue_meter_060_previous_w_demand_rate_b": data.get("revenue_meter_060_previous_w_demand_rate_b", 0),
                    "revenue_meter_070_previous_w_demand_rate_c": data.get("revenue_meter_070_previous_w_demand_rate_c", 0),

                    "revenue_meter_015_cumul_w_demand_rate_a": data.get("revenue_meter_015_cumul_w_demand_rate_a", 0),
                    "revenue_meter_016_cumul_w_demand_rate_b": data.get("revenue_meter_016_cumul_w_demand_rate_b", 0),
                    "revenue_meter_017_cumul_w_demand_rate_c": data.get("revenue_meter_017_cumul_w_demand_rate_c", 0),

                    "revenue_meter_050t_previous_time_of_w_demand_a": data.get("revenue_meter_050t_previous_time_of_w_deman", 0),
                    "revenue_meter_060t_previous_time_of_w_demand_b": data.get("revenue_meter_060t_previous_time_of_w_deman", 0),
                    "revenue_meter_070t_previous_time_of_w_demand_c": data.get("revenue_meter_070t_previous_time_of_w_deman", 0),

                    "revenue_meter_222_billing_total_varh_total": data.get("revenue_meter_222_billing_total_varh_total", 0),
                    "revenue_meter_280_previous_var_demand_total": data.get("revenue_meter_280_previous_var_demand_total", 0),
                    "revenue_meter_280t_previous_time_of_var_demand": data.get("revenue_meter_280t_previous_time_of_var_dem", 0),
                    "revenue_meter_118_cumul_var_demand_total": data.get("revenue_meter_118_cumul_var_demand_total", 0),

                    # "revenue_meter_000_total_energy": data.get("revenue_meter_000_total_energy", 0),
                    "revenue_meter_000_total_energy": (
                        data.get("revenue_meter_001_total_energy_rate_a", 0) +
                        data.get("revenue_meter_002_total_energy_rate_b", 0) +
                        data.get("revenue_meter_003_total_energy_rate_c", 0)
                    ),
                    "revenue_meter_001_total_energy_rate_a": data.get("revenue_meter_001_total_energy_rate_a", 0),
                    "revenue_meter_002_total_energy_rate_b": data.get("revenue_meter_002_total_energy_rate_b", 0),
                    "revenue_meter_003_total_energy_rate_c": data.get("revenue_meter_003_total_energy_rate_c", 0),
                    "revenue_meter_cur_total_energy": data.get("revenue_meter_cur_total_energy", 0),
                    "revenue_meter_cur_total_energy_rate_a": data.get("revenue_meter_cur_total_energy_rate_a", 0),
                    "revenue_meter_cur_total_energy_rate_b": data.get("revenue_meter_cur_total_energy_rate_b", 0),
                    "revenue_meter_cur_total_energy_rate_c": data.get("revenue_meter_cur_total_energy_rate_c", 0),
                    "revenue_meter_093_inst_power": data.get("revenue_meter_093_inst_power", 0)
                })

            elif folder == "pq_meter":
                payload.update({
                    "pq_meter_name": "PQ1",
                    "pq_meter_number": 1,
                    "pq_metercurrent_phase_a": data.get("32272", 0),
                    "pq_metercurrent_phase_b": data.get("32274", 0),
                    "pq_metercurrent_phase_c": data.get("32276", 0),
                    "pq_metercurrent_3-phase_average": data.get("AVG_Current", 0),
                    "pq_metervoltage_a-b": data.get("32266", 0),
                    "pq_metervoltage_b-c": data.get("32268", 0),
                    "pq_metervoltage_c-a": data.get("32270", 0),
                    "pq_metervoltage_l-l_average": data.get("AVG_Voltage", 0),
                    "pq_meterpower_factor": data.get("32284", 0),
                    "pq_meteractive_energy": data.get("32341", 0),
                    "pq_meterreactive_energy": data.get("32345", 0),
                    "pq_meterapparent_energy": 0,
                    "pq_meteractive_power": data.get("32278", 0),
                    "pq_meterreactive_power": data.get("32280", 0),
                    "pq_meterapparent_power": data.get("32287", 0),
                    "pq_meterfrequency": data.get("Frequency", 0),
                    "pq_meterthdi": data.get("HARD_1", 0),
                    "pq_meterthdv": data.get("HARD_2", 0)
                })

            elif folder == "smartlogger":
                payload.update({
                    "smartlogger_number": 1,
                    "smartlogger_plant_status": data.get("40566", 0),
                    "smartlogger_co2_reduction": data.get("40550", 0),
                    "smartlogger_co2_emission_reduction_coefficient": data.get("41124", 0) / 1000,
                    "smartlogger_e-total": data.get("40560", 0) / 100,
                    "smartlogger_e-daily": data.get("40562", 0) / 100,
                    "smartlogger_duration_of_daily_power_generation": data.get("40564", 0) / 10,
                    "smartlogger_active_alarm_sequence_number": data.get("40568", 0),
                    "smartlogger_historical_alarm_sequence_number": data.get("40570", 0),
                    "smartlogger_ac_voltage_phase_a": data.get("40575", 0) / 10,
                    "smartlogger_ac_voltage_phase_b": data.get("40576", 0) / 10,
                    "smartlogger_ac_voltage_phase_c": data.get("40577", 0) / 10,
                    "smartlogger_ac_current_phase_a": data.get("40572", 0),
                    "smartlogger_ac_current_phase_b": data.get("40573", 0),
                    "smartlogger_ac_current_phase_c": data.get("40574", 0),
                    "smartlogger_inverter_efficiency": data.get("40588", 98.2)
                    # "smartlogger_inverter_status": data.get("40685", 0)
                })

            send_api(endpoint, token, payload)


if __name__ == "__main__":
    while True:
        try:
            run_all_devices()
            token = login()

            # ตั้งชื่อไฟล์ log ใหม่ทุกครั้งก่อนส่ง API
            send_api.log_filename = f"api_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            send_all_data(token)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)
