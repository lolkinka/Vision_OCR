from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")
from routers import auth, ocr
from fastapi import Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
from security import get_current_user
from models import Conversion

app = FastAPI(
    title="Math OCR & Auth API",
    description="Приложение с авторизацией в PostgreSQL и распознаванием математических формул",
    version="1.0.0"
)

# Подключаем роутеры к главному приложению
app.include_router(auth.router)
app.include_router(ocr.router)

@app.get("/")
async def root():
    # Перенаправляем на страницу логина при открытии корня сайта
    return RedirectResponse(url="/login")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Отдаем страницу личного кабинета
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.get("/profile", response_class=HTMLResponse)
async def view_profile(
        request: Request,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    # Запрашиваем 10 последних конвертаций текущего пользователя, сортируя по дате (от новых к старым)
    history = db.query(Conversion) \
        .filter(Conversion.user_id == current_user.id) \
        .order_by(Conversion.created_at.desc()) \
        .limit(10) \
        .all()

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"user": current_user, "history": history}
    )