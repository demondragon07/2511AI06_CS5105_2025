# data_models.py
from dataclasses import dataclass, field
from typing import List

@dataclass
class Student:  # single student
    roll: str
    name: str

@dataclass
class Room:  # single classroom
    number: str
    capacity: int
    block: str
    effective_capacity: int = 0

@dataclass
class Course:   # course with enrolled students
    code: str
    students: List[Student] = field(default_factory=list)

    @property
    def student_count(self) -> int:  # provides the number of students
        return len(self.students)