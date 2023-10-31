import logging 

from datetime import datetime, timedelta

def initiate_logger(file):

    '''
    Initiates logging.

    :param file: name of log file to initiate
    :return logger: logger object
    '''

    # Get or create logger
    logger = logging.getLogger(file)

    if not logger.hasHandlers():
        # Set log level
        logging.getLogger().setLevel(logging.DEBUG)

        # Set handlers
        file_handler = logging.FileHandler(file)
        stream_handler = logging.StreamHandler()

        # Set formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Apply formatter
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
    

def format_number(curr_num, match_num):

    '''
    Format price to match tickSize of market pair.

    :param curr_num: quantity of market pair to trade
    :param match_num: tickSize of market pair
    '''

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

    '''
    Format timestmap to ISO

    :param timestamp: datetime obejct to format
    :return: datetime in ISO format
    '''
    return timestamp.replace(microsecond=0).isoformat()

def get_iso():

    '''
    Creates a dict of time ranges for market prices

    :return times_dict: dict of time ranges in required format
    '''

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

