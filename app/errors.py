from fastapi import HTTPException


def fail(status: int, code: str, message: str):
    raise HTTPException(status_code=status, detail={"code": code, "message": message})


def require(condition: bool, code: str, message: str, status: int = 409):
    if not condition:
        fail(status, code, message)
