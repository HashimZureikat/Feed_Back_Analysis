from azure.storage.blob import BlobServiceClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_blob_service_client():
    try:
        return BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
    except Exception as e:
        logger.error(f"Error connecting to Azure Blob Storage: {str(e)}")
        return None

def upload_file(file_content, blob_name):
    blob_service_client = get_blob_service_client()
    if not blob_service_client:
        return False
    try:
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_TRANSCRIPT)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(file_content, overwrite=True)
        return True
    except Exception as e:
        logger.error(f"Error uploading file to Azure Blob Storage: {str(e)}")
        return False

def download_file(blob_name):
    blob_service_client = get_blob_service_client()
    if not blob_service_client:
        return None
    try:
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_TRANSCRIPT)
        blob_client = container_client.get_blob_client(blob_name)
        return blob_client.download_blob().readall().decode('utf-8')
    except Exception as e:
        logger.error(f"Error downloading file from Azure Blob Storage: {str(e)}")
        return None

def list_blobs():
    blob_service_client = get_blob_service_client()
    if not blob_service_client:
        return []
    try:
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_TRANSCRIPT)
        return [blob.name for blob in container_client.list_blobs()]
    except Exception as e:
        logger.error(f"Error listing blobs in Azure Blob Storage: {str(e)}")
        return []