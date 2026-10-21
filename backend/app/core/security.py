"""Section 5.4 & Section 7: Security, Authentication, Access Governance & RBAC Engine.

Implements:
1. PBKDF2-HMAC-SHA256 Password Security (with salt and constant-time verify).
2. HMAC-SHA256 JWT Token Management (creation, validation, expiration).
3. 4-Tier RBAC Guardrails & Dependencies (get_current_active_user, require_min_level).
4. Legacy & Backward Compatibility (get_current_user_role, mask_tier3_perspective).
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Callable
import logging

import jwt
from fastapi import Header, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.core.database import get_db

logger = logging.getLogger("security")

# JWT 설정
JWT_ALGORITHM = "HS256"
JWT_DEFAULT_EXPIRE_MINUTES = 60 * 24  # 24시간
oauth2_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# 1. PBKDF2 비밀번호 보안 서비스 (PasswordSecurityService)
# ---------------------------------------------------------------------------
class PasswordSecurityService:
    """사내 폐쇄망 환경을 위한 무의존성 표준 PBKDF2-HMAC-SHA256 솔팅 암호화."""

    ITERATIONS = 100_000

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        """32바이트 솔트 생성 및 PBKDF2-HMAC-SHA256 해시 생성."""
        salt = secrets.token_hex(16)  # 32글자 hex salt
        dk = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=plain_password.encode("utf-8"),
            salt=salt.encode("utf-8"),
            iterations=cls.ITERATIONS
        )
        return f"{salt}${dk.hex()}"

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """일정 시간 비교(constant-time)로 타이밍 공격을 방어하며 암호 검증."""
        try:
            salt, hash_val = hashed_password.split("$", 1)
            dk = hashlib.pbkdf2_hmac(
                hash_name="sha256",
                password=plain_password.encode("utf-8"),
                salt=salt.encode("utf-8"),
                iterations=cls.ITERATIONS
            )
            return hmac.compare_digest(dk.hex(), hash_val)
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False


# ---------------------------------------------------------------------------
# 2. JWT 토큰 매니저 서비스 (TokenManagerService)
# ---------------------------------------------------------------------------
class TokenManagerService:
    """HMAC-SHA256 기반 사내 JWT 서명 발급 및 위조/만료 검증 매니저."""

    @classmethod
    def create_access_token(
        cls,
        subject: str,
        claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(minutes=JWT_DEFAULT_EXPIRE_MINUTES))
        payload = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
        if claims:
            payload.update(claims)
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    @classmethod
    def decode_access_token(cls, token: str) -> Dict[str, Any]:
        """토큰 위조, 서명 불일치, 만료 여부를 판별하여 페이로드 반환."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "TOKEN_EXPIRED", "message": "인증 토큰이 만료되었습니다. 다시 로그인해주세요."},
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": f"유효하지 않은 인증 토큰입니다: {str(e)}"},
                headers={"WWW-Authenticate": "Bearer"}
            )


# ---------------------------------------------------------------------------
# 3. FastAPI 인가 가드레일 & 의존성 주입 (Section 7.6)
# ---------------------------------------------------------------------------
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_bearer_scheme),
    db: AsyncSession = Depends(get_db)
):
    """토큰이 있으면 유저를 반환하고, 없으면 None을 반환하는 선택적 주입."""
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = TokenManagerService.decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        from backend.app.models.entities import UserModel
        user = await db.get(UserModel, user_id)
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_bearer_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Bearer JWT 토큰 유효성을 엄격히 검증하여 사내 유저 엔티티를 반환."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_TOKEN", "message": "인증 토큰(Bearer Token)이 누락되었습니다."},
            headers={"WWW-Authenticate": "Bearer"}
        )
    payload = TokenManagerService.decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "토큰 식별자(sub)가 유효하지 않습니다."},
            headers={"WWW-Authenticate": "Bearer"}
        )

    from backend.app.models.entities import UserModel
    user = await db.get(UserModel, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "존재하지 않는 사용자 계정입니다."},
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """활성화된 정상 사내 엔지니어인지 검증 (Soft Delete 퇴사자/차단자 403 거절)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_INACTIVE", "message": "비활성화 또는 퇴사 처리된 계정입니다."}
        )
    return current_user


def require_min_level(min_level: int) -> Callable:
    """지정된 권한 등급(Level 1~4) 미달 시 403 Forbidden을 선제 차단하는 팩토리 함수."""
    async def dependency(current_user = Depends(get_current_active_user)):
        if current_user.level < min_level:
            level_names = {
                1: "게스트 (Level 1)",
                2: "현장 엔지니어 (Level 2)",
                3: "수석 검토관 (Level 3)",
                4: "시스템 관리자 (Level 4)"
            }
            req_name = level_names.get(min_level, f"Level {min_level}")
            cur_name = level_names.get(current_user.level, f"Level {current_user.level}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_LEVEL",
                    "message": f"요청을 수행하기 위한 권한 등급이 부족합니다. (필요: {req_name}, 현재: {cur_name})"
                }
            )
        return current_user
    return dependency


# ---------------------------------------------------------------------------
# 4. 하위 호환성 유지 함수 (Section 5.4 Legacy)
# ---------------------------------------------------------------------------
def get_current_user_role(x_user_role: Optional[str] = Header(None, alias="X-User-Role")) -> str:
    """Extracts user role from X-User-Role header (default: chief_reviewer)."""
    if not x_user_role:
        return "chief_reviewer"
    role = x_user_role.strip().lower()
    if role in ["line_engineer", "chief_reviewer", "ontology_admin"]:
        return role
    return "chief_reviewer"


def mask_tier3_perspective(p_data: Dict[str, Any], user_role: str) -> Dict[str, Any]:
    """Masks Tier 3 sensitive manufacturing/yield metrics if user_role is line_engineer."""
    result = dict(p_data)

    if user_role == "line_engineer":
        result["isMasked"] = True
        result["is_masked"] = True
        result["maskReason"] = "Tier 3 양산 수율 및 결함 대외비 데이터 (일반 엔지니어 열람 제한)"
        result["mask_reason"] = "Tier 3 양산 수율 및 결함 대외비 데이터 (일반 엔지니어 열람 제한)"
        trend_text = (
            "상대적 경향성(Relative Trend): 본딩 가압력(145N) 제어 시 마이크로범프 크랙율 0.05% 이하로 안정화되며, "
            "피크 온도 상승에 따라 보이드 발생 위험이 지수 함수적으로 감소하는 양산 경향 확인됨."
        )
        result["relativeTrend"] = trend_text
        result["relative_trend"] = trend_text
        result["accessRequestCTA"] = "이 관점 상세 절대 수치 열람 권한 신청 ➔"
        result["access_request_cta"] = "이 관점 상세 절대 수치 열람 권한 신청 ➔"

        specs = result.get("specifications", [])
        masked_specs = []
        for s in specs:
            s_copy = dict(s)
            lbl = s_copy.get("label", "")
            if any(k in lbl for k in ["온도", "압력", "하중", "시간", "수율", "보이드", "두께"]):
                s_copy["value"] = "[🔒 대외비 마스킹]"
                s_copy["criteria"] = "보안 등급 기준 충족"
            masked_specs.append(s_copy)
        result["specifications"] = masked_specs

        narrative = result.get("context_narrative", "") or ""
        import re
        narrative = re.sub(r'\d+(?:\.\d+)?\s*(?:°C|℃|N|%|Torr|MPa|ms|s)', '[🔒 마스킹]', narrative)
        result["context_narrative"] = narrative
    else:
        result["isMasked"] = False

    return result
