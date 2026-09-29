"""Import settings from CSV into alma_admin.settings.

Before updating value_schema, validates that each existing setting value
conforms to the new schema (using jsonschema, same as update_instance_setting).
"""

import argparse

import jsonschema
import jsonschema.exceptions
import psycopg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-url", required=True, help="PostgreSQL connection URL")
    parser.add_argument(
        "--settings-csv", required=True, help="Path to settings CSV file"
    )
    args = parser.parse_args()

    with (
        psycopg.connect(args.db_url) as conn,
        open(args.settings_csv, "rb") as f,
    ):
        conn.execute("""
            create temporary table settings_import (
                key text,
                value text,
                category text,
                value_schema text
            )
        """)
        with conn.cursor().copy(
            "COPY settings_import FROM STDIN WITH (FORMAT csv, HEADER true)"
        ) as copy:
            while data := f.read(8192):
                copy.write(data)

        # For each existing setting where value_schema is changing, validate
        # that the current value still conforms to the new schema.
        rows = conn.execute("""
            select s.key, s.category, s.value, si.value_schema::jsonb as new_schema
            from alma_admin.settings s
            join settings_import si on s.key = si.key and s.category = si.category
            where si.value_schema::jsonb is distinct from s.value_schema
        """).fetchall()

        errors: list[str] = []
        for key, category, value, new_schema in rows:
            try:
                jsonschema.validate(instance=value, schema=new_schema)
            except jsonschema.exceptions.ValidationError as e:
                errors.append(f"  - {key} (category {category}): {e.message}")

        if errors:
            raise ValueError(
                "Settings value_schema validation failed:\n" + "\n".join(errors),
            )

        conn.execute("""
            insert into alma_admin.settings (key, value, value_schema, category)
            select key, value::jsonb, value_schema::jsonb, category from settings_import
            on conflict (key, category) do update set value_schema = excluded.value_schema::jsonb
        """)
        conn.commit()

    print("Settings imported successfully.")


if __name__ == "__main__":
    main()
