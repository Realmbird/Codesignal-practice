import unittest
from simulation import simulate


class TestSimulate(unittest.TestCase):

    # ------------------------------------------------------------------
    # Level 1: ADD_TASK, GET_TASK, DELETE_TASK
    # ------------------------------------------------------------------
    def test_level_1(self):
        queries = [
            ["ADD_TASK", "write_report"],
            ["ADD_TASK", "review_code"],
            ["GET_TASK", "1"],
            ["GET_TASK", "2"],
            ["GET_TASK", "99"],
            ["DELETE_TASK", "1"],
            ["GET_TASK", "1"],
            ["DELETE_TASK", "99"],
        ]
        r = simulate(queries)
        self.assertEqual(r[0], "added 1")
        self.assertEqual(r[1], "added 2")
        self.assertEqual(r[2], "name=write_report")
        self.assertEqual(r[3], "name=review_code")
        self.assertEqual(r[4], "task not found")
        self.assertEqual(r[5], "deleted")
        self.assertEqual(r[6], "task not found")
        self.assertEqual(r[7], "task not found")

    # ------------------------------------------------------------------
    # Level 2: LIST_TASKS (insertion order), SEARCH_TASKS (prefix, alpha),
    #           UPDATE_TASK
    # ------------------------------------------------------------------
    def test_level_2(self):
        queries = [
            ["ADD_TASK", "write_report"],
            ["ADD_TASK", "review_code"],
            ["ADD_TASK", "write_tests"],
            ["LIST_TASKS"],
            ["SEARCH_TASKS", "write"],
            ["SEARCH_TASKS", "deploy"],
            ["UPDATE_TASK", "1", "finalize_report"],
            ["GET_TASK", "1"],
            ["LIST_TASKS"],
            ["UPDATE_TASK", "99", "ghost"],
        ]
        r = simulate(queries)
        self.assertEqual(r[3], "write_report,review_code,write_tests")
        self.assertEqual(r[4], "write_report,write_tests")   # alphabetical
        self.assertEqual(r[5], "no results")
        self.assertEqual(r[6], "updated")
        self.assertEqual(r[7], "name=finalize_report")
        self.assertEqual(r[8], "finalize_report,review_code,write_tests")  # insertion order
        self.assertEqual(r[9], "task not found")

    # ------------------------------------------------------------------
    # Level 3: SET_PRIORITY, LIST_BY_PRIORITY, ADD_TAG, SEARCH_BY_TAG
    # ------------------------------------------------------------------
    def test_level_3(self):
        queries = [
            ["ADD_TASK", "task_a"],
            ["ADD_TASK", "task_b"],
            ["ADD_TASK", "task_c"],
            ["SET_PRIORITY", "1", "3"],
            ["SET_PRIORITY", "2", "5"],
            ["SET_PRIORITY", "3", "5"],
            ["LIST_BY_PRIORITY"],
            ["ADD_TAG", "1", "backend"],
            ["ADD_TAG", "2", "backend"],
            ["ADD_TAG", "3", "frontend"],
            ["SEARCH_BY_TAG", "backend"],
            ["SEARCH_BY_TAG", "frontend"],
            ["SEARCH_BY_TAG", "devops"],
            ["SET_PRIORITY", "99", "3"],
            ["ADD_TAG", "99", "backend"],
        ]
        r = simulate(queries)
        # priority 5 first (task_b, task_c alphabetical), then priority 3 (task_a)
        self.assertEqual(r[6], "task_b,task_c,task_a")
        self.assertEqual(r[10], "task_a,task_b")   # alphabetical
        self.assertEqual(r[11], "task_c")
        self.assertEqual(r[12], "no results")
        self.assertEqual(r[13], "task not found")
        self.assertEqual(r[14], "task not found")

    # ------------------------------------------------------------------
    # Level 4: SET_DUE, LIST_OVERDUE, SET_STATUS, LIST_BY_STATUS
    # ------------------------------------------------------------------
    def test_level_4(self):
        queries = [
            ["ADD_TASK", "task_a"],
            ["ADD_TASK", "task_b"],
            ["ADD_TASK", "task_c"],
            ["SET_DUE", "1", "100"],
            ["SET_DUE", "2", "50"],
            ["SET_DUE", "3", "200"],
            ["LIST_OVERDUE", "150"],
            ["LIST_OVERDUE", "40"],
            ["SET_STATUS", "1", "IN_PROGRESS"],
            ["SET_STATUS", "2", "DONE"],
            ["LIST_BY_STATUS", "IN_PROGRESS"],
            ["LIST_BY_STATUS", "DONE"],
            ["LIST_BY_STATUS", "TODO"],
            ["SET_STATUS", "99", "DONE"],
            ["SET_DUE", "99", "100"],
        ]
        r = simulate(queries)
        # overdue at 150: due < 150 → task_b(50), task_a(100); sorted by due date asc
        self.assertEqual(r[6], "task_b,task_a")
        self.assertEqual(r[7], "no tasks")
        self.assertEqual(r[10], "task_a")
        self.assertEqual(r[11], "task_b")
        self.assertEqual(r[12], "task_c")   # only task_c still TODO
        self.assertEqual(r[13], "task not found")
        self.assertEqual(r[14], "task not found")

    # ------------------------------------------------------------------
    # Level 5: CONCURRENT_ADD — add tasks in parallel using threading
    # ------------------------------------------------------------------
    def test_level_5(self):
        queries = [["CONCURRENT_ADD", "alpha,beta,gamma,delta"]]
        r = simulate(queries)
        ids = r[0].split(",")
        self.assertEqual(len(ids), 4)
        # IDs must be sequential integers (order may vary due to threads)
        id_nums = sorted(int(i) for i in ids)
        self.assertEqual(id_nums, list(range(id_nums[0], id_nums[0] + 4)))

        # state must be consistent after concurrent writes
        queries2 = [
            ["CONCURRENT_ADD", "x,y,z"],
            ["LIST_TASKS"],
        ]
        r2 = simulate(queries2)
        task_list = r2[1].split(",")
        self.assertIn("x", task_list)
        self.assertIn("y", task_list)
        self.assertIn("z", task_list)

    # ------------------------------------------------------------------
    # Level 6: ASYNC_GET — fetch multiple tasks concurrently with asyncio
    # ------------------------------------------------------------------
    def test_level_6(self):
        queries = [
            ["ADD_TASK", "task_one"],
            ["ADD_TASK", "task_two"],
            ["ADD_TASK", "task_three"],
            ["ASYNC_GET", "1,2,3"],
            ["ASYNC_GET", "1,99,3"],
        ]
        r = simulate(queries)
        self.assertEqual(r[3], "name=task_one;name=task_two;name=task_three")
        self.assertEqual(r[4], "name=task_one;task not found;name=task_three")


if __name__ == "__main__":
    unittest.main()
