from datetime import datetime
from typing import Self

import strawberry

from alma.protocols import AuditinProtocol, ErfassungMutationProtocol


@strawberry.type
class ErfassungMutation:
    erfassungs_datum: datetime | None
    erfasser: str | None
    mutations_datum: datetime | None
    mutierer: str | None

    @classmethod
    def from_db(cls, db_obj: ErfassungMutationProtocol | AuditinProtocol) -> Self:
        """Build ErfassungMutation from either an alma model (german audit
        columns via ErfassungMutationMixin) or a business_workflow_manager model
        (english audit columns via wm.AuditMixin)."""
        if isinstance(db_obj, ErfassungMutationProtocol):
            return cls(
                erfassungs_datum=db_obj.erfassungs_datum,
                erfasser=db_obj.erfasser,
                mutations_datum=db_obj.mutations_datum,
                mutierer=db_obj.mutierer,
            )
        else:
            return cls(
                erfassungs_datum=db_obj.created_at,
                erfasser=db_obj.created_by,
                mutations_datum=db_obj.updated_at,
                mutierer=db_obj.updated_by,
            )
