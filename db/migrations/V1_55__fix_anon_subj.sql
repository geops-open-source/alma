do $$ begin
  if not '${skipAnonymize}' then
    security label for anon on column alma.subj.name is 'MASKED WITH FUNCTION anon.ternary(
        name = '''',
        '''',
        anon.fake_last_name()
    )';
  end if;
end $$;
