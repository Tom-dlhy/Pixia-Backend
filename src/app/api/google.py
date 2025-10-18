from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from asyncpg import Pool
from fastapi import APIRouter, HTTPException, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import jwt
from pydantic import BaseModel

from src.config import oauth_settings

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


class GoogleAuthPayload(BaseModel):
    credential: str


def create_access_token(
    data: Dict[str, str], expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a signed JWT for the application."""

    if not oauth_settings.JWT_SECRET_KEY:
        raise RuntimeError("JWT secret key is not configured")

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=oauth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode = data.copy()
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        oauth_settings.JWT_SECRET_KEY,
        algorithm=oauth_settings.JWT_ALGORITHM,
    )


def get_user_infos_from_google_token(id_token_str: str) -> Dict[str, Optional[str]]:
    """Verify the Google ID token and extract user information."""

    try:
        id_info = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            oauth_settings.OIDC_GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid credential: {exc}",
        ) from exc

    user_infos = {
        "sub": id_info.get("sub"),
        "email": id_info.get("email"),
        "given_name": id_info.get("given_name"),
        "family_name": id_info.get("family_name"),
        "picture": id_info.get("picture"),
        "locale": id_info.get("locale"),
    }

    if not user_infos.get("sub") or not user_infos.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google credential is missing required user information.",
        )

    return user_infos


async def upsert_user(
    pool: Pool,
    sub: str,
    email: str,
    given_name: Optional[str],
    family_name: Optional[str],
    picture: Optional[str],
    locale: Optional[str],
) -> Dict[str, Any]:
    """Ensure a user record exists, updating fields if the Google account already exists."""

    query = """
        INSERT INTO users (google_sub, email, given_name, family_name, picture, locale)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (google_sub)
        DO UPDATE SET 
            email = EXCLUDED.email,
            given_name = EXCLUDED.given_name,
            family_name = EXCLUDED.family_name,
            picture = EXCLUDED.picture,
            locale = EXCLUDED.locale
        RETURNING id, google_sub, email, given_name, family_name, picture, locale
    """

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(query, sub, email, given_name, family_name, picture, locale)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while upserting user: {exc}",
            ) from exc

    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database did not return user information.",
        )

    return dict(row)


@router.post("/google")
async def auth_google(request: Request, payload: GoogleAuthPayload):
    credential = payload.credential
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No credential provided."
        )

    user_infos = get_user_infos_from_google_token(credential)

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection pool is not available.",
        )

    db_user = await upsert_user(
        pool,
        sub=user_infos["sub"],
        email=user_infos["email"],
        given_name=user_infos.get("given_name"),
        family_name=user_infos.get("family_name"),
        picture=user_infos.get("picture"),
        locale=user_infos.get("locale"),
    )

    try:
        access_token = create_access_token(data={"sub": user_infos["email"]})
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "token": access_token,
        "user_id": db_user["id"],
        "google_sub": db_user["google_sub"],
        "email": db_user["email"],
        "given_name": db_user["given_name"],
        "family_name": db_user["family_name"],
        "picture": db_user["picture"],
        "locale": db_user["locale"],
    }
