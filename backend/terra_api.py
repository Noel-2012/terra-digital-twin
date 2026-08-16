from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from pydantic import BaseModel

from .terra_scientific_engine import (
    DATA_DIR,
    OUTPUT_DIR,
    VARIABLE_CATALOG,
    DATASETS,
    inspect_dataset,
    register_dataset,
    list_datasets,
    open_data,
    calculate_time_series,
    calculate_statistics,
    calculate_trend,
    scientific_map,
    create_time_series_figure,
    build_analysis_plan,
)


app = FastAPI(
    title="TERRA",
    description=(
        "TERRA Planetary Digital Twin — "
        "Geospatial Scientific Workspace"
    ),
    version="9.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "TERRA",
        "system": "Planetary Digital Twin",
        "version": "9.0.0",
        "status": "online",
        "docs": "/docs",
    }


# ============================================================
# CAPABILITIES
# ============================================================

@app.get("/capabilities")
def capabilities():

    groups = {}

    for key, value in VARIABLE_CATALOG.items():

        group = value["group"]

        groups.setdefault(
            group,
            [],
        ).append(key)

    return {

        "version": "9.0.0",

        "variable_groups": groups,

        "analyses": [
            "map",
            "timeseries",
            "seasonal",
            "anomaly",
            "statistics",
            "trend",
            "percentile",
            "som",
        ],

        "spatial_tools": [
            "point",
            "circle",
            "rectangle",
            "polygon",
            "freehand",
            "coordinates",
            "geojson",
        ],

        "input_formats": [
            "NetCDF",
            "CSV",
            "Excel",
        ],

        "outputs": [
            "PNG",
            "SVG",
            "PDF",
            "CSV",
            "JSON",
            "NetCDF",
        ],

        "forecast": {
            "hourly": True,
            "24_hour": True,
            "multi_day": True,
            "ai_model": False,
            "status": "adapter architecture only",
        },

        "ai": {
            "enabled": False,
            "planner": True,
            "status": "scientific rule-based planner",
        },
    }


# ============================================================
# UPLOAD DATA
# ============================================================

@app.post("/data/upload")
async def upload_data(
    file: UploadFile = File(...)
):

    allowed = [
        ".nc",
        ".netcdf",
        ".csv",
        ".xlsx",
        ".xls",
    ]

    suffix = Path(
        file.filename
    ).suffix.lower()

    if suffix not in allowed:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {suffix}. "
                f"Supported: {allowed}"
            ),
        )

    destination = DATA_DIR / file.filename

    content = await file.read()

    destination.write_bytes(
        content
    )

    try:

        result = register_dataset(
            str(destination)
        )

        return result

    except Exception as exc:

        destination.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# INSPECT FILE
# ============================================================

@app.get("/data/inspect")
def inspect_file(
    filename: str,
):

    path = DATA_DIR / filename

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    try:

        return inspect_dataset(
            str(path)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# DATASETS
# ============================================================

@app.get("/data/datasets")
def datasets():

    return {
        "datasets": list_datasets()
    }


# ============================================================
# TIME SERIES REQUEST
# ============================================================

class TimeSeriesRequest(BaseModel):

    dataset_id: str
    variable: str

    bbox: Optional[dict] = None

    aggregation: str = "mean"


@app.post("/analysis/timeseries")
def timeseries(
    request: TimeSeriesRequest
):

    if request.dataset_id not in DATASETS:

        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    path = DATASETS[
        request.dataset_id
    ]["path"]

    try:

        data = open_data(
            path
        )

        result = calculate_time_series(
            data,
            request.variable,
            request.bbox,
            request.aggregation,
        )

        image = create_time_series_figure(
            result["time"],
            result["values"],
            request.variable,
            result["units"],
        )

        result["figure"] = (
            Path(image).name
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# MAP REQUEST
# ============================================================

class MapRequest(BaseModel):

    dataset_id: str
    variable: str
    title: Optional[str] = None


@app.post("/analysis/map")
def map_analysis(
    request: MapRequest
):

    if request.dataset_id not in DATASETS:

        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    path = DATASETS[
        request.dataset_id
    ]["path"]

    try:

        data = open_data(
            path
        )

        output = scientific_map(
            data,
            request.variable,
            title=request.title,
        )

        return {
            "status": "success",
            "variable": request.variable,
            "output": Path(
                output
            ).name,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# STATISTICS
# ============================================================

class StatisticsRequest(BaseModel):

    values: list[float]


@app.post("/analysis/statistics")
def statistics(
    request: StatisticsRequest
):

    try:

        return calculate_statistics(
            request.values
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# TREND
# ============================================================

class TrendRequest(BaseModel):

    times: list
    values: list[float]


@app.post("/analysis/trend")
def trend(
    request: TrendRequest
):

    try:

        return calculate_trend(
            request.times,
            request.values,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# AI-READY PLANNER
# ============================================================

class PlanRequest(BaseModel):

    request: str
    dataset_id: Optional[str] = None


@app.post("/ai/plan")
def ai_plan(
    request: PlanRequest
):

    return build_analysis_plan(
        request.request,
        request.dataset_id,
    )


# ============================================================
# OUTPUT FILE
# ============================================================

@app.get("/outputs/{filename}")
def output_file(
    filename: str
):

    path = OUTPUT_DIR / filename

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="Output not found.",
        )

    return FileResponse(
        path
    )