# General

Reports are configured in the database in the `alma_export` schema. The tables are:

- `report`: General configuration
- `report_param`: Required parameters for report generation
- `report_sql_query`: SQL queries used to populate reports with data
- `report_report_sql_query`: Mapping table between the SQL queries and the general configuration

The folder containing the templates is configurable via the `alma_templates_base_dir` setting in the `env` file. The specified path must exist.

Path entries in `report` are relative to the language folders.


# Creating a new report

**1. Define the report configuration.**

- The meaning of the individual table columns can be derived from the comments in the table. Notes:
    - `context` specifies where the report is used. For the cadastral extract it is `standort`, and for the annual report it is `jahresbericht`.
    - `title` is the key to the translations, since the title is meant to be multilingual.
- Add any required parameters to the `report_param` table, which are needed to execute the SQL queries (see next point). For example, if the query is `select * from alma_export.jasper_view v where v.vflz_id=:vflz_id;`, then the parameter `vflz_id` must be stored in `report_param`.
- Add the SQL queries to the `report_sql_query` table. The syntax is standard SQL with one exception: parameters defined in the `report_param` table and required to evaluate the query must start with a `:`, as noted above (`:vflz_id`). The queries must have a unique `name`. The `worksheet_name` field is not always required; it is only needed for annual reports (see "2.2. Excel templates (for annual reports)").
- Add the translation for `report.title`

**2. Create the template.**

There are two types of templates:

**2.1. Jinja templates**

Create the template using the name defined in the report configuration. It is a Jinja template ([documentation link](https://jinja.palletsprojects.com/en/stable/templates/)). If the Jinja template includes resources, they must be placed in the `elements` subfolder.

The following points should be noted:
- In the template, the result of the SQL queries for the report configuration is accessed via the name defined in step 1. Individual columns of the query are accessed using dot notation. The output is always a list of rows, even if there is only a single row. For example, if the SQL query is `select vflz_flurname as vf from ...` and has the name `grunddaten`, then within the template it is accessed as `grunddaten[0].vf`.

**2.2. Excel templates (for annual reports)**

The Excel templates are stored in the `settings.templates_base_dir` folder. When creating the templates, ensure that a separate sheet is created for each configured `report_sql_query`. The sheet name must be specified in the `worksheet_name` column.

**3. Create the stylesheet.**
**4. Deploy to the server.**

# Generating the report

Reports are generated via the path `/api/report/{report_id}?language=<language>&<param-name>=<param-value>`

Example: `/api/report/1?language=de&vflz_id=1234`

Report configurations can generally be queried via the `reportConfigurations` query.


# Importing existing reports

In `include/import_report_configurations.sql`, there are migrations for predefined configurations including queries. These can be imported into the database via `make db-import-report-configurations` in the `db` folder.

# Multilingual support

Reports are created as multilingual, meaning there is one file for all languages.
The translations are accessed in the template through the variable `translations`. Individual translations are accessed using the key from the translation. For example, if there is a translation with the key (in the table: `msg_id`) `reports.foo`, it is accessed via `translations['report.foo']`.

The queries for translations are created like the other queries (see above), with the difference that the `is_translation_query` flag must be set.

It is possible to leave variables in the translations. This is done using placeholders.

Example: There is a translation "The report was created on {0}" with the msg_id `reports.foo`. In the template, the corresponding value is inserted into `{0}` via `translations.foo.format(....)`.
