from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


executors = {
    'default': ThreadPoolExecutor(10),
    'processpool': ProcessPoolExecutor(10)
}

# job_defaults = {
#     'coalesce': False,  # Объединение
#     'max_instances': 5
# }

scheduler = BackgroundScheduler(executors=executors)

