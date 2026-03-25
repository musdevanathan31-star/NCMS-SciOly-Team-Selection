import unittest
import io
import sys

from team_event_assignment import parse_input, solve_ilp


class TestConflictAssignments(unittest.TestCase):
    def test_parse_input_supports_conflict_blocks(self):
        data = (
            "15 "
            "E01:2@A E02:2@A E03:2 E04:2 E05:2 E06:2 E07:2 E08:2 E09:2 E10:2 "
            "E11:2 E12:2 E13:2 E14:2 E15:2 E16:2 E17:2 E18:2 E19:2 E20:2 E21:2 E22:2 E23:2\n"
            + "\n".join([f"S{i:02d} " + " ".join(["1"] * 23) for i in range(15)])
            + "\n"
        )
        old_stdin = sys.stdin
        try:
            sys.stdin = io.StringIO(data)
            _, _, event_blocks, _, _ = parse_input()
        finally:
            sys.stdin = old_stdin

        self.assertEqual("A", event_blocks[0])
        self.assertEqual("A", event_blocks[1])
        self.assertIsNone(event_blocks[2])

    def test_solver_never_assigns_student_to_conflicting_events(self):
        n = 15
        event_slots = [2] * 23
        event_blocks = [None] * 23
        event_blocks[0] = "A"
        event_blocks[1] = "A"

        scores = []
        for student_idx in range(n):
            row = [10] * 23
            if student_idx < 2:
                row[0] = 1000
                row[1] = 1000
            scores.append(row)

        _, assignments_by_event, _, _ = solve_ilp(scores, event_slots, event_blocks)
        event0 = set(assignments_by_event[0])
        event1 = set(assignments_by_event[1])
        self.assertEqual(set(), event0.intersection(event1))


if __name__ == "__main__":
    unittest.main()
