import threading
import asyncio


def simulate(queries):
    tasks = {}
    next_id = [1]
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

        if op == "ADD_TASK":
            results.append(_add(q[1]))

        elif op == "GET_TASK":
            tid = int(q[1])
            results.append(f"name={tasks[tid]['name']}" if tid in tasks else "task not found")

        elif op == "DELETE_TASK":
            tid = int(q[1])
            if tid in tasks:
                del tasks[tid]
                results.append("deleted")
            else:
                results.append("task not found")

        elif op == "LIST_TASKS":
            if not tasks:
                results.append("no tasks")
            else:
                ordered = sorted(tasks.items(), key=lambda x: x[0])
                results.append(",".join(t["name"] for _, t in ordered))

        elif op == "SEARCH_TASKS":
            prefix = q[1]
            matches = sorted(t["name"] for t in tasks.values() if t["name"].startswith(prefix))
            results.append(",".join(matches) if matches else "no results")

        elif op == "UPDATE_TASK":
            tid = int(q[1])
            if tid in tasks:
                tasks[tid]["name"] = q[2]
                results.append("updated")
            else:
                results.append("task not found")

        elif op == "SET_PRIORITY":
            tid = int(q[1])
            if tid in tasks:
                tasks[tid]["priority"] = int(q[2])
                results.append("updated")
            else:
                results.append("task not found")

        elif op == "LIST_BY_PRIORITY":
            ordered = sorted(tasks.values(), key=lambda t: (-t["priority"], t["name"]))
            results.append(",".join(t["name"] for t in ordered) if ordered else "no tasks")

        elif op == "ADD_TAG":
            tid = int(q[1])
            if tid in tasks:
                tasks[tid]["tags"].add(q[2])
                results.append("tagged")
            else:
                results.append("task not found")

        elif op == "SEARCH_BY_TAG":
            tag = q[1]
            matches = sorted(t["name"] for t in tasks.values() if tag in t["tags"])
            results.append(",".join(matches) if matches else "no results")

        elif op == "SET_DUE":
            tid = int(q[1])
            if tid in tasks:
                tasks[tid]["due"] = int(q[2])
                results.append("updated")
            else:
                results.append("task not found")

        elif op == "LIST_OVERDUE":
            ts = int(q[1])
            overdue = [(tid, t) for tid, t in tasks.items() if t["due"] is not None and t["due"] < ts]
            if overdue:
                overdue.sort(key=lambda x: x[1]["due"])
                results.append(",".join(t["name"] for _, t in overdue))
            else:
                results.append("no tasks")

        elif op == "SET_STATUS":
            tid = int(q[1])
            if tid in tasks:
                tasks[tid]["status"] = q[2]
                results.append("updated")
            else:
                results.append("task not found")

        elif op == "LIST_BY_STATUS":
            status = q[1]
            matches = sorted(t["name"] for t in tasks.values() if t["status"] == status)
            results.append(",".join(matches) if matches else "no tasks")

        elif op == "CONCURRENT_ADD":
            names = q[1].split(",")
            new_ids = []

            def add_one(name):
                result = _add(name)
                with lock:
                    new_ids.append(int(result.split()[1]))

            threads = [threading.Thread(target=add_one, args=(n,)) for n in names]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            results.append(",".join(str(i) for i in sorted(new_ids)))

        elif op == "ASYNC_GET":
            ids = [int(i) for i in q[1].split(",")]

            async def fetch_all(id_list):
                async def fetch(tid):
                    return f"name={tasks[tid]['name']}" if tid in tasks else "task not found"
                return await asyncio.gather(*[fetch(tid) for tid in id_list])

            fetch_results = asyncio.run(fetch_all(ids))
            results.append(";".join(fetch_results))

    return results
