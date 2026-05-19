import threading
import asyncio


def simulate(queries):
    """
    Process a list of queries against an in-memory task manager.

    Each query is a list: [OPERATION, arg1, arg2, ...].
    Returns a list of result strings, one per query.

    Operations by level
    -------------------
    Level 1  ADD_TASK name            → "added {id}"
             GET_TASK id              → "name={name}" | "task not found"
             DELETE_TASK id           → "deleted" | "task not found"

    Level 2  LIST_TASKS               → "n1,n2,..." (insertion order) | "no tasks"
             SEARCH_TASKS prefix      → "n1,n2,..." (alphabetical) | "no results"
             UPDATE_TASK id name      → "updated" | "task not found"

    Level 3  SET_PRIORITY id priority → "updated" | "task not found"
             LIST_BY_PRIORITY         → "n1,n2,..." (priority desc, name asc)
             ADD_TAG id tag           → "tagged" | "task not found"
             SEARCH_BY_TAG tag        → "n1,n2,..." (alphabetical) | "no results"

    Level 4  SET_DUE id timestamp     → "updated" | "task not found"
             LIST_OVERDUE timestamp   → "n1,n2,..." (due asc) | "no tasks"
             SET_STATUS id status     → "updated" | "task not found"
             LIST_BY_STATUS status    → "n1,n2,..." (alphabetical) | "no tasks"

    Level 5  CONCURRENT_ADD names     → comma-separated ids (ascending)
             names is a comma-separated string; use threading for parallelism

    Level 6  ASYNC_GET ids            → semicolon-separated results in id order
             ids is a comma-separated string; use asyncio for parallelism
    """
    tasks = {}       # id (int) -> dict with keys: name, priority, tags, due, status
    next_id = [1]    # list so inner functions can mutate it
    lock = threading.Lock()
    results = []

    def _add(name):
        with lock:
            tid = next_id[0]
            next_id[0] += 1
            tasks[tid] = {
                "name": name,
                "priority": 1,
                "tags": set(),
                "due": None,
                "status": "TODO",
            }
            return f"added {tid}"

    for q in queries:
        op = q[0]

        # ---- Level 1 ------------------------------------------------
        if op == "ADD_TASK":
            results.append(_add(q[1]))

        elif op == "GET_TASK":
            tid = int(q[1])
            if tid in tasks:
                results.append(f"name={tasks[tid]['name']}")
            else:
                results.append("task not found")

        elif op == "DELETE_TASK":
            tid = int(q[1])
            if tid in tasks:
                del tasks[tid]
                results.append("deleted")
            else:
                results.append("task not found")

        # ---- Level 2 ------------------------------------------------
        elif op == "LIST_TASKS":
            # TODO: return names in insertion order (task ids are assigned in order)
            pass

        elif op == "SEARCH_TASKS":
            # TODO: return names starting with q[1], alphabetical
            pass

        elif op == "UPDATE_TASK":
            # TODO: update name of task q[1] to q[2]
            pass

        # ---- Level 3 ------------------------------------------------
        elif op == "SET_PRIORITY":
            # TODO: set task q[1] priority to int(q[2])
            pass

        elif op == "LIST_BY_PRIORITY":
            # TODO: sort by priority descending, then name ascending
            pass

        elif op == "ADD_TAG":
            # TODO: add tag q[2] to task q[1]
            pass

        elif op == "SEARCH_BY_TAG":
            # TODO: return names that have tag q[1], alphabetical
            pass

        # ---- Level 4 ------------------------------------------------
        elif op == "SET_DUE":
            # TODO: set due timestamp (int) on task
            pass

        elif op == "LIST_OVERDUE":
            # TODO: tasks with due < int(q[1]), sorted by due ascending
            pass

        elif op == "SET_STATUS":
            # TODO: set status string on task (TODO / IN_PROGRESS / DONE)
            pass

        elif op == "LIST_BY_STATUS":
            # TODO: tasks with matching status, alphabetical
            pass

        # ---- Level 5 ------------------------------------------------
        elif op == "CONCURRENT_ADD":
            # TODO: split q[1] on "," and add each task in a separate thread
            # collect all new ids, return them sorted ascending as "id1,id2,..."
            pass

        # ---- Level 6 ------------------------------------------------
        elif op == "ASYNC_GET":
            # TODO: split q[1] on "," to get a list of int ids
            # fetch each task asynchronously with asyncio.gather
            # return results joined by ";" in the original id order
            pass

    return results
