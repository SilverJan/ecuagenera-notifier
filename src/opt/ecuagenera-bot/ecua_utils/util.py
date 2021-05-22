import datetime
import os
import yaml


def reload_config_yml() -> dict:
    global config
    config = {}
    config_file_path = f'{os.path.dirname(os.path.realpath(__file__))}/../config.yml'
    if not os.path.isfile(config_file_path):
        raise Exception("Please create config.yml first")
    with open(config_file_path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config


# Converts custom format date (16/Jan/2021) and time (10:20 - 12:00) to datetime
def convert_to_date_time(date_str: str, time_str: str) -> datetime:
    # take only start time for date_time creation
    time_str = time_str.split(' ')[0]
    try:
        return datetime.datetime.strptime(f'{date_str} | {time_str}', '%d/%b/%Y | %H:%M')
    except ValueError:
        return datetime.datetime.strptime(f'{date_str} | {time_str}', '%d/%m/%Y | %H:%M')


# Converts AM/PM time (10:10 AM) to 24h format (10:10)
def convert_12_to_24(time_str) -> str:
    if "PM" in time_str or "AM" in time_str:
        return datetime.datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
    else:
        print(f"Time can't be converted: {time_str}")
        return time_str


def get_count_of_nested_dict(dict: dict) -> int:
    count = 0
    for _, v in dict.items():
        if isinstance(v, type(dict)):
            count += get_count_of_nested_dict(v)
        else:
            count += 1
    return count


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
