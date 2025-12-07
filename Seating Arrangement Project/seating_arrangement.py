import logging
import os
import sys
import pandas as pd
import utils
import data_loader
import logic
import output_writer
import pdf_generator 

def main():
    utils.setup_logging()
    logging.info("--- Starting Exam Seating Arrangement System ---")
    
    try:
        # 1. Inputs
        print("Please configure global settings:")
        buffer_str = input("Enter buffer (e.g., 5): ").strip()
        density = input("Enter density (sparse/dense): ").strip().lower() 

        if density not in ['sparse', 'dense']:
            raise ValueError("Density must be 'sparse' or 'dense'.")
        buffer = int(buffer_str)

        # 2. Load Data
        logging.info("Loading static data maps...")
        roll_name_map = data_loader.load_roll_name_mapping(utils.ROLL_NAME_MAPPING_FILE)
        course_roll_map = data_loader.load_course_roll_mapping(utils.COURSE_ROLL_MAPPING_FILE)
        all_rooms = data_loader.load_room_capacities(utils.ROOM_CAPACITY_FILE)
        
        # Get list of all slots (Dates + Morning/Evening)
        scheduled_slots = data_loader.get_all_scheduled_slots(utils.TIMETABLE_FILE)
        logging.info(f"Found {len(scheduled_slots)} slots to process.")

        master_schedule_data = [] 

        # 3. Main Processing Loop
        for date, slot in scheduled_slots:
            logging.info(f"--- Processing {date} : {slot} ---")
            
            courses_for_slot = data_loader.get_courses_for_slot(
                utils.TIMETABLE_FILE, course_roll_map, roll_name_map, date, slot
            )

            if not courses_for_slot:
                logging.info(f"No valid courses for {date} {slot}. Skipping.")
                continue

            if logic.check_for_clashes(courses_for_slot):
                logging.error(f"Clash detected for {date} {slot}. Skipping allocation.")
                continue

            try:
                # Allocating
                (arrangement, seats_left) = logic.allocate_seating(
                    courses_for_slot, all_rooms, buffer, density
                )
                
                output_dir = output_writer.create_output_directory(date, slot)
                
                left_path = os.path.join(output_dir, utils.OUTPUT_SEATS_LEFT_FILE)
                output_writer.write_seats_left(left_path, seats_left, all_rooms)
                
                output_writer.write_attendance_sheets(output_dir, arrangement, date, slot)

                logging.info("Generating PDF Attendance Sheets...")
                pdf_generator.generate_attendance_pdfs(output_dir, arrangement, date, slot)

                day_name = pd.to_datetime(date).day_name()
                
                for room_num, allocations in arrangement.items():
                    for course_code, students in allocations:
                        roll_list_str = ";".join([s.roll for s in students])
                        master_schedule_data.append({
                            "Date": date,
                            "Day": day_name,
                            "Course Code": course_code,
                            "Room": room_num,
                            "Allocated Count": len(students),
                            "Roll List": roll_list_str
                        })
                
            except Exception as e:
                logging.error(f"Failed to allocate/write for {date} {slot}: {e}", exc_info=True)

        logging.info("Generating Master Seating Arrangement File...")
        output_writer.write_master_plan(utils.OUTPUT_ARRANGEMENT_FILE, master_schedule_data)

        logging.info("--- All processes completed successfully. ---")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"An unexpected error occurred. Check {utils.ERROR_LOG_FILE} for details.", file=sys.stderr)

if __name__ == "__main__":
    main()