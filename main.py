import os
from dotenv import load_dotenv

from datetime import datetime
from datetime import date

from todoist_api_python.api import TodoistAPI

load_dotenv()

WORKDAY_MINUTES = 720
BREATHING_ROOM = 30  # minutes of breathing room between tasks

class Task:
    def __init__(self, name, duration, due_date=None):
        self.name = name
        self.duration = duration  # in minutes
        self.due_date = due_date  # datetime object or None

API = TodoistAPI(os.getenv('API_KEY'))

tasks = []

try:
    fetchedTasks = API.get_tasks()
    for fetchedTask in fetchedTasks:#
        if fetchedTask.project_id == "2315867087" and fetchedTask.due.date == str(date.today()):
            tasks.append(Task(fetchedTask.content, 60, fetchedTask.due.date))
            
except Exception as error:
    print(error)

week = {
    "Monday": {"tasks": [], "total_minutes": 0},
    "Tuesday": {"tasks": [], "total_minutes": 0},
    "Wednesday": {"tasks": [], "total_minutes": 0},
    "Thursday": {"tasks": [], "total_minutes": 0},
    "Friday": {"tasks": [], "total_minutes": 0},
    "Saturday": {"tasks": [], "total_minutes": 0},
    "Sunday": {"tasks": [], "total_minutes": 0}
}

def can_accommodate_day(day, duration):
    return week[day]["total_minutes"] + duration + BREATHING_ROOM <= WORKDAY_MINUTES

def place_task_on_day(task, day):
    week[day]["tasks"].append({"name": task.name, "duration": task.duration})
    week[day]["total_minutes"] += task.duration

tasks.sort(key=lambda t: (t.due_date if t.due_date else datetime.max, t.duration))

for task in tasks:
    placed = False
    sorted_days = sorted(week.keys(), key=lambda d: week[d]["total_minutes"])
    for day in sorted_days:
        if can_accommodate_day(day, task.duration):
            place_task_on_day(task, day)
            placed = True
            break

# Display the Scheduled Tasks
for day, data in week.items():
    print(f"{day}:")
    for task in data["tasks"]:
        print(f"  - {task['name']} ({task['duration']} min)")
    print()
