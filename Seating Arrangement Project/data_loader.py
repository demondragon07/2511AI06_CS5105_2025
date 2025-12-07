# Used for loading data from the xlsx input file
import pandas as pd
import logging
from typing import List, Dict, Tuple
from data_models import Student, Room, Course
import utils

EXCEL_FILE = 'files/input_data_tt.xlsx'

def load_roll_name_mapping(sheet_name: str) -> Dict[str, str]:
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
        mapping = {}
        for _, row in df.iterrows():
            roll = str(row['Roll']).strip()
            name = str(row['Name']).strip()
            mapping[roll] = name
        return mapping
    except FileNotFoundError:
        logging.error(f"File not found: {sheet_name}")
        raise
    except Exception as e:
        logging.error(f"Error loading {sheet_name}: {e}")
        raise

def load_course_roll_mapping(sheet_name: str) -> Dict[str, List[str]]:
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
        mapping = {}
        for _, row in df.iterrows():
            course = str(row['course_code']).strip()
            roll = str(row['rollno']).strip()
            if course not in mapping:
                mapping[course] = []
            mapping[course].append(roll)
        return mapping
    except FileNotFoundError:
        logging.error(f"File not found: {sheet_name}")
        raise
    except Exception as e:
        logging.error(f"Error loading {sheet_name}: {e}")
        raise

def load_room_capacities(sheet_name: str) -> Dict[str, Room]:
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
        rooms = {}
        for _, row in df.iterrows():
            number = str(row['Room No.']).strip()
            capacity = int(row['Exam Capacity'])
            block = str(row['Block']).strip()
            rooms[number] = Room(number=number, capacity=capacity, block=block)
        logging.info(f"Loaded {len(rooms)} rooms.")
        return rooms
    except FileNotFoundError:
        logging.error(f"File not found: {sheet_name}")
        raise
    except Exception as e:
        logging.error(f"Error loading {sheet_name}: {e}")
        raise

def get_all_scheduled_slots(timetable_path: str) -> List[Tuple[str, str]]:
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=timetable_path)
        slots_to_process = []
        
        # Checks date format
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        for _, row in df.iterrows():
            date = str(row['Date'])
            
            if 'Morning' in df.columns:
                morning_courses = str(row['Morning']).strip()
                if morning_courses and morning_courses.upper() != "NO EXAM":
                    slots_to_process.append((date, 'Morning'))
            
            if 'Evening' in df.columns:
                evening_courses = str(row['Evening']).strip()
                if evening_courses and evening_courses.upper() != "NO EXAM":
                    slots_to_process.append((date, 'Evening'))
                    
        return slots_to_process
    except Exception as e:
        logging.error(f"Error reading schedule: {e}")
        raise

def get_courses_for_slot(
    timetable_path: str,
    course_roll_map: Dict[str, List[str]],
    roll_name_map: Dict[str, str],
    target_date: str,
    target_slot: str
) -> List[Course]:
    """Gets all courses and their student data for a specific date and slot."""
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=timetable_path)
        # Ensuring that date format matches
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        slot_row = df[df['Date'] == target_date]

        if slot_row.empty:
            logging.error(f"No timetable entry found for date: {target_date}")
            return []

        course_codes_str = slot_row.iloc[0][target_slot].strip()
        if course_codes_str.upper() == "NO EXAM":
            return []
        
        course_codes = [code.strip() for code in course_codes_str.split(';')]
        
        courses: List[Course] = []
        for code in course_codes:
            if not code:
                continue
            
            course_obj = Course(code=code)
            roll_numbers = course_roll_map.get(code, [])
            
            for roll in roll_numbers:
                name = roll_name_map.get(roll, "Unknown Name")
                course_obj.students.append(Student(roll=roll, name=name))
            
            course_obj.students.sort(key=lambda s: s.roll)  # sorting by roll number
            
            if course_obj.student_count > 0:
                courses.append(course_obj)
            else:
                logging.warning(f"No students found for course: {code}")
        
        return courses

    except Exception as e:
        logging.error(f"Error getting courses: {e}")
        raise