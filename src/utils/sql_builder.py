from src.utils.case_safe import case_safe_column

async def build_case_safe_select(db, table, select_cols, joins=None, where=None, limit=20):
    """
    Build a SELECT SQL statement that uses case-safe column references for any schema.
    - db: instance of DatabaseConnection
    - table: main table name
    - select_cols: list of columns to select (from main or joined tables)
    - joins: list of dicts: {table, on_main, on_join}
    - where: list of dicts: {table, column, operator, value}
    """
    main_cols = await db.get_column_names(table)
    sql_cols = []
    for col in select_cols:
        if '.' in col:
            tbl, c = col.split('.', 1)
            real_cols = await db.get_column_names(tbl)
            sql_cols.append(f'{tbl}.{case_safe_column(c, real_cols)}')
        else:
            sql_cols.append(case_safe_column(col, main_cols))
    sql = f'SELECT {", ".join(sql_cols)} FROM {table}'

    # handle joins
    if joins:
        for join in joins:
            jt = join["table"]
            on_main = join["on_main"]
            on_join = join["on_join"]
            main_on = case_safe_column(on_main, main_cols)
            join_cols = await db.get_column_names(jt)
            join_on = case_safe_column(on_join, join_cols)
            sql += f' JOIN {jt} ON {table}.{main_on} = {jt}.{join_on}'

    # handle where
    if where:
        conds = []
        for cond in where:
            tbl = cond["table"]
            col = cond["column"]
            op = cond["operator"]
            val = cond["value"]
            tbl_cols = await db.get_column_names(tbl)
            conds.append(f"{tbl}.{case_safe_column(col, tbl_cols)} {op} {val}")
        sql += " WHERE " + " AND ".join(conds)

    if limit:
        sql += f" LIMIT {limit}"
    return sql
