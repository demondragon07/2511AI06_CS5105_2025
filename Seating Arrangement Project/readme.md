## Project Overview
This project is a comprehensive Python-based solution designed to automate the scheduling and allocation of university exams. It transforms raw input data (Timetables, Student Rolls, Room Capacities) into optimized seating plans and generates print-ready *Attendance Sheets (PDF)* with student photos.

The system is containerized using *Docker* to ensure it runs perfectly on any machine and features a user-friendly *Streamlit* web interface.

### Key Features
* *Optimized Allocation:* Uses a *"Linear Block Affinity"* algorithm to minimize student and faculty movement between buildings (e.g., Block 1 to Block 9).
* *Conflict Detection:* Automatically checks for and prevents scheduling clashes (same student, multiple exams in one slot).
* *Smart Capacity:* Handles *'Sparse'* (50% density) vs *'Dense'* (100% density) seating modes with configurable safety buffers.
* *PDF Generation:* Auto-generates A4 attendance sheets with student photos, merged headers, and static invigilator signature blocks.
* *Robustness:* Handles missing photos or data gracefully without crashing.

---

## Tech Stack
* *Language:* Python 3.10
* *Interface:* Streamlit
* *Data Processing:* Pandas, NumPy, OpenPyXL
* *PDF Generation:* ReportLab
* *Containerization:* Docker

---

## Project Structure
Ensure your project folder contains these files:
```
/project-root
├── app.py                 # Main Streamlit application (Entry Point)
├── logic.py               # Core algorithms (Clash detection, Allocation logic)
├── data_loader.py         # Excel parsing and data cleaning
├── output_writer.py       # Excel report generation
├── pdf_generator.py       # PDF attendance sheet generation (ReportLab)
├── data_models.py         # Data classes (Student, Room, Course)
├── utils.py               # Logging configuration
├── requirements.txt       # Python dependencies list
└── Dockerfile             # Docker image configuration
```
---

## Video Demonstration Link

([Click Here](https://youtu.be/DR00VIIeYfM))

---

## How to Run

### Method 1: Using Docker (Recommended)

This method ensures the application runs without manually installing Python or dependencies.

### 1. Build the Docker Image

bash
docker build -t student-management-system .


---

### 2. Run the Container

bash
docker run -p 8501:8501 student-management-system


---

### 3. Access the App

Open your browser:


http://localhost:8501


---

## Method 2: Manual Python Execution

### 1. Install Python
Ensure *Python 3.10+* is installed.

---

### 2. Install Dependencies

bash
pip install -r requirements.txt


---

### 3. Run the App

bash
streamlit run app.py


---

## Usage Guide

### Configure Settings (Sidebar)

- *Buffer:* Empty seats per room
- *Density:*
  - Dense → Near full capacity
  - Sparse → ~50% capacity

---

### Upload Inputs

#### Input_Data.xlsx
Must contain:
- Timetable
- Student Mapping
- Room Capacities

#### photos.zip
- Format: <ROLL_NUMBER>.jpg

---

###  Generate
Click *Generate Seating Arrangement*

---

### Download
Click *Download Output (ZIP)*

---

## Output Artifacts

### op_overall_seating_arrangement.xlsx
Master consolidated seating plan.

### op_seats_left.xlsx
Room capacity utilization report.

### Attendance PDFs
Location:

Output > [Date] > [Session]


Format:

YYYY_MM_DD_Session_Room_Subject.pdf


- A4 size
- 3-column photo grid
- Header on first page only
- Invigilator table on last page only

### errors.txt
Logs missing photos, overflows, and warnings.

---

## Smart Allocation Logic

- Subjects sorted by student count (largest first)
- Preferred block assigned on first room
- Same block gets +1,000,000 score bonus
- Linear floor-wise room filling

Result: Students remain on the same building and adjacent floors.

---

## Features

- Automated seating generation
- Block affinity optimization
- Attendance sheet PDFs with photos
- Capacity tracking reports
- Error diagnostics
- One-click ZIP download

---

## Requirements

- Python 3.10+
- OR Docker

---

## License

For academic and institutional use.

---

