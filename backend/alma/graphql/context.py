from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime

import httpx2
from business_workflow_manager.manager import WorkflowManager
from sqlalchemy import event
from sqlalchemy.orm import Session
from strawberry.fastapi import BaseContext

from ..keycloak import get_keycloak_client
from ..models.auth import User


class Context(BaseContext):
    def __init__(
        self,
        db: Session,
        user: User,
        workflow_manager: WorkflowManager,
        keycloak_maker: Callable[
            [], AbstractContextManager[httpx2.Client]
        ] = get_keycloak_client,
    ):
        self.db = db
        self.user = user
        self.keycloak_maker = keycloak_maker
        self.workflow_manager = workflow_manager

        @event.listens_for(db, "before_flush")
        def receive_before_flush(  # type: ignore[ARG001]
            session: Session, flush_context: object, instances: object
        ):
            now = datetime.now()
            for obj in session.new:
                # alma models (ErfassungMutationMixin, german columns)
                if hasattr(obj, "erfasser"):
                    obj.erfasser = user.username
                if hasattr(obj, "erfassungs_datum"):
                    obj.erfassungs_datum = now
                # business_workflow_manager models (wm.AuditMixin, english columns)
                if hasattr(obj, "created_by"):
                    obj.created_by = user.username
                if hasattr(obj, "created_at"):
                    obj.created_at = now

            for obj in session.dirty:
                if session.is_modified(obj):
                    # alma models
                    if hasattr(obj, "mutierer"):
                        obj.mutierer = user.username
                    if hasattr(obj, "mutations_datum"):
                        obj.mutations_datum = now
                    # business_workflow_manager models
                    if hasattr(obj, "updated_by"):
                        obj.updated_by = user.username
                    if hasattr(obj, "updated_at"):
                        obj.updated_at = now
