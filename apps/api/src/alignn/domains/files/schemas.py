from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from alignn.domains.identity.schemas import StrictModel

EXTENSIONS = {"resume": {".pdf", ".docx"}, "submission": {".pdf", ".pptx", ".zip"}}
LIMITS = {"resume": 10 * 1024 * 1024, "submission": 25 * 1024 * 1024}


class FileInit(StrictModel):
    filename: str = Field(min_length=1, max_length=180)
    purpose: Literal["resume", "submission"]
    size: int = Field(ge=1)

    @field_validator("filename")
    @classmethod
    def filename_safe(cls, value):
        if any(c in value for c in ("/", "\\", "\r", "\n", "\0")):
            raise ValueError("Use a filename without directory paths or control characters")
        return value

    @model_validator(mode="after")
    def valid_file(self):
        from pathlib import Path

        if Path(self.filename).suffix.lower() not in EXTENSIONS[self.purpose]:
            raise ValueError("This file type is not accepted")
        if self.size > LIMITS[self.purpose]:
            raise ValueError("This file exceeds the size limit")
        return self


class GrantCreate(StrictModel):
    organization_id: UUID
