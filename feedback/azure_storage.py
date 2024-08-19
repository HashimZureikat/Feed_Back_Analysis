from azure.storage.blob import BlobServiceClient
from django.conf import settings

def get_blob_service_client():
    return BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)

def upload_file(file_content, blob_name):
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_TRANSCRIPT)
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file_content, overwrite=True)

def download_file(blob_name):
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_TRANSCRIPT)
    blob_client = container_client.get_blob_client(blob_name)
    return blob_client.download_blob().readall().decode('utf-8')

def list_blobs():
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_TRANSCRIPT)
    return [blob.name for blob in container_client.list_blobs()]