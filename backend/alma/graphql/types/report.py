from typing import TYPE_CHECKING, Self

import strawberry

from alma.graphql.utils.schema import to_id
from alma.models import report as report_models

if TYPE_CHECKING:
    ReportContext = report_models.ReportContext
    ParamType = report_models.ParamType
else:
    ReportContext = strawberry.enum(report_models.ReportContext)
    ParamType = strawberry.enum(report_models.ParamType)


@strawberry.type
class ReportParamType:
    name: str
    param_type: ParamType

    @classmethod
    def from_db(cls, obj: report_models.ReportParam) -> Self:
        return cls(name=obj.name, param_type=obj.type)


@strawberry.type
class ReportConfigurationType:
    report_id: strawberry.ID
    params: list[ReportParamType]
    title: str

    @classmethod
    def from_db(cls, obj: report_models.Report) -> Self:
        return cls(
            report_id=to_id(obj.report_id),
            params=[ReportParamType.from_db(param) for param in obj.parameters],
            title=obj.title,
        )
