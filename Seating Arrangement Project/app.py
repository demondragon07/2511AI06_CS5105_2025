import streamlit as st
import pandas as pd
import os
import shutil
import zipfile
import logging

import utils
import data_loader
import logic
import output_writer
import pdf_generator

WORKING_DIR = "files"
PHOTOS_DIR = "photos"
OUTPUT_DIR = "output"
INPUT_EXCEL_PATH = os.path.join(WORKING_DIR, "input_data_tt.xlsx")
ARCHIVE_NAME = "seating_arrangement_output"

os.makedirs(WORKING_DIR, exist_ok=True)
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class StreamlitLogHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.log_buffer = []

    def emit(self, record):
        msg = self.format(record)
        self.log_buffer.append(msg)
        
        self.widget.code("\n".join(self.log_buffer[-15:]), language="text") # we only display last 15 lines of logs
def main():
    st.set_page_config(page_title="IITP Seating Arrangement", layout="wide")
    
    st.title("Exam Seating Arrangement System")
    st.markdown("Upload input data, configure settings, and generate seating plans with PDF attendance sheets.")

    with st.sidebar:
        st.header("Settings")
        buffer = st.number_input("Buffer Capacity", min_value=0, value=5, help="Seats to leave empty per room.")
        density = st.selectbox("Density Mode", ["dense", "sparse"], index=0, help="Sparse fills only 50% capacity per subject.")
        
        st.divider()
        st.info("Ensure your Input Excel follows the required schema.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Input Data")
        uploaded_excel = st.file_uploader("Upload Input_Data.xlsx", type=["xlsx"])

    with col2:
        st.subheader("2. Upload Photos (Optional)")
        uploaded_photos = st.file_uploader("Upload photos.zip", type=["zip"], help="Zip file containing student images (ROLL.jpg)")

    if st.button("Generate Seating Arrangement", type="primary"):
        if not uploaded_excel:
            st.error("Please upload the Input Excel file to proceed.")
            return

        cleanup_directories()
        
        save_uploaded_file(uploaded_excel, INPUT_EXCEL_PATH)
        if uploaded_photos:
            extract_photos(uploaded_photos)
        else:
            st.warning("No photos uploaded. Placeholders will be used for attendance sheets.")

        st.subheader("3. Execution Logs")
        log_container = st.empty()
        setup_streamlit_logging(log_container)

        try:
            run_allocation_process(buffer, density)
            st.success("Processing Complete!")
            
            shutil.make_archive(ARCHIVE_NAME, 'zip', OUTPUT_DIR)
            
            with open(f"{ARCHIVE_NAME}.zip", "rb") as fp:
                st.download_button(
                    label="Download Output (ZIP)",
                    data=fp,
                    file_name=f"{ARCHIVE_NAME}.zip",
                    mime="application/zip"
                )

        except Exception as e:
            st.error(f"An error occurred: {e}")
            logging.error(f"Critical Failure: {e}", exc_info=True)

def cleanup_directories():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_uploaded_file(uploaded_file, destination_path):
    with open(destination_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    logging.info(f"Saved input file to {destination_path}")

def extract_photos(uploaded_zip):
    try:
        with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
            zip_ref.extractall(PHOTOS_DIR)
        logging.info(f"Extracted photos to {PHOTOS_DIR}")
    except Exception as e:
        st.error(f"Failed to extract photos: {e}")

def setup_streamlit_logging(widget):
    
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    st_handler = StreamlitLogHandler(widget)
    st_handler.setFormatter(formatter)
    root_logger.addHandler(st_handler)
    
    # we keep errors and logs here
    file_handler = logging.FileHandler("errors.txt", mode='w')
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(file_handler)

def run_allocation_process(buffer, density):
    logging.info("--- Starting Allocation Process ---")
    logging.info(f"Global Params: Buffer={buffer}, Density={density}")

    logging.info("Loading static data maps...")
    try:
        roll_name_map = data_loader.load_roll_name_mapping(utils.ROLL_NAME_MAPPING_FILE)
        course_roll_map = data_loader.load_course_roll_mapping(utils.COURSE_ROLL_MAPPING_FILE)
        all_rooms = data_loader.load_room_capacities(utils.ROOM_CAPACITY_FILE)
        
        scheduled_slots = data_loader.get_all_scheduled_slots(utils.TIMETABLE_FILE)
        logging.info(f"Found {len(scheduled_slots)} slots to process.")
        
        master_schedule_data = []

        for date, slot in scheduled_slots:
            logging.info(f"Processing {date} : {slot}")
            
            courses = data_loader.get_courses_for_slot(
                utils.TIMETABLE_FILE, course_roll_map, roll_name_map, date, slot
            )

            if not courses:
                logging.info(f"Skipping {date} {slot} (No exams).")
                continue

            if logic.check_for_clashes(courses):
                logging.error(f"Skipping {date} {slot} due to CLASH.")
                continue

            try:
                arrangement, seats_left = logic.allocate_seating(courses, all_rooms, buffer, density)
                
                output_path = output_writer.create_output_directory(date, slot)
                
                output_writer.write_seats_left(
                    os.path.join(output_path, utils.OUTPUT_SEATS_LEFT_FILE), 
                    seats_left, 
                    all_rooms
                )
                
                output_writer.write_attendance_sheets(output_path, arrangement, date, slot)
                
                pdf_generator.generate_attendance_pdfs(output_path, arrangement, date, slot)

                day_name = pd.to_datetime(date).day_name()
                for room_num, allocations in arrangement.items():
                    for course_code, students in allocations:
                        roll_str = ";".join([s.roll for s in students])
                        master_schedule_data.append({
                            "Date": date,
                            "Day": day_name,
                            "Course Code": course_code,
                            "Room": room_num,
                            "Allocated Count": len(students),
                            "Roll List": roll_str
                        })

            except Exception as e:
                logging.error(f"Error processing {date} {slot}: {e}")

        if master_schedule_data:
            logging.info("Generating Master Seating Arrangement File...")
            output_writer.write_master_plan(utils.OUTPUT_ARRANGEMENT_FILE, master_schedule_data)
        else:
            logging.warning("No data generated for Master File.")

    except Exception as e:
        logging.error(f"Fatal error in allocation logic: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    main()