def case_safe_column(col: str, real_columns: list) -> str:
    """
    Map a logical column name to the real column name in the table, preserving case, for SQL.
    """
    for actual in real_columns:
        if actual.lower() == col.lower():
            return f'"{actual}"'
    return f'"{col}"'
