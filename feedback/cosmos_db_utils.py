from azure.cosmos import CosmosClient, PartitionKey
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CosmosDBManager:
    def __init__(self):
        self.client = CosmosClient(settings.COSMOS_DB['ENDPOINT'], settings.COSMOS_DB['PRIMARY_KEY'])
        self.database = self.client.get_database_client(settings.COSMOS_DB['DATABASE'])
        self.container = self.database.get_container_client(settings.COSMOS_DB['CONTAINER'])

    def store_sentiment_result(self, feedback_data):
        try:
            result = self.container.create_item(body=feedback_data)
            logger.info(f"Stored sentiment result: {result['id']}")
            return result
        except Exception as e:
            logger.error(f"Error storing sentiment result: {str(e)}")
            raise

    def get_sentiment_results(self, query):
        try:
            return list(self.container.query_items(query=query, enable_cross_partition_query=True))
        except Exception as e:
            logger.error(f"Error querying sentiment results: {str(e)}")
            raise

    def store_feedback(self, feedback_data):
        try:
            result = self.container.create_item(body=feedback_data)
            logger.info(f"Stored feedback: {result['id']}")
            return result
        except Exception as e:
            logger.error(f"Error storing feedback: {str(e)}")
            raise

cosmos_db = CosmosDBManager()