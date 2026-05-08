"""Google Secret Manager helper for the travel planner backend."""

from google.cloud import secretmanager


def get_secret(secret_id: str, project_id: str = "YOUR_PROJECT_ID") -> str:
    """Fetch the latest version of a secret from Google Secret Manager.

    Args:
        secret_id: The ID of the secret to retrieve.
        project_id: The GCP project that owns the secret.

    Returns:
        The secret payload decoded as a UTF-8 string.

    Raises:
        RuntimeError: If the secret cannot be fetched for any reason.
    """
    try:
        client: secretmanager.SecretManagerServiceClient = (
            secretmanager.SecretManagerServiceClient()
        )
        name: str = (
            f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        )
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("utf-8")
    except Exception as exc:
        raise RuntimeError(
            f"Failed to fetch secret '{secret_id}' from project '{project_id}': {exc}"
        ) from exc
