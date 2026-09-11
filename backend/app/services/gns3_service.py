import httpx
from app.config import GNS3_URL


class GNS3ServiceError(Exception):
    """Levée quand la communication avec GNS3 échoue."""
    pass


def get_projects() -> list[dict]:
    """Récupère la liste des projets GNS3."""
    url = f"{GNS3_URL}/v2/projects"
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as exc:
        raise GNS3ServiceError(f"Impossible de contacter GNS3 : {exc}")
    except httpx.HTTPStatusError as exc:
        raise GNS3ServiceError(f"GNS3 a renvoyé une erreur : {exc.response.status_code}")