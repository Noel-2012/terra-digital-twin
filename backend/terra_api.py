from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.terra_scientific_engine import (
    open_data,
    detect_variable,
    subset_region,
    convert_units,
    scientific_map,
    seasonal_map,
    time_series,
    anomaly_map,
    train_som,
    dataset_summary,
    get_series,
    calculate_statistics,
    trend_statistics,
)

from backend.terra_outputs import (
    publication_time_series,
    heatmap,
    create_pdf_report,
    save_json,
    save_dataframe_csv,
)


app = FastAPI(
    title="TERRA Scientific API",
    description=(
        "TERRA Planetary Digital Twin scientific "
        "analysis backend."
    ),
    version="8.2.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = Path(
    __file__
).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

DATA_DIR.mkdir(
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    exist_ok=True
)


VARIABLE_GROUPS = {
    "Atmosphere": [
        "temperature",
        "pressure",
        "humidity",
        "wind_speed",
        "wind_u",
        "wind_v",
        "precipitation",
    ],
    "Air quality": [
        "pm25",
        "pm10",
        "ozone",
        "no2",
        "so2",
        "co",
        "aerosol",
    ],
    "Trace gases": [
        "mercury",
        "co2",
        "ch4",
    ],
    "Land / biosphere": [
        "ndvi",
        "soil_moisture",
        "lst",
    ],
    "Ocean": [
        "sst",
        "salinity",
        "sea_level",
        "currents",
    ],
}


ANALYSES = [
    "map",
    "timeseries",
    "seasonal",
    "anomaly",
    "statistics",
    "trend",
    "percentile",
    "som",
]


@app.get("/")
def root():

    return {
        "name": "TERRA",
        "system": "Planetary Digital Twin",
        "version": "8.2.0",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
def health():

    return {
        "status": "ok",
        "engine": "TERRA Scientific Engine",
        "version": "8.2.0",
    }


@app.get("/capabilities")
def capabilities():

    return {
        "version": "8.2.0",
        "variable_groups": VARIABLE_GROUPS,
        "analyses": ANALYSES,
        "formats": [
            "NetCDF",
            "CSV",
        ],
        "outputs": [
            "PNG",
            "SVG",
            "PDF",
            "CSV",
            "JSON",
        ],
        "forecast": {
            "hourly": True,
            "24_hour": True,
            "multi_day": True,
            "ai_model": False,
            "status": (
                "adapter architecture only"
            ),
        },
    }


async def save_upload(
    file: UploadFile,
    prefix: str,
):

    suffix = Path(
        file.filename or ""
    ).suffix.lower()

    if suffix not in [
        ".nc",
        ".nc4",
        ".netcdf",
        ".csv",
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only NetCDF and CSV "
                "files are supported."
            ),
        )

    filename = (
        f"{prefix}_"
        f"{uuid.uuid4().hex}"
        f"{suffix}"
    )

    path = DATA_DIR / filename

    with path.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )

    return path


@app.post("/dataset/summary")
async def dataset_info(
    file: UploadFile = File(...),
):

    path = await save_upload(
        file,
        "summary",
    )

    try:

        return dataset_summary(
            str(path)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post("/analysis/run")
async def run_analysis(

    file: UploadFile = File(...),

    variable: str = Form(""),

    analysis: str = Form("map"),

    latitude: Optional[float] = Form(None),

    longitude: Optional[float] = Form(None),

    lat_min: Optional[float] = Form(None),

    lat_max: Optional[float] = Form(None),

    lon_min: Optional[float] = Form(None),

    lon_max: Optional[float] = Form(None),

    unit: Optional[str] = Form(None),
):

    path = await save_upload(
        file,
        "analysis",
    )

    job_id = uuid.uuid4().hex[:12]

    try:

        ds = open_data(
            str(path)
        )

        actual_variable = detect_variable(
            ds,
            variable or None,
        )

        if hasattr(
            ds,
            "data_vars",
        ):

            field = ds[
                actual_variable
            ]

            field = convert_units(
                field,
                actual_variable,
                unit,
            )

            if any(
                value is not None
                for value in [
                    lat_min,
                    lat_max,
                    lon_min,
                    lon_max,
                ]
            ):

                ds = subset_region(
                    ds,
                    lat_min,
                    lat_max,
                    lon_min,
                    lon_max,
                )

                field = ds[
                    actual_variable
                ]

        else:

            field = ds[
                actual_variable
            ]

        outputs = []

        base = (
            f"terra_{job_id}_"
            f"{actual_variable}"
        )

        if analysis == "map":

            output = (
                OUTPUT_DIR /
                f"{base}_map.png"
            )

            scientific_map(
                field,
                actual_variable,
                str(output),
            )

            outputs.append(
                output.name
            )

        elif analysis == "seasonal":

            output = (
                OUTPUT_DIR /
                f"{base}_seasonal.png"
            )

            seasonal_map(
                field,
                actual_variable,
                str(output),
            )

            outputs.append(
                output.name
            )

        elif analysis == "anomaly":

            output = (
                OUTPUT_DIR /
                f"{base}_anomaly.png"
            )

            anomaly_map(
                field,
                actual_variable,
                str(output),
            )

            outputs.append(
                output.name
            )

        elif analysis == "timeseries":

            output = (
                OUTPUT_DIR /
                f"{base}_timeseries.png"
            )

            result = time_series(
                field,
                actual_variable,
                str(output),
                latitude,
                longitude,
            )

            outputs.append(
                output.name
            )

            series = get_series(
                field,
                latitude,
                longitude,
            )

            svg = (
                OUTPUT_DIR /
                f"{base}_timeseries.svg"
            )

            publication_time_series(
                series,
                actual_variable,
                str(
                    field.attrs.get(
                        "units",
                        "",
                    )
                ),
                output_svg=str(svg),
            )

            outputs.append(
                svg.name
            )

        elif analysis == "statistics":

            series = get_series(
                field,
                latitude,
                longitude,
            )

            statistics = (
                calculate_statistics(
                    series
                )
            )

            json_path = (
                OUTPUT_DIR /
                f"{base}_statistics.json"
            )

            save_json(
                statistics,
                str(json_path),
            )

            outputs.append(
                json_path.name
            )

            return {
                "status": "success",
                "job_id": job_id,
                "analysis": analysis,
                "variable": actual_variable,
                "statistics": statistics,
                "outputs": outputs,
            }

        elif analysis == "trend":

            series = get_series(
                field,
                latitude,
                longitude,
            )

            trend = trend_statistics(
                series
            )

            json_path = (
                OUTPUT_DIR /
                f"{base}_trend.json"
            )

            save_json(
                trend,
                str(json_path),
            )

            outputs.append(
                json_path.name
            )

            return {
                "status": "success",
                "job_id": job_id,
                "analysis": analysis,
                "variable": actual_variable,
                "trend": trend,
                "outputs": outputs,
            }

        elif analysis == "percentile":

            series = get_series(
                field,
                latitude,
                longitude,
            )

            values = series.values

            result = {
                "p01": float(
                    np.percentile(
                        values,
                        1,
                    )
                ),
                "p05": float(
                    np.percentile(
                        values,
                        5,
                    )
                ),
                "p10": float(
                    np.percentile(
                        values,
                        10,
                    )
                ),
                "p50": float(
                    np.percentile(
                        values,
                        50,
                    )
                ),
                "p90": float(
                    np.percentile(
                        values,
                        90,
                    )
                ),
                "p95": float(
                    np.percentile(
                        values,
                        95,
                    )
                ),
                "p99": float(
                    np.percentile(
                        values,
                        99,
                    )
                ),
            }

            json_path = (
                OUTPUT_DIR /
                f"{base}_percentiles.json"
            )

            save_json(
                result,
                str(json_path),
            )

            outputs.append(
                json_path.name
            )

            return {
                "status": "success",
                "job_id": job_id,
                "analysis": analysis,
                "variable": actual_variable,
                "percentiles": result,
                "outputs": outputs,
            }

        elif analysis == "som":

            result = train_som(
                field
            )

            json_path = (
                OUTPUT_DIR /
                f"{base}_som.json"
            )

            save_json(
                result,
                str(json_path),
            )

            outputs.append(
                json_path.name
            )

            return {
                "status": "success",
                "job_id": job_id,
                "analysis": analysis,
                "variable": actual_variable,
                "result": result,
                "outputs": outputs,
            }

        else:

            raise ValueError(
                f"Unknown analysis: "
                f"{analysis}"
            )

        metadata = {
            "TERRA version": "8.2.0",
            "Job": job_id,
            "Variable": actual_variable,
            "Analysis": analysis,
            "Latitude": latitude,
            "Longitude": longitude,
            "Source": (
                "User-uploaded dataset"
            ),
        }

        metadata_path = (
            OUTPUT_DIR /
            f"{base}_metadata.json"
        )

        save_json(
            metadata,
            str(metadata_path),
        )

        outputs.append(
            metadata_path.name
        )

        return {
            "status": "success",
            "job_id": job_id,
            "analysis": analysis,
            "variable": actual_variable,
            "outputs": outputs,
            "download_base": "/outputs/",
            "metadata": metadata,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.get(
    "/outputs/{filename}"
)
def output_file(
    filename: str,
):

    path = (
        OUTPUT_DIR /
        Path(filename).name
    )

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="Output not found.",
        )

    return FileResponse(
        path
    )