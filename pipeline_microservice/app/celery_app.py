from celery import Celery

def make_celery():
    celery = Celery(
        "pipeline_microservice",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0"
    )
    # Optionally: celery.config_from_object('your_config_module')
    return celery

celery_app = make_celery()