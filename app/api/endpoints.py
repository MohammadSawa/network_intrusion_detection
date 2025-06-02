from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request, Response, UploadFile, File, Body
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import csv
import io
import pandas as pd
import json
import numpy as np
import base64
import joblib
from pathlib import Path
import sys
import traceback
import importlib.util


app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_dir not in sys.path:
    sys.path.append(app_dir)

from ..core.auth import create_user, get_user_by_api_key, UserInDB, authenticate_user
from ..core.database import get_db, TrafficLog, User, Workspace



try:
    
    original_dir = os.getcwd()
    os.chdir(app_dir)
    
    
    spec = importlib.util.spec_from_file_location("pipeline_manager", os.path.join(app_dir, "pipeline_manager.py"))
    pipeline_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline_manager)
    
    
    main_pipeline_path = os.path.join(app_dir, "main_pipeline.pkl")
    
    
    print("Loading pipeline using pipeline_manager...")
    if not os.path.exists(main_pipeline_path):
        print(f"Pipeline not found, pipeline_manager will create it")
        
    
    print("Getting main_pipeline from pipeline_manager...")
    main_pipeline = pipeline_manager.get_pipeline()
    if main_pipeline:
        PIPELINE_READY = True
        print(f"Successfully loaded main pipeline")
    else:
        print("Failed to get pipeline from pipeline_manager")
        PIPELINE_READY = False
        main_pipeline = None
        
    
    os.chdir(original_dir)
except Exception as e:
    print(f"Error loading main pipeline: {str(e)}")
    traceback.print_exc()
    PIPELINE_READY = False
    main_pipeline = None

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class TrafficLogResponse(BaseModel):
    id: int
    timestamp: datetime
    source_ip: str
    destination_ip: str
    protocol: str
    status: str

    class Config:
        from_attributes = True


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[UserInDB]:
    
    api_key = request.cookies.get("api_key")
    if not api_key:
        return None
    
    try:
        return await get_user_by_api_key(db, api_key)
    except:
        return None


@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    workspace: WorkspaceCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> WorkspaceResponse:
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    db_workspace = Workspace(
        name=workspace.name,
        description=workspace.description,
        user_id=current_user.id
    )
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

@router.get("/workspaces", response_model=List[WorkspaceResponse])
async def get_workspaces(
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[WorkspaceResponse]:
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    workspaces = db.query(Workspace).filter(Workspace.user_id == current_user.id).all()
    return workspaces

@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    db.delete(workspace)
    db.commit()
    return {"message": "Workspace deleted successfully"}


@router.post("/register", response_model=UserInDB)
async def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
) -> UserInDB:
    
    try:
        return create_user(db, user.username, user.email, user.password)
    except IntegrityError as e:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=UserInDB)
async def login(
    user: UserLogin,
    db: Session = Depends(get_db)
) -> UserInDB:
    
    try:
        return authenticate_user(db, user.username, user.password)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

@router.get("/logs", response_model=List[TrafficLogResponse])
async def get_logs(
    workspace_id: int = Query(..., description="Workspace ID to filter logs"),
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
) -> List[TrafficLogResponse]:
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
        
    
    logs = db.query(TrafficLog).filter(
        TrafficLog.user_id == current_user.id,
        TrafficLog.workspace_id == workspace_id
    ).offset(skip).limit(limit).all()
    
    
    if not logs:
        return []
        
    return logs

@router.get("/auth/status")
async def get_auth_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    
    return {"is_authenticated": current_user is not None}

@router.get("/api-key")
async def get_api_key(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"api_key": current_user.api_key}

@router.get("/workspaces-for-monitor", response_model=List[WorkspaceResponse])
async def get_workspaces_for_monitor(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
) -> List[WorkspaceResponse]:
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    
    user = db.query(User).filter(User.api_key == x_api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    
    workspaces = db.query(Workspace).filter(Workspace.user_id == user.id).all()
    return workspaces 

@router.post("/direct-process")
async def direct_process_csv(
    request: Request,
    x_api_key: str = Header(None)
):
    print(f"[INFO] Received request to /direct-process endpoint")
    print(f"[INFO] API Key used: {x_api_key}")
    
    try:
        
        body = await request.json()
        print(f"[INFO] Request body keys: {list(body.keys())}")
        
        
        if 'csv_text' not in body:
            raise HTTPException(
                status_code=400, 
                detail="Missing required parameter: csv_text must be provided"
            )
        
        csv_text = body.get('csv_text')
        workspace_id = body.get('workspace_id')
        
        
        if workspace_id:
            if not x_api_key:
                raise HTTPException(
                    status_code=400,
                    detail="API key required when workspace_id is specified"
                )
            
            
            db = next(get_db())
            user = db.query(User).filter(User.api_key == x_api_key).first()
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )
            
            
            workspace = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.user_id == user.id
            ).first()
            if not workspace:
                raise HTTPException(
                    status_code=404,
                    detail="Workspace not found or access denied"
                )
        print(f"[INFO] Received CSV text data, length: {len(csv_text)}")
        
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.csv', mode='w', delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(csv_text)
            print(f"[INFO] Saved CSV data to temporary file: {temp_file_path}")
        
        try:
            
            import importlib.util
            
            app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app")
            spec = importlib.util.spec_from_file_location("pipeline_manager", os.path.join(app_dir, "pipeline_manager.py"))
            pipeline_manager_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pipeline_manager_module)
            
            
            import pandas as pd
            import io
            
            
            df = pd.read_csv(io.StringIO(csv_text))
            original_data = df.to_dict(orient='records')
            
            
            print(f"[INFO] Calling pipeline_manager.process_file with {temp_file_path}")
            predictions = pipeline_manager_module.process_file(temp_file_path)
            print(f"[INFO] Predictions generated: {predictions[:5] if hasattr(predictions, '__iter__') else predictions}")
            
            
            if len(predictions) == 0:
                print(f"[WARNING] No predictions were generated for the input file")
                response_data = {
                    "status": "warning",
                    "message": "No predictions were generated. The file may be empty or contain invalid data.",
                    "predictions": [],
                    "original_data": [],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                return response_data
            
            
            if hasattr(predictions, 'tolist'):
                predictions_list = predictions.tolist()
            else:
                try:
                    predictions_list = list(predictions)
                except:
                    predictions_list = predictions
            
            
            from datetime import datetime, timezone
            current_time = datetime.now(timezone.utc).isoformat()
            response_data = {
                "status": "success",
                "predictions": predictions_list,
                "original_data": original_data,
                "timestamp": current_time
            }
            
            
            try:
                
                user_id = None
                if x_api_key:
                    db = next(get_db())
                    user = db.query(User).filter(User.api_key == x_api_key).first()
                    if user:
                        user_id = user.id
                
                
                if user_id and len(predictions_list) > 0 and len(original_data) > 0:
                    for i, (pred, data_row) in enumerate(zip(predictions_list, original_data)):
                        
                        
                        
                        source_ip = (data_row.get('Source IP') or 
                                   data_row.get(' Source IP') or 
                                   data_row.get('Src IP') or 
                                   data_row.get(' Src IP') or
                                   data_row.get('src_ip') or
                                   data_row.get('source_ip') or 'N/A')
                        
                        
                        destination_ip = (data_row.get('Destination IP') or 
                                        data_row.get(' Destination IP') or 
                                        data_row.get('Dst IP') or 
                                        data_row.get(' Dst IP') or
                                        data_row.get('dst_ip') or
                                        data_row.get('destination_ip') or 
                                        f"Port: {data_row.get(' Destination Port', data_row.get('Destination Port', 'unknown'))}")
                        
                        
                        protocol = (data_row.get('Protocol') or 
                                  data_row.get(' Protocol') or 
                                  data_row.get('protocol') or 'TCP/IP')
                        
                        
                        traffic_log = TrafficLog(
                            user_id=user_id,
                            workspace_id=workspace_id,  
                            source_ip=source_ip,
                            destination_ip=destination_ip,
                            protocol=protocol,
                            status=str(pred),  
                            headers=data_row
                        )
                        db.add(traffic_log)
                        
                        
                        if i % 100 == 0:
                            db.commit()
                    
                    
                    db.commit()
            except Exception as e:
                print(f"[WARNING] Failed to store logs in database: {str(e)}")
                
                pass
            
            print(f"[INFO] Returning response with predictions and original data")
            return response_data
            
        except Exception as e:
            print(f"[ERROR] Error processing CSV: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Error processing CSV data: {str(e)}"
            )
        finally:
            
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                print(f"[INFO] Removed temporary file: {temp_file_path}")
                
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON in request body"
        )
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )