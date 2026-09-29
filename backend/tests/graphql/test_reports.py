from utils import make_report, make_report_param

from alma.models import report as report_models


def test_querying_public_report_configurations(session, run_query):
    report = make_report(session, report_models.ReportContext.STANDORT)
    vflz_id_param = make_report_param(
        session, report, "vflz_id", report_models.ParamType.INTEGER
    )
    date_param = make_report_param(
        session, report, "date", report_models.ParamType.DATE
    )
    query = """
    {
        reportConfigurations(context: STANDORT) {
            reportId
            params {
                name
                paramType
            }
            title
        }
    }
    """

    result = run_query(query)
    assert result.data["reportConfigurations"] == [
        {
            "reportId": str(report.report_id),
            "params": [
                {"name": vflz_id_param.name, "paramType": vflz_id_param.type},
                {"name": date_param.name, "paramType": date_param.type},
            ],
            "title": report.title,
        }
    ]
