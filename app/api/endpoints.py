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

# Add app directory to the path to ensure imports work
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_dir not in sys.path:
    sys.path.append(app_dir)

from ..core.auth import create_user, get_user_by_api_key, UserInDB, authenticate_user
from ..core.database import get_db, TrafficLog, User, Workspace

# Initialize the pipeline using pipeline_manager.py
# This would typically be moved to a startup event or module-level initialization
try:
    # Change to the app directory to ensure relative paths work
    original_dir = os.getcwd()
    os.chdir(app_dir)
    
    # Load the module directly
    spec = importlib.util.spec_from_file_location("pipeline_manager", os.path.join(app_dir, "pipeline_manager.py"))
    pipeline_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline_manager)
    
    # Check if pipeline exists, and let pipeline_manager handle everything
    main_pipeline_path = os.path.join(app_dir, "main_pipeline.pkl")
    
    # Let pipeline_manager load or create the pipeline
    print("Loading pipeline using pipeline_manager...")
    if not os.path.exists(main_pipeline_path):
        print(f"Pipeline not found, pipeline_manager will create it")
        
    # Get the main_pipeline directly from pipeline_manager
    print("Getting main_pipeline from pipeline_manager...")
    main_pipeline = pipeline_manager.get_pipeline()
    if main_pipeline:
        PIPELINE_READY = True
        print(f"Successfully loaded main pipeline")
    else:
        print("Failed to get pipeline from pipeline_manager")
        PIPELINE_READY = False
        main_pipeline = None
        
    # Change back to the original directory
    os.chdir(original_dir)
except Exception as e:
    print(f"Error loading main pipeline: {str(e)}")
    traceback.print_exc()
    PIPELINE_READY = False
    main_pipeline = None

router = APIRouter()

# Request/Response Models
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

# Dependency
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[UserInDB]:
    """Get current user from session or API key."""
    api_key = request.cookies.get("api_key")
    if not api_key:
        return None
    
    try:
        return await get_user_by_api_key(db, api_key)
    except:
        return None

# Workspace Endpoints
@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    workspace: WorkspaceCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> WorkspaceResponse:
    """Create a new workspace for the current user."""
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
    """Get all workspaces for the current user."""
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
    """Delete a workspace."""
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

# User Endpoints
@router.post("/register", response_model=UserInDB)
async def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
) -> UserInDB:
    """Register a new user and get API key."""
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
    """Login and get API key."""
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
    """Get traffic logs for a specific workspace."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate workspace belongs to user
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
        
    # Get logs filtered by workspace
    logs = db.query(TrafficLog).filter(
        TrafficLog.user_id == current_user.id,
        TrafficLog.workspace_id == workspace_id
    ).offset(skip).limit(limit).all()
    
    # If no logs exist, return empty list
    if not logs:
        return []
        
    return logs

@router.get("/auth/status")
async def get_auth_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """Check if the user is authenticated."""
    return {"is_authenticated": current_user is not None}

@router.get("/api-key")
async def get_api_key(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Get the API key for the current user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"api_key": current_user.api_key}

@router.get("/workspaces-for-monitor", response_model=List[WorkspaceResponse])
async def get_workspaces_for_monitor(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
) -> List[WorkspaceResponse]:
    """Get workspaces for network monitor selection."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Get user from API key
    user = db.query(User).filter(User.api_key == x_api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get user's workspaces
    workspaces = db.query(Workspace).filter(Workspace.user_id == user.id).all()
    return workspaces 

@router.post("/direct-process")
async def direct_process_csv(
    request: Request,
    x_api_key: str = Header(None)
):
    """
    Process CSV data directly using the main pipeline.
    This endpoint calls pipeline_manager.py to process data and return predictions.
    """
    # Log that we received a request
    print(f"[INFO] Received request to /direct-process endpoint")
    print(f"[INFO] API Key used: {x_api_key}")
    
    try:
        # Get the raw request body
        body = await request.json()
        print(f"[INFO] Request body keys: {list(body.keys())}")
        
        # Get the CSV text from the request body
        if 'csv_text' not in body:
            raise HTTPException(
                status_code=400, 
                detail="Missing required parameter: csv_text must be provided"
            )
        
        csv_text = body.get('csv_text')
        workspace_id = body.get('workspace_id')
        
        # Validate workspace_id if provided
        if workspace_id:
            if not x_api_key:
                raise HTTPException(
                    status_code=400,
                    detail="API key required when workspace_id is specified"
                )
            
            # Get user from API key
            db = next(get_db())
            user = db.query(User).filter(User.api_key == x_api_key).first()
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )
            
            # Validate workspace belongs to user
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
        
        # Save the received CSV to a temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.csv', mode='w', delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(csv_text)
            print(f"[INFO] Saved CSV data to temporary file: {temp_file_path}")
        
        try:
            # Import pipeline_manager as a module
            import importlib.util
            
            app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app")
            spec = importlib.util.spec_from_file_location("pipeline_manager", os.path.join(app_dir, "pipeline_manager.py"))
            pipeline_manager_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pipeline_manager_module)
            
            # Parse CSV data to get original rows
            import pandas as pd
            import io
            
            # Parse the CSV text into a DataFrame
            df = pd.read_csv(io.StringIO(csv_text))
            original_data = df.to_dict(orient='records')
            
            # Call the process_file function directly
            print(f"[INFO] Calling pipeline_manager.process_file with {temp_file_path}")
            predictions = pipeline_manager_module.process_file(temp_file_path)
            print(f"[INFO] Predictions generated: {predictions[:5] if hasattr(predictions, '__iter__') else predictions}")
            
            # Check if we got valid predictions
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
            
            # Convert predictions to a list for JSON serialization
            if hasattr(predictions, 'tolist'):
                predictions_list = predictions.tolist()
            else:
                try:
                    predictions_list = list(predictions)
                except:
                    predictions_list = predictions
            
            # Create response with both predictions and original data
            from datetime import datetime, timezone
            current_time = datetime.now(timezone.utc).isoformat()
            response_data = {
                "status": "success",
                "predictions": predictions_list,
                "original_data": original_data,
                "timestamp": current_time
            }
            
            # Store predictions and data in the database for historical tracking
            try:
                # Extract API key user if available
                user_id = None
                if x_api_key:
                    db = next(get_db())
                    user = db.query(User).filter(User.api_key == x_api_key).first()
                    if user:
                        user_id = user.id
                
                # Create traffic log entries in batches
                if user_id and len(predictions_list) > 0 and len(original_data) > 0:
                    for i, (pred, data_row) in enumerate(zip(predictions_list, original_data)):
                        # Extract network information from data_row using the actual CSV columns
                        # Use appropriate fields from the dataset or defaults if not available
                        # Try multiple possible column names for source IP (with and without spaces)
                        source_ip = (data_row.get('Source IP') or 
                                   data_row.get(' Source IP') or 
                                   data_row.get('Src IP') or 
                                   data_row.get(' Src IP') or
                                   data_row.get('src_ip') or
                                   data_row.get('source_ip') or 'N/A')
                        
                        # Try multiple possible column names for destination IP
                        destination_ip = (data_row.get('Destination IP') or 
                                        data_row.get(' Destination IP') or 
                                        data_row.get('Dst IP') or 
                                        data_row.get(' Dst IP') or
                                        data_row.get('dst_ip') or
                                        data_row.get('destination_ip') or 
                                        f"Port: {data_row.get(' Destination Port', data_row.get('Destination Port', 'unknown'))}")
                        
                        # Try multiple possible column names for protocol
                        protocol = (data_row.get('Protocol') or 
                                  data_row.get(' Protocol') or 
                                  data_row.get('protocol') or 'TCP/IP')
                        
                        # Create traffic log with prediction and original data
                        traffic_log = TrafficLog(
                            user_id=user_id,
                            workspace_id=workspace_id,  # Associate with specific workspace
                            source_ip=source_ip,
                            destination_ip=destination_ip,
                            protocol=protocol,
                            status=str(pred),  # Store the actual prediction (DoS, DDoS, etc.)
                            headers=data_row
                        )
                        db.add(traffic_log)
                        
                        # Commit in batches to avoid excessive database operations
                        if i % 100 == 0:
                            db.commit()
                    
                    # Final commit for any remaining logs
                    db.commit()
            except Exception as e:
                print(f"[WARNING] Failed to store logs in database: {str(e)}")
                # Don't fail the whole request if logging to DB fails
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
            # Clean up the temporary file
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