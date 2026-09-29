from procrastinate import App, PsycopgConnector

from alma.settings import settings

app = App(
    connector=PsycopgConnector(
        conninfo=settings.database.url,
    ),
    # All modules that import "app" to register tasks must be added here
    import_paths=["alma.task_queue.tasks", "alma.task_queue.schedules"],
)
