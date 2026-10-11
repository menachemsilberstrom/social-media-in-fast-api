import logging

import httpx

from storeapi.config import config

logger = logging.getLogger(__name__)

class APIResponseError(Exception):
    pass

async def send_simple_email(to_email: str, subject: str, body: str):
    logger.debug(
        "sending email",
        extra={"to_email": to_email, "subject": subject, "body": body},
    )
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
                auth=("api", config.MAILGUN_API_KEY),
                data={
                    "from": f"Mailgun Sandbox <postmaster@{config.MAILGUN_DOMAIN}>",
                    "to": to_email,
                    "subject": subject,
                    "text": body,
                },
            )
            response.raise_for_status()
            logger.debug(response.json(), extra={"to_email": to_email, "subject": subject})
        except httpx.HTTPError as err:
            logger.error(
                "Error sending email",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "body": body,
                    "error": str(err),
                },
            )
            raise APIResponseError(
                f"Error sending email: {err.response.text if err.response else str(err)}"
            ) from err


async def send_registration_email(to_email: str, confirmation_url: str):
    subject = "Confirm your email address"
    body = f"Please click the following link to confirm your email address: {confirmation_url}"
    return await send_simple_email(
        to_email=to_email,
        subject=subject,
        body=body
    )