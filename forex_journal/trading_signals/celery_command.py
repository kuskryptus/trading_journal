import subprocess
import psutil
import os
import logging
import time

log = logging.getLogger(__name__)


def start_celery_worker_pair():
    
    command = "start cmd /k celery -A forex_journal worker -l INFO --pool=threads -Q notification-pair --concurrency=1"

    # Start Celery worker process
    worker_process = subprocess.Popen(command, shell=True)
    print("Celery worker started. PID:", worker_process.pid)

    return worker_process


def restart_celery_worker(queue_name):
    stop_celery_workers(queue_name)

    command = f"start cmd /c celery -A forex_journal worker -l INFO --pool=threads -Q {queue_name} --concurrency=2"
    subprocess.call(command, shell=True)


def stop_celery_workers(queue_name):
    # Iterate over all processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):

        # Check if the process name contains 'celery' and if the command line contains the queue name
        if 'celery' in proc.info['name'] and queue_name in ' '.join(proc.info['cmdline']):
            log.info(f"PID: {proc.info['pid']}, Name: {proc.info['name']}")
            # Terminate the process
            proc.terminate()
            time.sleep(2)
            log.info(
                f"Celery worker for queue '{queue_name}' terminated. PID: {proc.info['pid']}"
            )


def restart_celery_beat():
    stop_celery_beat()
    start_celery_beat()


def start_celery_beat():
    command = "start cmd /c celery -A forex_journal beat -l debug"
    # Check if celery beat is already running
    for process in psutil.process_iter():
        if "celery" in process.name().lower() and "beat" in process.cmdline():
            print("Celery Beat is already running. PID:", process.pid)
            stop_celery_beat()
            return None

    # Command to start the celery beat
    command = "start cmd /c celery -A forex_journal beat -l debug"
    subprocess.run(command, shell=True)
    log.info("Celery Beat started.")


def stop_celery_beat():
    # Find the PID of the Celery beat process
    beat_pid = None
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        if "celery" in process.name().lower() and "beat" in process.cmdline():
            beat_pid = process.pid
            break

    if beat_pid:
        # Command to stop the Celery beat process based on the identified PID
        subprocess.run(["taskkill", "/f", "/pid", str(beat_pid)], shell=True)
        log.info("Celery beat process stopped.")
    else:
        # The Celery beat process was not found
        log.info("Celery beat process not found, nothing to stop.")


""" def show_celery_processes():
    while True:
        log.info("Active Celery Processes:")
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
           if "celery" in proc.name().lower() and "beat" in proc.cmdline():
               log.info(proc.name)
        time.sleep(2) """
