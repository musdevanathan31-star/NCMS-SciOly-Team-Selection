# NCMS SciOly Team Selection

This program selects a **15-student team** and assigns students to **23 Science Olympiad events** based on per-event performance scores.

It supports events that require **either 2 or 3 students**:
- **Codebusters** and **Experimental_Design** require **3 slots**
- All other events require **2 slots**

The assignment is solved as an **optimization problem (ILP)** to maximize total score while respecting participation limits.

---

## Key rules enforced

- Select **exactly 15 unique students** for the team.
- Assign the required number of students to **each of the 23 events**.
- **Every selected student must be used at least once** (so the “team list” matches the students actually competing).
- Each student may participate in **at most 4 events**.
- Preference: keep students at **≤ 2 events** when possible (implemented as a soft penalty for a 3rd/4th event).
- Students are not assigned to events in the same **conflict block** (optional, configured in header).

---

## Requirements

- Python 3.9+ recommended
- PuLP (linear programming library)

Install PuLP:

```bash
pip install pulp
```

PuLP typically uses the CBC solver via `pulp.PULP_CBC_CMD`. If CBC is not available in your environment, you may need to install/configure a supported solver.

---

## Input format

The program reads from **stdin**.

### Header row (single line)

```
N event1:slots[@block] event2:slots[@block] ... event23:slots[@block]
```

- `N` is the number of students.
- Each `event:slots` token gives the event name and how many students are needed for that event.
- Optional `@block` marks events that run at the same time; a student can be assigned to at most one event in each block.
  - Example: `Anatomy_and_Physiology:2@B1 Disease_Detectives:2@B1` means those two events conflict.

### Student rows (N lines)

```
StudentName score1 score2 ... score23
```

- Exactly 23 integer scores per student, in the same order as the header events.

### Example event list (recommended for your use case)

Use these event names (single-token, underscore-separated):

1. Anatomy_and_Physiology
2. Disease_Detectives
3. Entomology
4. Heredity
5. Water_Quality
6. Dynamic_Planet
7. Meteorology
8. Remote_Sensing
9. Rocks_and_Minerals
10. Solar_System
11. Circuit_Lab
12. Crime_Busters
13. Hovercraft
14. Machines
15. Potions_and_Poisons
16. Boomilever
17. Helicopter
18. Mission_Possible
19. Scrambler
20. Codebusters  (**3 slots**)
21. Experimental_Design (**3 slots**)
22. Metric_Mastery
23. Write_It_Do_It

Slots:
- `Codebusters:3`
- `Experimental_Design:3`
- all others `:2`

---

## Example input (template)

```text
20 Anatomy_and_Physiology:2 Disease_Detectives:2 Entomology:2 Heredity:2 Water_Quality:2 Dynamic_Planet:2 Meteorology:2 Remote_Sensing:2 Rocks_and_Minerals:2 Solar_System:2 Circuit_Lab:2 Crime_Busters:2 Hovercraft:2 Machines:2 Potions_and_Poisons:2 Boomilever:2 Helicopter:2 Mission_Possible:2 Scrambler:2 Codebusters:3 Experimental_Design:3 Metric_Mastery:2 Write_It_Do_It:2
Alice  85 90 70 88 92 76 81 79 84 73 95 80 78 82 69 91 77 74 83 89 86 72 87
Bob    75 80 68 70 85 72 79 71 76 74 82 77 73 69 66 78 70 72 75 90 88 65 80
...
```

---

## Running the program

```bash
python team_event_assignment.py < input.txt
```

---

## Output

The program prints:

- The selected & used 15-student team (with each student’s event load)
- The **top 3 alternates** (non-team students) ranked by **total score across all events**
- Per-student event list (which events each selected student is assigned to)
- A pretty-printed list of assignments for each event showing:
  - event name
  - number of slots
  - assigned students and their scores for that event
- Total performance score (raw sum of assigned scores)

---

## Notes / Customization

- To make the “prefer ≤ 2 events” rule stronger/weaker, adjust:
  - `PENALTY_THIRD_EVENT`
  - `PENALTY_FOURTH_EVENT`

- To change the maximum number of events per student, adjust:
  - `MAX_EVENTS_PER_STUDENT`
