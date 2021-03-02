from django_rq.queues import get_connection

from rq import cancel_job
from rq.command import send_kill_horse_command
from rq.exceptions import NoSuchJobError
from rq.worker import Worker, WorkerStatus


def delete_job(job_id):
    redis_conn = get_connection()
    workers = Worker.all(redis_conn)
    for worker in workers:
        if worker.state == WorkerStatus.BUSY and \
                worker.get_current_job_id() == str(job_id):
            send_kill_horse_command(redis_conn, worker.name)

    try:
        # remove from queue
        cancel_job(str(job_id), connection=redis_conn)
    except NoSuchJobError:
        pass
