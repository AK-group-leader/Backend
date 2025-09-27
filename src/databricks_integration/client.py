"""
Databricks client for data processing and ML operations
"""

import logging
from typing import Dict, Any, List, Optional
from databricks import sql
from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession

from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabricksClient:
    """Databricks client for data operations"""

    def __init__(self):
        """Initialize Databricks client"""
        self.host = settings.DATABRICKS_HOST
        self.token = settings.DATABRICKS_TOKEN
        self.cluster_id = settings.DATABRICKS_CLUSTER_ID

        if not all([self.host, self.token]):
            logger.warning("Databricks credentials not configured")
            self._enabled = False
        else:
            self._enabled = True
            self._init_connections()

    def _init_connections(self):
        """Initialize Databricks connections"""
        try:
            # SQL connection
            self.sql_connection = sql.connect(
                server_hostname=self.host,
                http_path=f"/sql/1.0/warehouses/{self.cluster_id}",
                access_token=self.token
            )

            # Spark session
            self.spark = DatabricksSession.builder \
                .remote(
                    host=self.host,
                    token=self.token,
                    cluster_id=self.cluster_id
                ) \
                .getOrCreate()

            logger.info("Databricks connections initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize Databricks connections: {str(e)}")
            self._enabled = False

    def is_enabled(self) -> bool:
        """Check if Databricks is enabled and configured"""
        return self._enabled

    async def execute_sql(self, query: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SQL query on Databricks"""
        if not self.is_enabled():
            raise Exception("Databricks not configured")

        try:
            cursor = self.sql_connection.cursor()
            cursor.execute(query, parameters or {})

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch results
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results

        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            raise

    async def read_table(self, table_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Read data from Databricks table"""
        if not self.is_enabled():
            raise Exception("Databricks not configured")

        try:
            query = f"SELECT * FROM {table_name}"
            if limit:
                query += f" LIMIT {limit}"

            return await self.execute_sql(query)

        except Exception as e:
            logger.error(f"Failed to read table {table_name}: {str(e)}")
            raise

    async def write_dataframe(self, df, table_name: str, mode: str = "overwrite"):
        """Write DataFrame to Databricks table"""
        if not self.is_enabled():
            raise Exception("Databricks not configured")

        try:
            df.write.mode(mode).saveAsTable(table_name)
            logger.info(f"DataFrame written to table {table_name}")

        except Exception as e:
            logger.error(
                f"Failed to write DataFrame to table {table_name}: {str(e)}")
            raise

    async def create_table(self, table_name: str, schema: str):
        """Create table in Databricks"""
        if not self.is_enabled():
            raise Exception("Databricks not configured")

        try:
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
            await self.execute_sql(query)
            logger.info(f"Table {table_name} created successfully")

        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            raise

    async def run_ml_pipeline(self, pipeline_name: str, parameters: Dict[str, Any]):
        """Run ML pipeline on Databricks"""
        if not self.is_enabled():
            raise Exception("Databricks not configured")

        try:
            # TODO: Implement ML pipeline execution
            logger.info(
                f"Running ML pipeline {pipeline_name} with parameters {parameters}")

            # Placeholder for actual ML pipeline execution
            return {
                "pipeline_name": pipeline_name,
                "status": "completed",
                "parameters": parameters
            }

        except Exception as e:
            logger.error(f"ML pipeline execution failed: {str(e)}")
            raise

    def close(self):
        """Close Databricks connections"""
        if hasattr(self, 'sql_connection'):
            self.sql_connection.close()

        if hasattr(self, 'spark'):
            self.spark.stop()

        logger.info("Databricks connections closed")


# Global Databricks client instance
databricks_client = DatabricksClient()
