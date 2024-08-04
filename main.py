import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, date, time
from todoist_api_python.api import TodoistAPI

load_dotenv()

WORKDAY_MINUTES = 720
BREATHING_ROOM = 30  # minutes of breathing room between tasks
WORKDAY_START_TIME = time(9, 0)  # start at 9 AM
DEFAULT_TASK_DURATION = 60  # default task duration in minutes

class Task:
    def __init__(self, name, priority, due_date=None):
        self.name = name
        self.priority = priority
        self.duration = DEFAULT_TASK_DURATION  # in minutes
        self.due_date = due_date  # datetime object or None

API = TodoistAPI(os.getenv('API_KEY'))

def fetch_tasks_on_day(day_date):
    gathered_tasks = []
    try:
        fetched_tasks = API.get_tasks()
        for fetched_task in fetched_tasks:
            if fetched_task.due and fetched_task.due.date == str(day_date):
                due_datetime = datetime.fromisoformat(fetched_task.due.datetime) if fetched_task.due.datetime else datetime.combine(day_date, WORKDAY_START_TIME)
                gathered_tasks.append(Task(fetched_task.content, fetched_task.priority, due_datetime))
    except Exception as error:
        print(error)
    return gathered_tasks

def can_accommodate_between(existing_tasks, start_time, duration):
    end_time = start_time + timedelta(minutes=duration + BREATHING_ROOM)
    for task in existing_tasks:
        task_start = task.due_date
        task_end = task_start + timedelta(minutes=task.duration)
        if start_time < task_end and end_time > task_start:
            return False
    return True

def find_time_slot(existing_tasks, duration, day):
    start_of_day = datetime.combine(day, WORKDAY_START_TIME)
    end_of_day = start_of_day + timedelta(minutes=WORKDAY_MINUTES)

    current_time = start_of_day

    for task in sorted(existing_tasks, key=lambda t: t.due_date):
        task_start = task.due_date
        task_end = task_start + timedelta(minutes=task.duration)

        if can_accommodate_between(existing_tasks, current_time, duration):
            return current_time

        current_time = task_end + timedelta(minutes=BREATHING_ROOM)

        if current_time + timedelta(minutes=duration) > end_of_day:
            break

    if current_time + timedelta(minutes=duration) <= end_of_day:
        return current_time

    return None  # No slot found

def place_task_on_day(task, day):
    slot_time = find_time_slot(week[day]["tasks"], task.duration, day)
    if slot_time:
        task.due_date = slot_time
    else:
        end_time = week[day]["end_time"]
        start_time = end_time + timedelta(minutes=BREATHING_ROOM)
        task.due_date = start_time
    week[day]["tasks"].append(task)
    week[day]["tasks"].sort(key=lambda t: t.due_date)
    week[day]["time_remaining"] -= (task.duration + BREATHING_ROOM)
    week[day]["end_time"] = task.due_date + timedelta(minutes=task.duration)

def can_accommodate_day(day, duration):
    return week[day]["time_remaining"] >= duration + BREATHING_ROOM

tasks = []

try:
    fetched_tasks = API.get_tasks()
    for fetched_task in fetched_tasks:
        if fetched_task.project_id == "2315867087" and fetched_task.due and fetched_task.due.date == str(date.today()):
            due_datetime = datetime.fromisoformat(fetched_task.due.datetime) if fetched_task.due.datetime else datetime.combine(date.today(), WORKDAY_START_TIME)
            tasks.append(Task(fetched_task.content, fetched_task.priority, due_datetime))
except Exception as error:
    print(error)

week = {}

# Sort tasks by due date first (treat None as latest possible date), then by duration
tasks.sort(key=lambda t: (t.due_date if t.due_date else datetime.max, t.duration))

current_day = date.today() + timedelta(days=1)
for task in tasks:
    placed = False
    while not placed:
        if current_day not in week:
            fetched_tasks = fetch_tasks_on_day(current_day)
            week[current_day] = {"tasks": fetched_tasks, "time_remaining": WORKDAY_MINUTES, "end_time": datetime.combine(current_day, WORKDAY_START_TIME)}
            for t in fetched_tasks:
                week[current_day]["time_remaining"] -= t.duration
                week[current_day]["end_time"] += timedelta(minutes=t.duration)

        if can_accommodate_day(current_day, task.duration):
            place_task_on_day(task, current_day)
            placed = True
        else:
            current_day += timedelta(days=1)

for day, data in sorted(week.items()):
    for task in data["tasks"]:
        try:
            # new_task = API.add_task(
            #     content=task.name,
            #     due_datetime=task.due_date,
            #     due_lang="en",
            #     project_id="2315867356",
            #     section_id="162229528",
            #     priority=task.priority,
            # )
            print(f"""
---TASK---
Title: {task.name}
Due: {str(task.due_date)}""")
        except Exception as error:
            print(error)
