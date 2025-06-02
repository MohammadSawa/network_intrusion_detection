from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from app.api.endpoints import router as api_router
from app.core.database import Base, engine, get_db, User, Workspace
from app.core.auth import get_user_by_api_key
from sqlalchemy.orm import Session
from pathlib import Path


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Network Anomaly Detection API",
    description="API for detecting anomalous web traffic patterns",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.mount("/static", StaticFiles(directory="app/static"), name="static")


templates = Jinja2Templates(directory="app/templates")


app.include_router(api_router, prefix="/api")


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    
    api_key = request.cookies.get("api_key")
    if not api_key:
        return None

    try:
        return await get_user_by_api_key(db, api_key)
    except:
        return None

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user: User = Depends(get_current_user)):
    
    if current_user:
        return RedirectResponse(url="/workspaces")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, current_user: User = Depends(get_current_user)):
    
    if current_user:
        return RedirectResponse(url="/workspaces")
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/workspaces", response_class=HTMLResponse)
async def workspaces_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    if not current_user:
        return RedirectResponse(url="/login")

    workspaces = db.query(Workspace).filter(Workspace.user_id == current_user.id).all()
    return templates.TemplateResponse(
        "workspaces.html",
        {
            "request": request,
            "workspaces": workspaces
        }
    )

@app.get("/dashboard/{workspace_id}", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    if not current_user:
        return RedirectResponse(url="/login")

    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "workspace": workspace
        }
    )

@app.get("/logout")
async def logout():
    
    response = RedirectResponse(url="/")
    response.delete_cookie("api_key")
    return response

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    
    return templates.TemplateResponse("logs.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    
    return templates.TemplateResponse("settings.html", {"request": request}) 