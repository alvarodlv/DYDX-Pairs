import logging 


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