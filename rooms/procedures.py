from django.db import connection


def sql_func(func):
    """Call or create function in sql

    Args:
        args - list of arguments to calling procedure with;
        use_dbo - boolean, set True if procedure or function was not created.
    """

    def wraps(*, use_dbo=False):
        lookup_name = func.__name__
        with connection.cursor() as cursor:
            if use_dbo:
                return cursor.execute(func().format(lookup_name))
            cursor.execute('select * from {lookup_name}();'.format(lookup_name=lookup_name))
            cols = [col[0] for col in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    return wraps


@sql_func
def select_filtered_rooms():
    return """
        create or replace function {0}()
            RETURNS TABLE
                    (
                        id               integer,
                        title            varchar,
                        description      varchar,
                        type             varchar,
                        capacity         integer,
                        occupied         integer,
                        occupied_tables  integer,
                        capacity_tables  integer,
                        occupied_meeting integer,
                        capacity_meeting integer
                    )
        as
        $$
        BEGIN
            return query
                select r.id,
                       r.title,
                       r.description::varchar(256),
                       r.type::varchar(64),
                       (select count(*) from tables_table)::integer                              as "capacity",
                       (select count(*) from tables_table t where t.is_occupied = True)::integer as "occupied",
                       (select case
                                   when r.type = 'Рабочее место'
                                       then (select count(*) from tables_table t where t.is_occupied = True)
                                   else 0
                                   END)::integer                                                 as "occupied_tables",
                       (select case
                                   when r.type = 'Рабочее место' then (select count(*) from tables_table)
                                   else 0
                                   END)::integer                                                 as "capacity_tables",
                       (select case
                                   when r.type = 'Переговорная'
                                       then (select count(*) from tables_table t where t.is_occupied = True)
                                   else 0
                                   END)::integer                                                 as "occupied_meeting",
                       (select case
                                   when r.type = 'Переговорная' then (select count(*) from tables_table)
                                   else 0
                                   END)::integer                                                 as "capacity_meeting"
                from rooms_room r;
        END ;
        $$ language plpgsql;
        """
