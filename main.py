import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, date, time
from todoist_api_python.api import TodoistAPI

load_dotenv()

WORKDAY_MINUTES = 720
BREATHING_ROOM = 30  # minutes of breathing room between tasks
WORKDAY_START_TIME = time(9, 0)  # start at 9 AM
DEFAULT_TASK_DURATION = 60  # default task duration in minutes
API = TodoistAPI(os.getenv('API_KEY'))

class Task:
    def __init__(self, name, priority, duration, due_date=None):
        self.name = name
        self.priority = priority
        self.duration = duration  # in minutes
        self.due_date = due_date  # datetime object or None

class TaskScheduler:
    def __init__(self, workday_minutes, breathing_room, workday_start_time):
        self.workday_minutes = workday_minutes
        self.breathing_room = breathing_room
        self.workday_start_time = workday_start_time
        self.tasks = []
        self.week = {}

    def fetch_tasks_on_day(self, day_date):
        gathered_tasks = []
        try:
            fetched_tasks = API.get_tasks()
            for fetched_task in fetched_tasks:
                if fetched_task.due and fetched_task.due.date == str(day_date):
                    due_datetime = datetime.fromisoformat(fetched_task.due.datetime) if fetched_task.due.datetime else datetime.combine(day_date, WORKDAY_START_TIME)
                    gathered_tasks.append(Task(fetched_task.content, fetched_task.priority, DEFAULT_TASK_DURATION, due_datetime))
        except Exception as error:
            print(error)
        return gathered_tasks

    def can_accommodate_between(self, existing_tasks, start_time, duration):
        end_time = start_time + timedelta(minutes=duration + BREATHING_ROOM)
        for task in existing_tasks:
            task_start = task.due_date
            task_end = task_start + timedelta(minutes=task.duration)
            if start_time < task_end and end_time > task_start:
                return False
        return True

    def find_time_slot(self, existing_tasks, duration, day):
        start_of_day = datetime.combine(day, WORKDAY_START_TIME)
        end_of_day = start_of_day + timedelta(minutes=WORKDAY_MINUTES)

        current_time = start_of_day

        for task in sorted(existing_tasks, key=lambda t: t.due_date):
            task_start = task.due_date
            task_end = task_start + timedelta(minutes=task.duration)

            if self.can_accommodate_between(existing_tasks, current_time, duration):
                return current_time

            current_time = task_end + timedelta(minutes=BREATHING_ROOM)

            if current_time + timedelta(minutes=duration) > end_of_day:
                break

        if current_time + timedelta(minutes=duration) <= end_of_day:
            return current_time

        return None  # No slot found

    def place_task_on_day(self, task, day):
        slot_time = self.find_time_slot(self.week[day]["tasks"], task.duration, day)
        if slot_time:
            task.due_date = slot_time
        else:
            end_time = self.week[day]["end_time"]
            start_time = end_time + timedelta(minutes=BREATHING_ROOM)
            task.due_date = start_time
        self.week[day]["tasks"].append(task)
        self.week[day]["tasks"].sort(key=lambda t: t.due_date)
        self.week[day]["time_remaining"] -= (task.duration + BREATHING_ROOM)
        self.week[day]["end_time"] = task.due_date + timedelta(minutes=task.duration)

    def can_accommodate_day(self, day, duration):
        return self.week[day]["time_remaining"] >= duration + BREATHING_ROOM

    def schedule_tasks(self):
        try:
            fetched_tasks = API.get_tasks()
            for fetched_task in fetched_tasks:
                if fetched_task.project_id == "2315867087" and fetched_task.due and fetched_task.due.date == str(date.today()):
                    due_datetime = datetime.fromisoformat(fetched_task.due.datetime) if fetched_task.due.datetime else datetime.combine(date.today(), WORKDAY_START_TIME)
                    self.tasks.append(Task(fetched_task.content, fetched_task.priority, DEFAULT_TASK_DURATION, due_datetime))
        except Exception as error:
            print(error)

        # sort tasks by due date first (treat None as latest possible date), then by duration
        self.tasks.sort(key=lambda t: (t.due_date if t.due_date else datetime.max, t.duration))

        current_day = date.today() + timedelta(days=1)
        for task in self.tasks:
            placed = False
            while not placed:
                if current_day not in self.week:
                    fetched_tasks = self.fetch_tasks_on_day(current_day)
                    self.week[current_day] = {"tasks": fetched_tasks, "time_remaining": WORKDAY_MINUTES, "end_time": datetime.combine(current_day, WORKDAY_START_TIME)}
                    for t in fetched_tasks:
                        self.week[current_day]["time_remaining"] -= t.duration
                        self.week[current_day]["end_time"] += timedelta(minutes=t.duration)

                if self.can_accommodate_day(current_day, task.duration):
                    self.place_task_on_day(task, current_day)
                    placed = True
                else:
                    current_day += timedelta(days=1)

    def print_schedule(self):
        if self.week == {}:
            print("no schedules have been queued")
            return
        for day, data in sorted(self.week.items()):
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

new_schedule = TaskScheduler(WORKDAY_MINUTES, BREATHING_ROOM, WORKDAY_START_TIME)
new_schedule.schedule_tasks()
new_schedule.print_schedule()