# database/connection.py
import os
import asyncio
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    def __init__(self):
        self.engine = None
        self.async_session = None
        self._setup_connection()
    
    def _setup_connection(self):
        db_url = URL.create(
            drivername="postgresql+asyncpg",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME"),
        )
        self.engine = create_async_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        try:
            async with self.async_session() as session:
                result = await session.execute(text("SELECT 1 as test"))
                test_result = result.fetchone()
                if test_result and test_result.test == 1:
                    return True, None
                else:
                    return False, "Connection test failed - unexpected result"
        except Exception as e:
            return False, f"Database connection failed: {e}"

    async def execute_query(self, sql_query: str) -> Tuple[bool, Any, Optional[str], int]:
        try:
            async with self.async_session() as session:
                await session.execute(text("SET statement_timeout = '30s'"))
                result = await session.execute(text(sql_query))
                rows = result.fetchall()
                cols = result.keys()
                data = [dict(zip(cols, row)) for row in rows] if rows else []
                if len(data) > 1000:
                    data = data[:1000]
                return True, data, None, 200
        except Exception as e:
            return False, None, str(e), 400

    async def get_column_names(self, table_name: str) -> list:
        """
        Returns the actual column names for a table, preserving their case.
        """
        async with self.async_session() as session:
            query = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
            """
            result = await session.execute(text(query))
            return [row[0] for row in result.fetchall()]

    async def close(self):
        if self.engine:
            await self.engine.dispose()