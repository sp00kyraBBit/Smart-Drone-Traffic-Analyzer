from pathlib import Path
from typing import List, Dict

import pandas as pd


def build_summary_dataframe(summary: Dict) -> pd.DataFrame:
    rows = [
        {"Metric": "Total Unique Vehicles",   "Value": summary.get("total_unique_vehicles", 0)},
        {"Metric": "Cars",                    "Value": summary.get("car", 0)},
        {"Metric": "Trucks",                  "Value": summary.get("truck", 0)},
        {"Metric": "Buses",                   "Value": summary.get("bus", 0)},
        {"Metric": "Motorcycles",             "Value": summary.get("motorcycle", 0)},
        {"Metric": "Processing Duration (s)", "Value": summary.get("processing_duration_sec", 0)},
    ]
    return pd.DataFrame(rows)


def build_counted_vehicles_dataframe(count_events: List[dict]) -> pd.DataFrame:
    """
    One row per unique vehicle — the frame/timestamp at which it was
    officially counted (first stable detection).
    """
    if not count_events:
        return pd.DataFrame(columns=[
            "vehicle_id", "vehicle_type",
            "first_counted_frame", "first_counted_timestamp_sec", "count_reason",
        ])

    df = pd.DataFrame(count_events)

    rename = {
        "canonical_id":        "vehicle_id",
        "count_frame":         "first_counted_frame",
        "count_timestamp_sec": "first_counted_timestamp_sec",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # Keep only the columns we want, in order
    cols = ["vehicle_id", "vehicle_type", "first_counted_frame",
            "first_counted_timestamp_sec", "count_reason"]
    df = df[[c for c in cols if c in df.columns]]

    return df


def build_vehicle_timeline_dataframe(detection_logs: List[dict]) -> pd.DataFrame:
    """
    Every frame where a vehicle was detected — full frame + timestamp trail
    per vehicle_id.  This satisfies the requirement for frame and timestamp
    data for when vehicles were detected.
    """
    if not detection_logs:
        return pd.DataFrame(columns=[
            "vehicle_id", "vehicle_type", "frame_index", "timestamp_sec",
            "confidence", "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2",
            "inside_roi", "counted_flag",
        ])

    df = pd.DataFrame(detection_logs)

    rename = {"track_id": "vehicle_id"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # Columns to expose in the timeline sheet
    keep = [
        "vehicle_id", "vehicle_type", "frame_index", "timestamp_sec",
        "confidence", "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2",
        "inside_roi", "counted_flag",
    ]
    df = df[[c for c in keep if c in df.columns]]

    # Sort by vehicle then frame for readability
    if "vehicle_id" in df.columns and "frame_index" in df.columns:
        df = df.sort_values(["vehicle_id", "frame_index"]).reset_index(drop=True)

    return df


def build_detection_log_dataframe(detection_logs: List[dict]) -> pd.DataFrame:
    """Raw full log — every detection with all fields."""
    if not detection_logs:
        return pd.DataFrame()
    return pd.DataFrame(detection_logs)


def _autofit_columns(worksheet):
    for col in worksheet.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                cell_len = len(str(cell.value)) if cell.value is not None else 0
                if cell_len > max_len:
                    max_len = cell_len
            except Exception:
                pass
        worksheet.column_dimensions[col_letter].width = min(max_len + 4, 50)


def export_excel(
    report_path: Path,
    summary: Dict,
    count_events: List[dict],
    detection_logs: List[dict],
) -> None:
    summary_df      = build_summary_dataframe(summary)
    counted_df      = build_counted_vehicles_dataframe(count_events)
    timeline_df     = build_vehicle_timeline_dataframe(detection_logs)
    raw_log_df      = build_detection_log_dataframe(detection_logs)

    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer,  sheet_name="Summary",         index=False)
        counted_df.to_excel(writer,  sheet_name="CountedVehicles",  index=False)
        timeline_df.to_excel(writer, sheet_name="VehicleTimeline",  index=False)
        raw_log_df.to_excel(writer,  sheet_name="RawDetectionLog",  index=False)

        for sheet_name in writer.sheets:
            _autofit_columns(writer.sheets[sheet_name])