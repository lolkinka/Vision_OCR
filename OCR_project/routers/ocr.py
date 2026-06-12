import io
import ollama
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from security import get_current_user
from models import Conversion

router = APIRouter(tags=["Math OCR"])


@router.post("/predict-math")
async def predict_math(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)  # Защищаем эндпоинт и получаем юзера
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файл должен быть изображением")

    try:
        image_bytes = await file.read()

        prompt = (
            "Convert the handwritten mathematical expression in this image into a clean, valid LaTeX code string. "
            "Output ONLY the raw LaTeX text line. Do NOT repeat it. Just one line."
        )

        response = ollama.chat(
            model='glm-ocr',
            messages=[{'role': 'user', 'content': prompt, 'images': [image_bytes]}]
        )

        raw_output = response.message.content

        # Фильтрация зацикливаний
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        valid_lines = [line for line in lines if not line.startswith("`")]
        latex_formula = valid_lines[0] if valid_lines else raw_output.strip()

        # Очистка от знаков $
        if latex_formula.startswith("$$") and latex_formula.endswith("$$"):
            latex_formula = latex_formula[2:-2].strip()
        elif latex_formula.startswith("$") and latex_formula.endswith("$"):
            latex_formula = latex_formula[1:-1].strip()
        latex_formula = latex_formula.removeprefix("\\(").removesuffix("\\)").removeprefix("\\[").removesuffix(
            "\\]").strip()

        # СОХРАНЕНИЕ В ИСТОРИЮ
        new_conversion = Conversion(
            user_id=current_user.id,
            filename=file.filename,
            formula_latex=latex_formula
        )
        db.add(new_conversion)
        db.commit()

        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "formula_latex": latex_formula
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка модели: {str(e)}")