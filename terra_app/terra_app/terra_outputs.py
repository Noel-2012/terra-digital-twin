from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr


def _safe(value: Any) -> str:
    return str(value).replace("/", "_").replace("\\", "_").replace(" ", "_")


def save_json(data: dict, path: str):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8",
    )
    return path


def save_dataframe_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=True)
    return path


def series_dataframe(series):
    if isinstance(series, pd.Series):
        df = series.to_frame("value")
        df.index.name = "time"
        return df

    return pd.DataFrame({"value": np.asarray(series)})


def publication_time_series(
    series,
    variable: str,
    units: str = "",
    title: Optional[str] = None,
    output_png: Optional[str] = None,
    output_svg: Optional[str] = None,
):
    df = series_dataframe(series)

    fig, ax = plt.subplots(figsize=(12, 5.8), dpi=160)

    ax.plot(
        df.index,
        df["value"],
        linewidth=1.6,
    )

    ax.set_title(
        title or f"TERRA — {variable}",
        fontsize=15,
        fontweight="bold",
        pad=12,
    )

    ax.set_xlabel("Time", fontsize=11)
    ax.set_ylabel(
        f"{variable} ({units})" if units else variable,
        fontsize=11,
    )

    ax.grid(
        True,
        linestyle="--",
        linewidth=0.6,
        alpha=0.35,
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    if output_png:
        fig.savefig(
            output_png,
            dpi=600,
            bbox_inches="tight",
            facecolor="white",
        )

    if output_svg:
        fig.savefig(
            output_svg,
            format="svg",
            bbox_inches="tight",
            facecolor="white",
        )

    plt.close(fig)

    return output_png or output_svg


def heatmap(
    values,
    x_labels,
    y_labels,
    title,
    output_png,
    xlabel="",
    ylabel="",
    cmap="RdYlBu_r",
):
    arr = np.asarray(values, dtype=float)

    fig, ax = plt.subplots(
        figsize=(12, 7),
        dpi=160,
    )

    image = ax.imshow(
        arr,
        aspect="auto",
        cmap=cmap,
        interpolation="nearest",
    )

    ax.set_xticks(np.arange(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=45, ha="right")

    ax.set_yticks(np.arange(len(y_labels)))
    ax.set_yticklabels(y_labels)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.set_title(
        title,
        fontsize=15,
        fontweight="bold",
        pad=12,
    )

    cbar = fig.colorbar(
        image,
        ax=ax,
        pad=0.02,
    )

    cbar.ax.tick_params(labelsize=9)

    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if np.isfinite(arr[i, j]):
                ax.text(
                    j,
                    i,
                    f"{arr[i, j]:.2f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                )

    fig.tight_layout()

    fig.savefig(
        output_png,
        dpi=600,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    return output_png


def create_pdf_report(
    output_path: str,
    title: str,
    metadata: dict,
    image_paths: list[str],
    summary: str = "",
):
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(output_path) as pdf:

        fig = plt.figure(figsize=(11.69, 8.27))
        fig.patch.set_facecolor("white")

        fig.text(
            0.08,
            0.88,
            title,
            fontsize=22,
            fontweight="bold",
        )

        y = 0.78

        for key, value in metadata.items():
            fig.text(
                0.08,
                y,
                f"{key}: {value}",
                fontsize=11,
            )
            y -= 0.035

        if summary:
            fig.text(
                0.08,
                y - 0.02,
                summary,
                fontsize=11,
                wrap=True,
            )

        pdf.savefig(
            fig,
            bbox_inches="tight",
        )

        plt.close(fig)

        for image_path in image_paths:

            if not image_path:
                continue

            if not Path(image_path).exists():
                continue

            image = plt.imread(image_path)

            fig = plt.figure(figsize=(11.69, 8.27))

            ax = fig.add_axes(
                [0.04, 0.04, 0.92, 0.92]
            )

            ax.imshow(image)
            ax.axis("off")

            pdf.savefig(
                fig,
                bbox_inches="tight",
            )

            plt.close(fig)

    return output_path