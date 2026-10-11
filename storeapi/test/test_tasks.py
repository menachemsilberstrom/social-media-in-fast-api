import httpx
import pytest

from storeapi.tasks import APIResponseError, send_simple_email


@pytest.mark.anyio
async def test_send_simple_email(mock_httpx_client):
    # Provide a mock JSON response so response.json() doesn't fail
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200,
        json={"message": "Queued. Thank you."},
        request=httpx.Request("POST", "https://api.mailgun.net/v3/send"),
    )

    await send_simple_email(
        "test@example.com", "Hello, World!", "This is a test email."
    )
    mock_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_simple_email_api_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=500,
        content="",
        request=httpx.Request("POST", "https://api.mailgun.net/v3/send"),
    )

    with pytest.raises(APIResponseError):
        await send_simple_email("test@exsmple.net", "Test subject", "test body")
