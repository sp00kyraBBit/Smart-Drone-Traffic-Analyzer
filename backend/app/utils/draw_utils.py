import cv2


def draw_box_and_label(frame, bbox, label: str, counted: bool = False):
    x1, y1, x2, y2 = bbox
    color = (0, 255, 0) if counted else (0, 200, 255)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        frame,
        label,
        (x1, max(20, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
        cv2.LINE_AA,
    )


def draw_counting_line(frame, line_points):
    # Accept either ((x1,y1),(x2,y2)) or (x1,y1,x2,y2)
    if len(line_points) == 2:
        (x1, y1), (x2, y2) = line_points
    else:
        x1, y1, x2, y2 = line_points

    cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
    cv2.putText(
        frame,
        "Reference Line",
        (x1, max(30, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 0, 255),
        2,
        cv2.LINE_AA,
    )


def draw_summary_overlay(frame, summary_dict: dict):
    y = 30
    for key, value in summary_dict.items():
        text = f"{key}: {value}"
        cv2.putText(
            frame,
            text,
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        y += 30


def draw_roi(frame, roi):
    x1, y1, x2, y2 = roi
    cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 255, 100), 2)
    cv2.putText(
        frame,
        "Counting ROI",
        (x1, max(25, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (100, 255, 100),
        2,
        cv2.LINE_AA,
    )