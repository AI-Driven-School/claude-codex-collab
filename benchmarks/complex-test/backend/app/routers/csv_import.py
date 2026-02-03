"""
CSV一括インポートエンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import csv
import io
import re
import secrets
import string

from app.db.database import get_db
from app.db.models import User, UserRole
from app.routers.auth import get_current_user
from app.models.csv_import import (
    CSVImportResult,
    CSVValidationError,
    DuplicateEntry,
    CSVPreviewResponse,
    CSVPreviewRow,
)
from app.utils.security import get_password_hash

router = APIRouter(prefix="/api/v1/admin/csv", tags=["csv-import"])

# 必須カラム
REQUIRED_COLUMNS = ["email", "name", "employee_id", "department"]


def generate_temp_password(length: int = 12) -> str:
    """一時パスワード生成"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_email(email: str) -> bool:
    """メールアドレスの形式チェック"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


async def parse_csv_file(file: UploadFile) -> tuple[List[dict], List[CSVValidationError]]:
    """CSVファイルをパースしてバリデーション"""
    content = await file.read()

    # エンコーディング検出（UTF-8, Shift-JIS対応）
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            text = content.decode('shift-jis')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSVファイルのエンコーディングが不正です。UTF-8またはShift-JISで保存してください。"
            )

    reader = csv.DictReader(io.StringIO(text))

    # ヘッダーチェック
    if not reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSVファイルにヘッダーがありません"
        )

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
    if missing_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"必須カラムがありません: {', '.join(missing_columns)}"
        )

    rows = []
    errors = []

    for row_num, row in enumerate(reader, start=2):  # ヘッダーが1行目なので2から開始
        row_errors = []

        # 各フィールドのバリデーション
        email = row.get('email', '').strip()
        name = row.get('name', '').strip()
        employee_id = row.get('employee_id', '').strip()
        department = row.get('department', '').strip()

        # 必須チェック
        if not email:
            row_errors.append(CSVValidationError(
                row_number=row_num, column="email", value="", error_message="メールアドレスは必須です"
            ))
        elif not validate_email(email):
            row_errors.append(CSVValidationError(
                row_number=row_num, column="email", value=email, error_message="メールアドレスの形式が不正です"
            ))

        if not name:
            row_errors.append(CSVValidationError(
                row_number=row_num, column="name", value="", error_message="名前は必須です"
            ))
        elif len(name) > 100:
            row_errors.append(CSVValidationError(
                row_number=row_num, column="name", value=name[:20] + "...", error_message="名前は100文字以内で入力してください"
            ))

        if not employee_id:
            row_errors.append(CSVValidationError(
                row_number=row_num, column="employee_id", value="", error_message="社員IDは必須です"
            ))
        elif len(employee_id) > 50:
            row_errors.append(CSVValidationError(
                row_number=row_num, column="employee_id", value=employee_id[:20] + "...", error_message="社員IDは50文字以内で入力してください"
            ))

        if not department:
            row_errors.append(CSVValidationError(
                row_number=row_num, column="department", value="", error_message="部署は必須です"
            ))
        elif len(department) > 100:
            row_errors.append(CSVValidationError(
                row_number=row_num, column="department", value=department[:20] + "...", error_message="部署は100文字以内で入力してください"
            ))

        errors.extend(row_errors)
        rows.append({
            "row_number": row_num,
            "email": email,
            "name": name,
            "employee_id": employee_id,
            "department": department,
            "is_valid": len(row_errors) == 0,
            "errors": [e.error_message for e in row_errors]
        })

    return rows, errors


async def check_duplicates(
    rows: List[dict],
    company_id: str,
    db: AsyncSession
) -> tuple[List[DuplicateEntry], List[DuplicateEntry]]:
    """重複チェック（CSV内重複とDB重複）"""
    csv_duplicates = []
    db_duplicates = []

    # CSV内の重複チェック
    email_counts = {}
    for row in rows:
        email = row["email"].lower()
        if email in email_counts:
            csv_duplicates.append(DuplicateEntry(
                row_number=row["row_number"],
                email=row["email"],
                duplicate_type="csv_internal"
            ))
        else:
            email_counts[email] = row["row_number"]

    # DBの重複チェック
    if rows:
        emails = [row["email"].lower() for row in rows]
        result = await db.execute(
            select(User).where(User.email.in_(emails))
        )
        existing_users = result.scalars().all()
        existing_emails = {u.email.lower() for u in existing_users}

        for row in rows:
            if row["email"].lower() in existing_emails:
                db_duplicates.append(DuplicateEntry(
                    row_number=row["row_number"],
                    email=row["email"],
                    duplicate_type="database"
                ))

    return csv_duplicates, db_duplicates


@router.post("/preview", response_model=CSVPreviewResponse)
async def preview_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """CSVファイルのプレビュー（インポート前確認）"""
    # 管理者権限チェック
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )

    # ファイル形式チェック
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSVファイルのみアップロード可能です"
        )

    # CSVパース
    rows, validation_errors = await parse_csv_file(file)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSVファイルにデータがありません"
        )

    # 重複チェック
    csv_duplicates, db_duplicates = await check_duplicates(
        rows, str(current_user.company_id), db
    )

    # 重複情報をrowsに反映
    csv_dup_rows = {d.row_number for d in csv_duplicates}
    db_dup_rows = {d.row_number for d in db_duplicates}

    for row in rows:
        if row["row_number"] in csv_dup_rows:
            row["errors"].append("CSV内で重複しています")
            row["is_valid"] = False
        if row["row_number"] in db_dup_rows:
            row["errors"].append("既にデータベースに登録されています")
            row["is_valid"] = False

    valid_rows = sum(1 for r in rows if r["is_valid"])
    invalid_rows = len(rows) - valid_rows

    preview_data = [
        CSVPreviewRow(**row) for row in rows[:100]  # 最大100件表示
    ]

    return CSVPreviewResponse(
        total_rows=len(rows),
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        duplicate_in_csv=len(csv_duplicates),
        duplicate_in_db=len(db_duplicates),
        preview_data=preview_data,
        can_import=valid_rows > 0
    )


@router.post("/import", response_model=CSVImportResult)
async def import_csv(
    file: UploadFile = File(...),
    skip_errors: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """CSVファイルから従業員を一括登録"""
    # 管理者権限チェック
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )

    # ファイル形式チェック
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSVファイルのみアップロード可能です"
        )

    # CSVパース
    rows, validation_errors = await parse_csv_file(file)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSVファイルにデータがありません"
        )

    # 重複チェック
    csv_duplicates, db_duplicates = await check_duplicates(
        rows, str(current_user.company_id), db
    )

    all_duplicates = csv_duplicates + db_duplicates

    # skip_errors=Falseで、エラーがある場合は処理中止
    if not skip_errors and (validation_errors or all_duplicates):
        return CSVImportResult(
            success=False,
            total_rows=len(rows),
            imported_count=0,
            skipped_count=len(rows),
            validation_errors=validation_errors,
            duplicates=all_duplicates,
            message="バリデーションエラーまたは重複があります。skip_errors=trueで再実行するとエラー行をスキップしてインポートします。"
        )

    # インポート対象の行を特定
    error_row_numbers = {e.row_number for e in validation_errors}
    csv_dup_rows = {d.row_number for d in csv_duplicates}
    db_dup_rows = {d.row_number for d in db_duplicates}
    skip_rows = error_row_numbers | csv_dup_rows | db_dup_rows

    # 既にインポート済みのメールアドレス（CSV内重複対策）
    imported_emails = set()
    imported_count = 0
    skipped_count = 0

    for row in rows:
        if row["row_number"] in skip_rows:
            skipped_count += 1
            continue

        email_lower = row["email"].lower()
        if email_lower in imported_emails:
            skipped_count += 1
            continue

        # 一時パスワード生成
        temp_password = generate_temp_password()

        # ユーザー作成
        new_user = User(
            company_id=current_user.company_id,
            email=row["email"],
            hashed_password=get_password_hash(temp_password),
            role=UserRole.EMPLOYEE,
        )
        db.add(new_user)
        imported_emails.add(email_lower)
        imported_count += 1

    await db.commit()

    return CSVImportResult(
        success=True,
        total_rows=len(rows),
        imported_count=imported_count,
        skipped_count=skipped_count,
        validation_errors=validation_errors if skip_errors else [],
        duplicates=all_duplicates if skip_errors else [],
        message=f"{imported_count}件のユーザーを登録しました。{skipped_count}件はスキップされました。"
    )


@router.get("/template")
async def download_template(current_user: User = Depends(get_current_user)):
    """CSVテンプレートのダウンロード"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )

    template = "email,name,employee_id,department\nuser@example.com,山田太郎,EMP001,営業部\n"

    return StreamingResponse(
        io.StringIO(template),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employee_template.csv"}
    )
