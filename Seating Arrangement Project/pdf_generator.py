import os
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from typing import List
from data_models import Student

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 40  
COL_WIDTH = (PAGE_WIDTH - (2 * MARGIN)) / 3  
ROW_HEIGHT = 100  
PHOTO_WIDTH = 60
PHOTO_HEIGHT = 60
PHOTOS_DIR = 'photos'  
FALLBACK_IMAGE = 'nopic.jpg' 

class AttendancePDFGenerator:
    def __init__(self, output_path, date_str, session, room, course_code, student_count):
        self.c = canvas.Canvas(output_path, pagesize=A4)
        self.date_str = date_str
        self.session = session
        self.room = room
        self.course_code = course_code
        self.student_count = student_count
        self.y_curr = PAGE_HEIGHT - MARGIN 

    def _get_formatted_date(self):
        try:
            date_obj = datetime.strptime(self.date_str, '%Y-%m-%d')
            return date_obj.strftime('%d-%m-%Y (%A)')
        except:
            return self.date_str

    def draw_header(self):
        c = self.c
        c.setLineWidth(1)
        
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(PAGE_WIDTH / 2, self.y_curr, "IITP Attendance System") 
        self.y_curr -= 20 

        header_height = 50 
        box_top = self.y_curr
        box_bottom = self.y_curr - header_height
        box_width = PAGE_WIDTH - (2 * MARGIN)
        
        c.rect(MARGIN, box_bottom, box_width, header_height)
        
        mid_y = box_top - (header_height / 2)
        c.line(MARGIN, mid_y, PAGE_WIDTH - MARGIN, mid_y)
        
        # ROW 1: Metadata
        # Date | Shift | Room No | Student count
        formatted_date = self._get_formatted_date()
        
        row1_text = (f"Date: {formatted_date}   |   Shift: {self.session}   |   "
                     f"Room No: {self.room}   |   Student count: {self.student_count}")
        
        c.setFont("Helvetica-Bold", 10)

        text_y_row1 = box_top - 16 
        c.drawString(MARGIN + 5, text_y_row1, row1_text)
        
        
        split_x1 = MARGIN + (box_width * 0.55)
        c.line(split_x1, mid_y, split_x1, box_bottom)

        split_x2 = MARGIN + (box_width * 0.80)
        c.line(split_x2, mid_y, split_x2, box_bottom)
        
        text_y_row2 = mid_y - 16
        
        # Draw Text
        c.drawString(MARGIN + 5, text_y_row2, f"Subject: {self.course_code}")
        c.drawString(split_x1 + 5, text_y_row2, "Stud Present:")
        c.drawString(split_x2 + 5, text_y_row2, "Stud Absent:")
        
        self.y_curr -= (header_height + 15) 

    def draw_student_block(self, x_pos, y_pos, student: Student):
        c = self.c
        c.setLineWidth(0.5)
        c.rect(x_pos, y_pos, COL_WIDTH - 5, ROW_HEIGHT, stroke=1, fill=0)

        # 1. Photo Logic
        photo_path = os.path.join(PHOTOS_DIR, f"{student.roll.upper()}.jpg")
        final_photo_path = None
        
        if os.path.exists(photo_path):
            final_photo_path = photo_path
        elif os.path.exists(os.path.join(PHOTOS_DIR, FALLBACK_IMAGE)):
            final_photo_path = os.path.join(PHOTOS_DIR, FALLBACK_IMAGE) 

        img_x = x_pos + 5
        img_y = y_pos + ROW_HEIGHT - PHOTO_HEIGHT - 10 

        if final_photo_path:
            try:
                c.drawImage(final_photo_path, img_x, img_y, width=PHOTO_WIDTH, height=PHOTO_HEIGHT, preserveAspectRatio=True)
            except Exception as e:
                logging.error(f"Error rendering image {final_photo_path}: {e}")
                c.setFont("Helvetica-Oblique", 8)
                c.drawString(img_x, img_y + 30, "Img Error")
        else:
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(img_x + 10, img_y + 30, "No Image") 
            c.drawString(img_x + 10, img_y + 20, "Available")

        # 2. Text Details
        text_x = img_x + PHOTO_WIDTH + 5
        current_text_y = y_pos + ROW_HEIGHT - 20 

        c.setFont("Helvetica-Bold", 10)
        safe_name = (student.name[:15] + '..') if len(student.name) > 17 else student.name
        c.drawString(text_x, current_text_y, safe_name)
        
        current_text_y -= 15
        c.setFont("Helvetica", 10)
        c.drawString(text_x, current_text_y, f"Roll: {student.roll}")
        
        current_text_y -= 35
        c.drawString(text_x, current_text_y, "Sign: _______")

    def draw_footer_table(self):
        c = self.c

        if self.y_curr < 250:
            c.showPage()
            self.y_curr = PAGE_HEIGHT - MARGIN

        self.y_curr -= 20
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(PAGE_WIDTH / 2, self.y_curr, "Invigilator Name & Signature") 
        self.y_curr -= 5

        row_h = 20
        col_w_sno = 30
        col_w_name = 200
        col_w_sign = 200
        table_start_x = MARGIN + 20
        
        # Header Row
        self.y_curr -= row_h
        c.rect(table_start_x, self.y_curr, col_w_sno + col_w_name + col_w_sign, row_h)
        c.line(table_start_x + col_w_sno, self.y_curr, table_start_x + col_w_sno, self.y_curr + row_h)
        c.line(table_start_x + col_w_sno + col_w_name, self.y_curr, table_start_x + col_w_sno + col_w_name, self.y_curr + row_h)

        c.drawString(table_start_x + 5, self.y_curr + 6, "Sl No.")
        c.drawString(table_start_x + col_w_sno + 5, self.y_curr + 6, "Name")
        c.drawString(table_start_x + col_w_sno + col_w_name + 5, self.y_curr + 6, "Signature")

        # 10 Blank Rows
        c.setFont("Helvetica", 10)
        for i in range(1, 11):
            self.y_curr -= row_h
            c.rect(table_start_x, self.y_curr, col_w_sno + col_w_name + col_w_sign, row_h)
            c.line(table_start_x + col_w_sno, self.y_curr, table_start_x + col_w_sno, self.y_curr + row_h)
            c.line(table_start_x + col_w_sno + col_w_name, self.y_curr, table_start_x + col_w_sno + col_w_name, self.y_curr + row_h)
            c.drawCentredString(table_start_x + (col_w_sno/2), self.y_curr + 6, str(i))

    def generate(self, students: List[Student]):
        self.draw_header()

        col_counter = 0
        x_start = MARGIN
        
        for student in students:
            if self.y_curr < (ROW_HEIGHT + MARGIN):
                self.c.showPage()
                self.y_curr = PAGE_HEIGHT - MARGIN
            
            current_x = x_start + (col_counter * COL_WIDTH)
            
            self.draw_student_block(current_x, self.y_curr - ROW_HEIGHT, student)
            
            col_counter += 1
            
            if col_counter >= 3:
                col_counter = 0
                self.y_curr -= (ROW_HEIGHT + 5) 

        # Fix cursor for overlapping footer if last row was partial
        if col_counter > 0:
             self.y_curr -= (ROW_HEIGHT + 5)

        self.draw_footer_table()
        self.c.save()

def generate_attendance_pdfs(output_dir: str, arrangement_data: dict, date: str, session: str):
    if not os.path.exists(PHOTOS_DIR):
        logging.warning(f"Photos directory '{PHOTOS_DIR}' not found. Images will be missing.")

    for room_num, allocations in arrangement_data.items():
        if not allocations:
            continue

        for course_code, students in allocations:
            try:
                student_count = len(students)
                safe_date = date.replace("-", "_")
                filename = f"{safe_date}_{session}_{room_num}_{course_code}.pdf"
                filepath = os.path.join(output_dir, filename)
                
                generator = AttendancePDFGenerator(
                    filepath, date, session, room_num, course_code, student_count
                )
                generator.generate(students)
                logging.info(f"Generated PDF: {filename}")

            except Exception as e:
                logging.error(f"Failed to generate PDF for {date} {session} {room_num} {course_code}: {e}", exc_info=True)