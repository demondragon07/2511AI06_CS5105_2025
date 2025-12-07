import logging
import sys

TIMETABLE_FILE = 'in_timetable'
ROOM_CAPACITY_FILE = 'in_room_capacity'
COURSE_ROLL_MAPPING_FILE = 'in_course_roll_mapping'
ROLL_NAME_MAPPING_FILE = 'in_roll_name_mapping'

OUTPUT_ARRANGEMENT_FILE = 'op_overall_seating_arrangement.xlsx'
OUTPUT_SEATS_LEFT_FILE = 'op_seats_left.xlsx'
ERROR_LOG_FILE = 'errors.txt'

def setup_logging():
    """Configures the logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(ERROR_LOG_FILE, mode='w'), 
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Separate handler for errors.txt to only log ERROR level
    error_file_handler = logging.FileHandler(ERROR_LOG_FILE, mode='w')
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger('').addHandler(error_file_handler)