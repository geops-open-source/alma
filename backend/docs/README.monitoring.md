# Monitoring

Code snippets that are to be monitored, save their state in the `alma_admin.task_status` table.
A schedule collects all of the states and sends it to ICINGA.

If a new code snippet is to be added to the monitoring, the process is as follows:

1. Identify code snippet.
2. Think of a **unique task status name**, henceforth called "unique_task_status_name"
3. Think of a category (import, export or application), henceforth called "task_category"
4. Implement as follows (check comments):

```python
from sqlalchemy.orm import Session
from alma.models.task_status import TaskCategory
from alma.monitoring import monitor_task_status

with monitor_task_status(session: Session, unique_task_name: str, task_category: TaskCategory):
    # your code goes here
```
