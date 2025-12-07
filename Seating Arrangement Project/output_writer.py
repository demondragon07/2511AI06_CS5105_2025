import pandas as pd
import os
import logging
from typing import List, Dict, Tuple, Any
from data_models import Room, Student

def create_output_directory(date: str, slot: str) -> str:
    """Creates the required output directory structure."""
    dir_path = os.path.join("output", date, slot.lower())
    try:
        os.makedirs(dir_path, exist_ok=True)
        return dir_path
    except OSError as e:
        logging.error(f"Failed to create directory {dir_path}: {e}")
        raise

def write_master_plan(output_path: str, master_rows: List[Dict[str, Any]]):
    """
    Writes the single MASTER seating arrangement file containing ALL dates.
    Columns: Date, Day, Course Code, Room, Count, Roll List
    """
    if not master_rows:
        logging.warning("No data to write to Master Seating Plan.")
        return

    try:
        df = pd.DataFrame(master_rows)
        # Column order in output file
        cols = ["Date", "Day", "Course Code", "Room", "Allocated Count", "Roll List"]
        
        # Filter to only existing columns and reorder
        df = df[cols]
        
        full_path = os.path.join("output", output_path)
        df.to_excel(full_path, index=False)
        logging.info(f"Successfully wrote MASTER arrangement file to {full_path}")
    except Exception as e:
        logging.error(f"Failed to write Master Arrangement file: {e}")

def write_seating_arrangement(
    output_path: str, 
    arrangement_data: Dict[str, List[Tuple[str, List[Student]]]], 
    room_data: Dict[str, Room]
):
    """Writes the per-session arrangement file (kept for folder-level detail)."""
    output_rows = []
    
    for room_num, allocations in arrangement_data.items():
        if not allocations:
            continue
            
        room = room_data[room_num]
        row = {"Room No.": room.number, "Block": room.block}
        
        for i, (course_code, students) in enumerate(allocations):
            col_suffix = i + 1
            roll_str = ";".join([s.roll for s in students])
            
            row[f'Subject {col_suffix}'] = course_code
            row[f'Count {col_suffix}'] = len(students)
            row[f'Rolls {col_suffix}'] = roll_str
        
        output_rows.append(row)

    try:
        if not output_rows:
            return 
            
        df = pd.DataFrame(output_rows)
        # Dynamic column sorting to keep Subject 1, Count 1, Rolls 1 together
        cols = ["Room No.", "Block"]
        max_subjects = max(len(a) for a in arrangement_data.values()) if arrangement_data else 0
        for i in range(1, max_subjects + 1):
            cols.extend([f'Subject {i}', f'Count {i}', f'Rolls {i}'])
        
        df = df.reindex(columns=[c for c in cols if c in df.columns])
        df.to_excel(output_path, index=False)
        logging.info(f"Successfully wrote session arrangement file to {output_path}")
    except Exception as e:
        logging.error(f"Failed to write session file: {e}")

def write_seats_left(
    output_path: str, 
    seats_left_data: Dict[str, int], 
    room_data: Dict[str, Room]
):
    """Writes the op_seats_left.xlsx file."""
    output_rows = []
    for room_num, seats_left in seats_left_data.items():
        room = room_data[room_num]
        output_rows.append({
            "Room No.": room.number,
            "Block": room.block,
            "Original Capacity": room.capacity,
            "Effective Capacity": room.effective_capacity,
            "Seats Left": seats_left
        })
        
    try:
        df = pd.DataFrame(output_rows)
        df = df.sort_values(by=["Block", "Room No."])
        df.to_excel(output_path, index=False)
        logging.info(f"Successfully wrote seats left file to {output_path}")
    except Exception as e:
        logging.error(f"Failed to write seats left file: {e}")

def write_attendance_sheets(
    output_dir: str, 
    arrangement_data: Dict[str, List[Tuple[str, List[Student]]]], 
    date: str,
    slot: str
):
    for room_num, allocations in arrangement_data.items():
        for course_code, students in allocations:
            data = []
            for idx, student in enumerate(students, 1):
                data.append({
                    "S.No": idx,
                    "Roll No.": student.roll,
                    "Name": student.name,
                    "Signature": ""
                })
            
            df = pd.DataFrame(data)
            
            safe_date = date.replace("-", "_")
            filename = f"{safe_date}_{course_code}_{room_num}.xlsx"
            filepath = os.path.join(output_dir, filename)
            
            try:
                writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
                df.to_excel(writer, sheet_name='Sheet1', startrow=4, index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Sheet1']
                
                # --- FORMATTING ---

                header_format = workbook.add_format({
                    'bold': True,
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_size': 14,
                    'border': 1
                })
                
                header_text = f"Course: {course_code} | Room: {room_num} | Date: {date} | Session: {slot}"
                worksheet.merge_range('A1:D3', header_text, header_format)
                
                # Column Widths
                worksheet.set_column('A:A', 8)   # S.No
                worksheet.set_column('B:B', 15)  # Roll No
                worksheet.set_column('C:C', 30)  # Name
                worksheet.set_column('D:D', 20)  # Signature
                
                # Footer (Static Invigilator & TA Text), starting 2 rows after last entry
                footer_start_row = len(data) + 6
                footer_format = workbook.add_format({'font_size': 11})
                
                footer_lines = [
                    "Invigilators:",
                    "1. __________________________",
                    "2. __________________________",
                    "3. __________________________",
                    "4. __________________________",
                    "5. __________________________",
                    "", 
                    "TA:",
                    "1. __________________________",
                    "2. __________________________",
                    "3. __________________________",
                    "4. __________________________",
                    "5. __________________________"
                ]
                
                for i, line in enumerate(footer_lines):
                    worksheet.write(footer_start_row + i, 0, line, footer_format)
                
                writer.close()
                
            except Exception as e:
                logging.error(f"Failed to create attendance sheet {filename}: {e}")

    logging.info(f"Generated attendance sheets in {output_dir}")