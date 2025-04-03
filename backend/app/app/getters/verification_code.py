from app.models.verification_code import VerificationCode
from app.schemas.verification_code import GettingVerificationCode


def get_verification_code(code: VerificationCode) -> GettingVerificationCode:
    return GettingVerificationCode(
        code=code.value
    )
