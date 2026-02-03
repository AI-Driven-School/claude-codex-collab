"""
CSVインポート関連のPydanticモデル
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List


class CSVRowData(BaseModel):
    """CSVの1行分のデータ"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    employee_id: str = Field(..., min_length=1, max_length=50)
    department: str = Field(..., min_length=1, max_length=100)


class CSVValidationError(BaseModel):
    """CSV検証エラー"""
    row_number: int
    column: str
    value: str
    error_message: str


class DuplicateEntry(BaseModel):
    """重複エントリ"""
    row_number: int
    email: str
    duplicate_type: str  # "csv_internal" or "database"


class CSVImportResult(BaseModel):
    """CSVインポート結果"""
    success: bool
    total_rows: int
    imported_count: int
    skipped_count: int
    validation_errors: List[CSVValidationError] = []
    duplicates: List[DuplicateEntry] = []
    message: str


class CSVPreviewRow(BaseModel):
    """CSVプレビュー用の行データ"""
    row_number: int
    email: str
    name: str
    employee_id: str
    department: str
    is_valid: bool
    errors: List[str] = []


class CSVPreviewResponse(BaseModel):
    """CSVプレビューレスポンス"""
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_in_csv: int
    duplicate_in_db: int
    preview_data: List[CSVPreviewRow]
    can_import: bool
