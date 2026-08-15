from __future__ import annotations

import json
import os
import tempfile
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
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="TERRA Scientific API",
    description=(
        "Scientific backend for the TERRA Planetary Digital Twin. "
        "Provides Earth-system data processing, mapping, "
        "time-series analysis, anomalies, seasonal analysis "
        "and SOM analysis."
    ),
    version="8.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

DATA_DIR.mkdir(
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "TERRA",
        "system": "Planetary Digital Twin",
        "version": "8.1.0",
        "status": "online",
        "docs": "/docs",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "engine": "TERRA Scientific Engine",
        "version": "8.1.0",
    }


# ============================================================
# DATASET SUMMARY
# ============================================================

@app.post("/dataset/summary")
async def dataset_info(
    file: UploadFile = File(...)
):

    suffix = Path(
        file.filename
    ).suffix

    temp_path = (
        DATA_DIR /
        f"uploaded{suffix}"
    )

    content = await file.read()

    temp_path.write_bytes(
        content
    )

    try:

        result = dataset_summary(
            str(temp_path)
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# ANALYSIS
# ============================================================

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

    suffix = Path(
        file.filename
    ).suffix

    temp_path = (
        DATA_DIR /
        f"analysis_input{suffix}"
    )

    temp_path.write_bytes(
        await file.read()
    )

    try:

        ds = open_data(
            str(temp_path)
        )

        actual_variable = detect_variable(
            ds,
            variable or None,
        )

        # ----------------------------------------------------
        # XARRAY VARIABLE
        # ----------------------------------------------------

        if hasattr(ds, "data_vars"):

            field = ds[
                actual_variable
            ]

            field = convert_units(
                field,
                actual_variable,
                unit,
            )

            if any(
                x is not None
                for x in [
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

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        output_name = (
            f"terra_{analysis}_"
            f"{actual_variable}.png"
        )

        output_path = (
            OUTPUT_DIR /
            output_name
        )

        if analysis == "map":

            scientific_map(
                field,
                actual_variable,
                str(output_path),
            )

        elif analysis == "seasonal":

            seasonal_map(
                field,
                actual_variable,
                str(output_path),
            )

        elif analysis == "anomaly":

            anomaly_map(
                field,
                actual_variable,
                str(output_path),
            )

        elif analysis == "timeseries":

            time_series(
                field,
                actual_variable,
                str(output_path),
                latitude,
                longitude,
            )

        elif analysis == "som":

            result = train_som(
                field
            )

            return {
                "status": "success",
                "analysis": "som",
                "variable": actual_variable,
                "result": result,
            }

        else:

            raise ValueError(
                f"Unknown analysis: {analysis}"
            )

        return {
            "status": "success",
            "analysis": analysis,
            "variable": actual_variable,
            "output": (
                f"/outputs/{output_name}"
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# OUTPUT FILE
# ============================================================

@app.get("/outputs/{filename}")
def output_file(
    filename: str
):

    path = (
        OUTPUT_DIR /
        filename
    )

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="Output not found.",
        )

    return FileResponse(
        path
    )