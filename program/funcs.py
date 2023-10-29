import logging 

from datetime import datetime, timedelta

def initiate_logger(file):
    logger = logging.getLogger(__name__)
    logging.getLogger().setLevel(logging.DEBUG)

    handler = logging.FileHandler(file)
    file_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    file_handler.setFormatter(formatter)
    handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(handler)

    return logger

def format_price(curr_num, match_num):

    curr_num_str = f'{curr_num}'
    match_num_str = f'{match_num}'

    if '.' in match_num_str:
        match_dec = len(match_num_str.split('.')[1])
        curr_num_str = f'{curr_num:.{match_dec}f}' 
        curr_num_str = curr_num_str[:]   
        return curr_num_str

    else:
        return f'{int(curr_num)}'

def format_time(timestamp):
    return timestamp.replace(microsecond=0).isoformat()

def get_iso():

    # Get timestamp
    date_start_0 = datetime.now()
    date_start_1 = date_start_0 - timedelta(hours=100)
    date_start_2 = date_start_1 - timedelta(hours=100)
    date_start_3 = date_start_2 - timedelta(hours=100)
    date_start_4 = date_start_3 - timedelta(hours=100)

    # Format datetime
    times_dict = {
        'range1': {
            'from_iso': format_time(date_start_1),
            'to_iso': format_time(date_start_0)
        },
        'range2': {
            'from_iso': format_time(date_start_2),
            'to_iso': format_time(date_start_1)
        },
        'range3': {
            'from_iso': format_time(date_start_3),
            'to_iso': format_time(date_start_2)
        },
        'range4': {
            'from_iso': format_time(date_start_4),
            'to_iso': format_time(date_start_3)
        }
    }

    return times_dict

