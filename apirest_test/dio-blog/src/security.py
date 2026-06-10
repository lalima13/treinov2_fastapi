import time
from typing import Annotated
from uuid import uuid4

import jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel

SECRET = "my-secret"
ALGORITHM = "HS256"


class AccessToken(BaseModel):
    iss: str
    sub: str 
    exp: float
    iat: float
    nbf: float
    jti: str


# Representa o token já decodificado (payload)
class JWTToken(BaseModel):
    access_token: AccessToken


# Representa a resposta do login (string do token)
class JWTResponse(BaseModel):
    access_token: str


def sign_jwt(user_id: int) -> JWTResponse:
    now = time.time()
    payload = {
        "iss": "curso-fastapi.com.br",
        "sub": str(user_id),  # ← Converter para string
        "aud": "curso-fastapi",
        "exp": now + (60 * 30),
        "iat": now,
        "nbf": now,
        "jti": uuid4().hex,
    }
    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    return JWTResponse(access_token=token)  # <-- retorna a string


async def decode_jwt(token: str) -> JWTToken | None:
    try:
        # jwt.decode já valida exp, nbf, aud automaticamente
        decoded_token = jwt.decode(
            token,
            SECRET,
            audience="curso-fastapi",
            algorithms=[ALGORITHM]
        )
        # decoded_token já é o dict do payload, encapsula em JWTToken
        return JWTToken(access_token=AccessToken(**decoded_token))
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


class JWTBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> JWTToken:
        authorization = request.headers.get("Authorization", "")
        scheme, _, credentials = authorization.partition(" ")

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization code."
            )

        if scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme."
            )

        payload = await decode_jwt(credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token."
            )
        return payload


async def get_current_user(
    token: Annotated[JWTToken, Depends(JWTBearer())]
) -> dict[str, int]:
    return {"user_id": int(token.access_token.sub)}  # ← Converter de volta para int


def login_required(
    current_user: Annotated[dict[str, int], Depends(get_current_user)]
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return current_user