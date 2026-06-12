from fastapi import APIRouter, Depends, Response, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
import security

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# Открытие страницы логина (GET)
@router.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


# Обработка отправки формы (POST)
@router.post("/login")
def login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    # Ищем пользователя в БД
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user or not security.verify_password(password, user.password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Неверное имя пользователя или пароль"}
        )

    token = security.create_access_token(data={"sub": user.username})

    response = RedirectResponse(url="/dashboard", status_code=303)

    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response

# Выход из системы (GET)
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# Открытие страницы с регистрацией (GET)
@router.get("/register", response_class=HTMLResponse)
def get_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

# Отправка запроса на регистрацию (POST)
@router.post("/register")
def register(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    # Проверяем, нет ли уже пользователя с таким логином
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Пользователь с таким именем уже существует"}
        )

    # Хэшируем чистый пароль
    hashed = security.hash_password(password)

    new_user = models.User(username=username, password=hashed)

    db.add(new_user)
    db.commit()

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"success": "Вы успешно зарегистрировались! Теперь войдите в аккаунт."}
    )