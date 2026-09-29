-- Extend translation uniqueness constraints to cover Benzinartige Kohlenwasserstoffe (code list 317)

alter table alma.translations
    drop constraint ex_code_c_cli_id_same_lang_stoff,
    drop constraint ex_code_c_cli_id_diff_lang_stoff;

alter table alma.translations
    add constraint ex_code_c_cli_id_same_lang_stoff exclude using gist (
        locale with =,
        (lower(msgstr)) with =
    ) where (
        msgid like 'code:%:%'
        and (string_to_array(msgid, ':'))[2]::integer between 301 and 317
    ),
    add constraint ex_code_c_cli_id_diff_lang_stoff exclude using gist (
        (lower(msgstr)) with =,
        (regexp_replace(msgid, '^code:', '')) with !=
    ) where (
        msgid like 'code:%:%'
        and (string_to_array(msgid, ':'))[2]::integer between 301 and 317
    );
