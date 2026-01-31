from .celery_worker import celery_app
import time

@celery_app.task
def example_task(duration: int):
    time.sleep(duration)
    return f"Task completed after {duration} seconds"

@celery_app.task
def add_numbers(x: int, y: int):
    """Simple test task that adds two numbers"""
    time.sleep(2)  # Simulate some work
    return {"result": x + y, "message": f"{x} + {y} = {x + y}"}