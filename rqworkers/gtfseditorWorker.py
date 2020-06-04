from rq import Worker


# Same worker called with rqworker by default, created to be able to call it in the same way
# as any other worker in the script for the service.
class GTFSEditorWorker(Worker):

    def __init__(self, queues, name=None, default_result_ttl=None, connection=None,
                 exc_handler=None, exception_handlers=None, default_worker_ttl=None,
                 job_class=None, queue_class=None):
        print("Initializing GTFSEditorWorker...")
        super(GTFSEditorWorker, self).__init__(queues, name=name, default_result_ttl=default_result_ttl,
                                               connection=connection, exc_handler=exc_handler,
                                               exception_handlers=exception_handlers,
                                               default_worker_ttl=default_worker_ttl, job_class=job_class,
                                               queue_class=queue_class)
        print("GTFSEditorWorker ready!")
