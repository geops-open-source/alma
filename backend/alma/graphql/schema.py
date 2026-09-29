from collections.abc import Iterable
from typing import Any

import strawberry
from anyio.to_thread import run_sync
from strawberry.schema.config import StrawberryConfig
from strawberry.types import ExecutionResult
from strawberry.types.graphql import OperationType

from . import scalars as alma_scalars
from .mutation import Mutation
from .query import Query
from .types import workflow


class SyncExecutionSchema(strawberry.Schema):
    """Schema that executes resolvers synchronously in the anyio thread pool"""

    async def execute(
        self,
        query: str | None,
        variable_values: dict[str, Any] | None = None,
        context_value: Any | None = None,
        root_value: Any | None = None,
        operation_name: str | None = None,
        allowed_operation_types: Iterable[OperationType] | None = None,
        operation_extensions: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        return await run_sync(
            self.execute_sync,
            query,
            variable_values,
            context_value,
            root_value,
            operation_name,
            allowed_operation_types,
            operation_extensions,
        )


schema = SyncExecutionSchema(
    query=Query,
    mutation=Mutation,
    config=StrawberryConfig(
        scalar_map={
            alma_scalars.GeoJSONPoint: alma_scalars.GeoJSONPointScalar,
            alma_scalars.GeoJSONMultiPolygon: alma_scalars.GeoJSONMultiPolygonScalar,
            alma_scalars.GeoJSONPointOrMultiPolygon: alma_scalars.GeoJSONPointOrMultiPolygonScalar,
            alma_scalars.GeoJSONFeatureCollection: alma_scalars.GeoJSONFeatureCollectionScalar,
            alma_scalars.GeoJSONLineString: alma_scalars.GeoJSONLineStringScalar,
            alma_scalars.JSONTranslation: alma_scalars.JSONTranslationScalar,
            alma_scalars.FormularFelder: alma_scalars.FormularFelderScalar,
            alma_scalars.FormularEingaben: alma_scalars.FormularEingabenScalar,
        }
    ),
    types=[
        workflow.Prozess,
        workflow.Aufgabe,
        workflow.Dokument,
        workflow.Formular,
        workflow.Notiz,
    ],
)
