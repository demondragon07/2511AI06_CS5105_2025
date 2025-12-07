import logging
from typing import List, Dict, Tuple, Set
from data_models import Course, Room, Student

def check_for_clashes(courses: List[Course]) -> bool:
    
    if not courses:
        return False
        
    student_sets: Dict[str, Set[str]] = {}
    for course in courses:
        student_sets[course.code] = {student.roll for student in course.students}

    clash_found = False
    course_codes = list(student_sets.keys())
    
    for i in range(len(course_codes)):
        for j in range(i + 1, len(course_codes)):
            code1 = course_codes[i]
            code2 = course_codes[j]
            
            intersection = student_sets[code1].intersection(student_sets[code2])
            
            if intersection:
                clash_found = True
                for roll in intersection:
                   
                    logging.error(f"CLASH DETECTED: Roll {roll} in {code1} and {code2}")
    
    return clash_found

def calculate_effective_capacity(room: Room, buffer: int, density: str) -> int:
    adjusted_capacity = room.capacity - buffer
    if adjusted_capacity < 0:
        adjusted_capacity = 0

    if density == 'sparse':

        return adjusted_capacity // 2
    else:

        return adjusted_capacity

def allocate_seating(
    courses: List[Course], 
    rooms: Dict[str, Room], 
    buffer: int, 
    density: str
) -> Tuple[Dict[str, List[Tuple[str, List[Student]]]], Dict[str, int]]:
    
    # 1. Calculate effective capacity & Initializing Trackers
    total_effective_capacity = 0
    room_capacities_left = {} # RoomNum: RemainingCap
    
    # Pre-sort rooms to ensure we pick smaller/ordered rooms within a block first if scores are tied
    sorted_rooms_static = sorted(rooms.values(), key=lambda r: (r.block, r.number))
    
    for room in sorted_rooms_static:
        eff_cap = calculate_effective_capacity(room, buffer, density)
        room.effective_capacity = eff_cap
        room_capacities_left[room.number] = eff_cap
        total_effective_capacity += eff_cap

    # 2. Capacity Check
    total_students = sum(c.student_count for c in courses)
    if total_students > total_effective_capacity:
        raise ValueError(f"Cannot allocate due to excess students. Needed: {total_students}, Available: {total_effective_capacity}")

    # 3. Sort courses (Largest First) to place big groups first
    sorted_courses = sorted(courses, key=lambda c: c.student_count, reverse=True)
    
    final_arrangement = {r.number: [] for r in sorted_rooms_static}
    course_block_affinity = {}

    def get_best_room_for_course(course_code: str, required_seats: int):
        candidates = []
        
        # Identify Preferred Block
        preferred_block = course_block_affinity.get(course_code)
        
        for i, r in enumerate(sorted_rooms_static):
            remaining = room_capacities_left[r.number]
            if remaining <= 0:
                continue
                
            score = 0
            
            # PRIORITY 1: CRITICAL - Stay in the same Block
            if preferred_block:
                if r.block == preferred_block:
                    score += 1_000_000  # Massive bonus to stay in block
                else:
                    score -= 1_000_000  # Massive penalty to leave block
            
            # PRIORITY 2: Contiguity / Same Floor (Linear Fill)
            score -= i  # Small penalty for being further down the list
            
            candidates.append((score, r))
        
        if not candidates:
            return None
            
        # Sort by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    # 4. Allocation Loop
    for course in sorted_courses:
        students_to_allocate = course.students.copy()
        logging.info(f"Allocating {course.code} ({len(students_to_allocate)} students)")
        
        while students_to_allocate:
            # Find best room for the CURRENT batch size
            best_room = get_best_room_for_course(course.code, len(students_to_allocate))
            
            if not best_room:
                # Should not happen due to total capacity check
                raise RuntimeError(f"Fragmentation Error: Enough total seats, but no room available for {course.code}.")

            # Set Affinity if this is the first room for this course
            if course.code not in course_block_affinity:
                course_block_affinity[course.code] = best_room.block
            
            # Log warning if optimization failed (forced split across blocks)
            if course_block_affinity[course.code] != best_room.block:
                logging.warning(f"Optimization Miss: {course.code} forced to split between {course_block_affinity[course.code]} and {best_room.block}")

            # Allocate
            cap_left = room_capacities_left[best_room.number]
            take = min(len(students_to_allocate), cap_left)
            
            allocated_batch = [students_to_allocate.pop(0) for _ in range(take)]
            final_arrangement[best_room.number].append((course.code, allocated_batch))
            
            room_capacities_left[best_room.number] -= take

    logging.info("Allocation complete.")
    return final_arrangement, room_capacities_left