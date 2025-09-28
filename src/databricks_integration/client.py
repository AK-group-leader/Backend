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
        self.warehouse_id = settings.DATABRICKS_WAREHOUSE_ID

        if not all([self.host, self.token, self.warehouse_id]):
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
                http_path=f"/sql/1.0/warehouses/{self.warehouse_id}",
                access_token=self.token
            )
            logger.info(
                f"Databricks SQL Warehouse connection initialized successfully (Warehouse ID: {self.warehouse_id})")

            # Spark sessions are not supported with serverless warehouses
            logger.info(
                "Spark sessions not available with serverless warehouses - using SQL only")
            self.spark = None
            self._spark_enabled = False

            logger.info(
                "Databricks serverless warehouse connection initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize Databricks connections: {str(e)}")
            self._enabled = False
            self._spark_enabled = False

    def is_enabled(self) -> bool:
        """Check if Databricks is enabled and configured"""
        return self._enabled

    def is_spark_enabled(self) -> bool:
        """Check if Spark session is enabled"""
        return getattr(self, '_spark_enabled', False)

    def execute_sql(self, query: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
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

    def read_table(self, table_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Read data from Databricks table"""
        if not self.is_enabled():
            raise Exception("Databricks not configured")

        try:
            query = f"SELECT * FROM {table_name}"
            if limit:
                query += f" LIMIT {limit}"

            return self.execute_sql(query)

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

    def create_table(self, table_name: str, schema: str):
        """Create table in Databricks"""
        if not self.is_enabled():
            raise Exception("Databricks not configured")

        try:
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
            self.execute_sql(query)
            logger.info(f"Table {table_name} created successfully")

        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            raise

    def run_ml_pipeline(self, pipeline_name: str, parameters: Dict[str, Any]):
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
        if hasattr(self, 'sql_connection') and self.sql_connection:
            self.sql_connection.close()

        if hasattr(self, 'spark') and self.spark and self.is_spark_enabled():
            self.spark.stop()

        logger.info("Databricks connections closed")


# Global Databricks client instance
databricks_client = DatabricksClient()
