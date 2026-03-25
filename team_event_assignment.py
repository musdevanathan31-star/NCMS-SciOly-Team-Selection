from __future__ import annotations

import sys
from collections import defaultdict
import re
from typing import List, Tuple, Dict, Optional


EVENTS = 23
TEAM_SIZE = 15

MAX_EVENTS_PER_STUDENT = 4

# Soft preference: discourage giving a student 3rd or 4th event.
PENALTY_THIRD_EVENT = 50
PENALTY_FOURTH_EVENT = 120


def parse_input() -> Tuple[List[str], List[int], List[Optional[str]], List[str], List[List[int]]]:
    """
    Input format (stdin):
      N event1:slots event2:slots ... event23:slots
      student_name score1 score2 ... score23
      ... (N lines)

    Example header:
      20 E01:2 E02:2 ... E08:3 ... E23:2

    Notes:
      - event names must be single tokens (no spaces). Use underscores if needed.
      - slots must be integer (e.g., 2 or 3).
      - scores must be integers.
    """
    data = [line.strip() for line in sys.stdin if line.strip()]
    if not data:
        raise ValueError("No input provided.")

    header = data[0].split()
    if len(header) != 1 + EVENTS:
        raise ValueError(
            f"Header must be: N + {EVENTS} event:slots tokens (total {1 + EVENTS} tokens), got {len(header)}."
        )

    n = int(header[0])
    if n <= 0:
        raise ValueError("N must be positive.")

    event_names: List[str] = []
    event_slots: List[int] = []
    event_blocks: List[Optional[str]] = []

    for tok in header[1:]:
        if tok.count("@") > 1:
            raise ValueError(f"Bad event token '{tok}': only one '@block' suffix is allowed.")

        base_tok = tok
        block: Optional[str] = None
        if "@" in tok:
            base_tok, block = tok.rsplit("@", 1)
            if block == "":
                raise ValueError(f"Bad event token '{tok}': empty conflict block after '@'.")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", block):
                raise ValueError(
                    f"Bad event token '{tok}': conflict block must use only letters, numbers, '_' or '-'."
                )

        if ":" not in base_tok:
            raise ValueError(f"Event token '{tok}' must be formatted as Name:slots (e.g., E08:3).")
        name, slots_s = base_tok.rsplit(":", 1)
        if not name:
            raise ValueError(f"Bad event token '{tok}': empty name.")
        try:
            slots = int(slots_s)
        except ValueError as e:
            raise ValueError(f"Bad slots in token '{tok}': '{slots_s}' is not an int.") from e
        if slots <= 0:
            raise ValueError(f"Bad slots in token '{tok}': slots must be positive.")
        event_names.append(name)
        event_slots.append(slots)
        event_blocks.append(block)

    if len(data) != 1 + n:
        raise ValueError(f"Expected {n} student lines after header, got {len(data) - 1}.")

    student_names: List[str] = []
    scores: List[List[int]] = []

    for i in range(n):
        parts = data[i + 1].split()
        if len(parts) != 1 + EVENTS:
            raise ValueError(
                f"Line {i+2}: expected student_name + {EVENTS} scores (total {1 + EVENTS} fields), got {len(parts)}."
            )
        student_names.append(parts[0])
        scores.append(list(map(int, parts[1:])))

    return event_names, event_slots, event_blocks, student_names, scores


def solve_ilp(
    scores: List[List[int]], event_slots: List[int], event_blocks: Optional[List[Optional[str]]] = None
) -> Tuple[List[int], List[List[int]], List[int], int]:
    """
    ILP model:
      - choose TEAM_SIZE students
      - assign exactly event_slots[e] students per event
      - max 4 events per student (counting "being in an event" as 1)
      - all 15 selected students must be used at least once
      - soft penalty for having >=3 events and >=4 events
    """
    try:
        import pulp  # type: ignore
    except Exception as e:
        raise RuntimeError("This program requires PuLP. Install with: pip install pulp") from e

    n = len(scores)
    E = len(event_slots)
    if E != EVENTS:
        raise ValueError(f"Expected event_slots length {EVENTS}, got {E}.")
    if event_blocks is not None and len(event_blocks) != E:
        raise ValueError(f"Expected event_blocks length {E}, got {len(event_blocks)}.")

    y = pulp.LpVariable.dicts("y", range(n), 0, 1, cat="Binary")  # selected
    u = pulp.LpVariable.dicts("u", range(n), 0, 1, cat="Binary")  # used at least once
    x = pulp.LpVariable.dicts("x", (range(n), range(E)), 0, 1, cat="Binary")  # assigned to event

    t3 = pulp.LpVariable.dicts("t3", range(n), 0, 1, cat="Binary")  # load >= 3
    t4 = pulp.LpVariable.dicts("t4", range(n), 0, 1, cat="Binary")  # load == 4

    prob = pulp.LpProblem("TeamEventAssignment", pulp.LpMaximize)

    load = {s: pulp.lpSum(x[s][e] for e in range(E)) for s in range(n)}

    prob += (
        pulp.lpSum(scores[s][e] * x[s][e] for s in range(n) for e in range(E))
        - pulp.lpSum(PENALTY_THIRD_EVENT * t3[s] + PENALTY_FOURTH_EVENT * t4[s] for s in range(n))
    )

    prob += pulp.lpSum(y[s] for s in range(n)) == TEAM_SIZE

    for e in range(E):
        prob += pulp.lpSum(x[s][e] for s in range(n)) == event_slots[e]

    for s in range(n):
        for e in range(E):
            prob += x[s][e] <= y[s]

    for s in range(n):
        prob += load[s] <= MAX_EVENTS_PER_STUDENT

    for s in range(n):
        prob += u[s] <= y[s]
        prob += load[s] >= u[s]
        prob += load[s] <= MAX_EVENTS_PER_STUDENT * u[s]
    prob += pulp.lpSum(u[s] for s in range(n)) == TEAM_SIZE

    for s in range(n):
        prob += load[s] - 2 <= 2 * t3[s]
        prob += load[s] - 3 <= 1 * t4[s]
        prob += t4[s] <= t3[s]

    if event_blocks is not None:
        events_by_block: Dict[str, List[int]] = defaultdict(list)
        for e, block in enumerate(event_blocks):
            if block:
                events_by_block[block].append(e)
        for block_events in events_by_block.values():
            if len(block_events) > 1:
                for s in range(n):
                    prob += pulp.lpSum(x[s][e] for e in block_events) <= 1

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    if pulp.LpStatus[prob.status] != "Optimal":
        raise RuntimeError(f"Solver status: {pulp.LpStatus[prob.status]} (no optimal solution found).")

    team = [s for s in range(n) if pulp.value(y[s]) > 0.5]

    assignments_by_event: List[List[int]] = []
    for e in range(E):
        assigned = [s for s in range(n) if pulp.value(x[s][e]) > 0.5]
        if len(assigned) != event_slots[e]:
            raise RuntimeError(f"Bad assignment for event {e+1}: expected {event_slots[e]} got {len(assigned)}")
        assignments_by_event.append(assigned)

    loads = [int(round(pulp.value(load[s]) or 0)) for s in range(n)]

    perf = 0
    for e, assigned in enumerate(assignments_by_event):
        perf += sum(scores[s][e] for s in assigned)

    return team, assignments_by_event, loads, perf


def build_student_event_list(assignments_by_event: List[List[int]]) -> Dict[int, List[int]]:
    m: Dict[int, List[int]] = {}
    for e, ss in enumerate(assignments_by_event):
        for s in ss:
            m.setdefault(s, []).append(e)
    return m


def top_alternates(scores: List[List[int]], student_names: List[str], team: List[int], k: int = 3) -> List[Tuple[int, int]]:
    """
    Rank non-team students by total score across all events.
    Returns list of (student_index, total_score) length <= k.
    """
    team_set = set(team)
    totals = []
    for s in range(len(scores)):
        if s in team_set:
            continue
        totals.append((s, sum(scores[s])))
    totals.sort(key=lambda x: (-x[1], student_names[x[0]].lower()))
    return totals[:k]


def pretty_print_results(
    event_names: List[str],
    event_slots: List[int],
    student_names: List[str],
    scores: List[List[int]],
    team: List[int],
    assignments_by_event: List[List[int]],
    loads: List[int],
    perf: int,
) -> None:
    n = len(student_names)
    used = {s for ss in assignments_by_event for s in ss}
    total_slots = sum(event_slots)

    if len(used) != TEAM_SIZE:
        raise RuntimeError(f"Sanity check failed: used {len(used)} unique students, expected {TEAM_SIZE}.")
    if any(loads[s] > MAX_EVENTS_PER_STUDENT for s in used):
        raise RuntimeError("Sanity check failed: a student exceeds max events.")
    if sum(len(ss) for ss in assignments_by_event) != total_slots:
        raise RuntimeError("Sanity check failed: total assigned slots mismatch.")

    print("Optimal ILP (PuLP + CBC)")
    print(
        f"N={n}, TeamSize={TEAM_SIZE}, Events={len(event_names)}, TotalSlots={total_slots}, "
        f"MaxEventsPerStudent={MAX_EVENTS_PER_STUDENT}"
    )
    print()

    print("Selected & used team (exactly 15):")
    for s in sorted(team, key=lambda i: student_names[i].lower()):
        print(f"- {student_names[s]} (index {s})  load={loads[s]}")
    print()

    alts = top_alternates(scores, student_names, team, k=3)
    print("Alternates (top 3 non-team by total score across all events):")
    if not alts:
        print("- (none)")
    else:
        for rank, (s, tot) in enumerate(alts, start=1):
            print(f"{rank}. {student_names[s]} (index {s})  total_score={tot}")
    print()

    per_student = build_student_event_list(assignments_by_event)
    print("Per-student assignments:")
    for s in sorted(team, key=lambda i: (-loads[i], student_names[i].lower())):
        evs = per_student.get(s, [])
        ev_str = ", ".join(f"{event_names[e]}(#{e+1})" for e in evs)
        print(f"- {student_names[s]}: {loads[s]} event(s): {ev_str}")
    print()

    print("Event assignments:")
    name_w = max(len(en) for en in event_names)
    for e, assigned in enumerate(assignments_by_event):
        en = event_names[e]
        parts = [f"{student_names[s]}[{scores[s][e]}]" for s in assigned]
        print(f"{e+1:02d}. {en:<{name_w}} ({event_slots[e]} slots) : " + "  |  ".join(parts))
    print()
    print("Total performance score (no penalties):", perf)


def main() -> None:
    event_names, event_slots, event_blocks, student_names, scores = parse_input()

    if len(scores) < TEAM_SIZE:
        raise ValueError(f"Need at least {TEAM_SIZE} students to select a team, but got N={len(scores)}.")

    total_slots = sum(event_slots)
    if total_slots > TEAM_SIZE * MAX_EVENTS_PER_STUDENT:
        raise ValueError(
            f"Infeasible: total slots {total_slots} exceeds capacity {TEAM_SIZE * MAX_EVENTS_PER_STUDENT} "
            f"(TEAM_SIZE*MAX_EVENTS_PER_STUDENT)."
        )

    team, assignments_by_event, loads, perf = solve_ilp(scores, event_slots, event_blocks)
    pretty_print_results(event_names, event_slots, student_names, scores, team, assignments_by_event, loads, perf)


if __name__ == "__main__":
    main()
