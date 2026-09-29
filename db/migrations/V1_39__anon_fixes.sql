do $$ begin
  if not '${skipAnonymize}' then
        security label for anon on column alma.subj.name is 'MASKED WITH FUNCTION anon.ternary(
            anon.ternary(
                name = '''',
                '''',
                anon.fake_last_name()
            )
        )';
        security label for anon on column alma.subj.vorname is 'MASKED WITH FUNCTION anon.ternary(
            vorname = '''',
            '''',
            anon.fake_first_name()
        )';
        security label for anon on column alma.subj.taetigkeit is 'MASKED WITH FUNCTION anon.ternary(
            taetigkeit = '''',
            '''',
            anon.fake_company()
        )';
        security label for anon on column alma.wf_node.note is 'MASKED WITH FUNCTION anon.ternary(
            note is null,
            null,
            anon.lorem_ipsum( paragraphs := 1 )
        )';
  end if;
end $$;
