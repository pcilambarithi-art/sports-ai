"""
OpenCV Sports Video Movement & Technique Analyzer.

Uses OpenCV (Farneback optical flow + MOG2 foreground contour tracking) to:
- Extract video metadata (FPS, duration, resolution, frame count)
- Compute motion intensity timeline over sampled frames
- Track primary moving subject bounding box & centroid trajectory
- Detect peak-activity key moments
- Render annotated visual feedback keyframe PNG images

Explicitly distinguishes OpenCV computer vision telemetry from the user's
tabular ExtraTreesRegressor calorie prediction model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def analyze_sports_video(
    video_path: Path,
    output_frames_dir: Path,
    max_sampled_frames: int = 90,
) -> Dict[str, Any]:
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError("OpenCV could not open the uploaded video file. Verify codec/format.")

    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 0.0 or np.isnan(fps):
            fps = 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        if width <= 0 or height <= 0:
            raise ValueError("Invalid video stream dimensions detected.")

        sample_step = max(1, frame_count // max_sampled_frames) if frame_count > 0 else 5

        bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=120, varThreshold=25, detectShadows=False
        )

        prev_gray: Optional[np.ndarray] = None
        motion_timeline: List[Dict[str, Any]] = []
        trajectory_points: List[Dict[str, Any]] = []
        cached_frames: List[Tuple[int, float, float, np.ndarray, Optional[Tuple[int, int, int, int]]]] = []

        frame_idx = 0
        processed_frames = 0
        actual_frames_read = 0

        # Scale down for fast optical flow computation
        target_w = min(480, width)
        scale = target_w / float(width)
        target_h = max(64, int(height * scale))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            actual_frames_read += 1

            if frame_idx % sample_step != 0:
                frame_idx += 1
                continue

            resized = cv2.resize(frame, (target_w, target_h))
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            timestamp_sec = round(frame_idx / fps, 2)

            # Foreground mask & primary moving contour tracking
            fg_mask = bg_subtractor.apply(resized)
            fg_mask = cv2.medianBlur(fg_mask, 5)
            _, fg_thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(fg_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            bbox: Optional[Tuple[int, int, int, int]] = None
            min_contour_area = (target_w * target_h) * 0.004
            valid_contours = [c for c in contours if cv2.contourArea(c) >= min_contour_area]
            if valid_contours:
                largest = max(valid_contours, key=cv2.contourArea)
                x, y, bw, bh = cv2.boundingRect(largest)
                bbox = (x, y, bw, bh)
                cx_norm = round((x + bw / 2.0) / target_w, 3)
                cy_norm = round((y + bh / 2.0) / target_h, 3)
                trajectory_points.append(
                    {
                        "timestamp_sec": timestamp_sec,
                        "frame_idx": frame_idx,
                        "x_norm": cx_norm,
                        "y_norm": cy_norm,
                        "area_pct": round((bw * bh) / float(target_w * target_h) * 100.0, 2),
                    }
                )

            # Dense optical flow motion intensity
            motion_score = 0.0
            if prev_gray is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                )
                mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                # Normalize motion intensity cleanly
                motion_score = round(float(np.mean(mag) * 10.0), 2)

            prev_gray = gray
            motion_timeline.append(
                {
                    "timestamp_sec": timestamp_sec,
                    "frame_idx": frame_idx,
                    "motion_intensity": motion_score,
                }
            )
            cached_frames.append((frame_idx, timestamp_sec, motion_score, resized.copy(), bbox))
            processed_frames += 1
            frame_idx += 1

            if processed_frames >= max_sampled_frames + 10:
                break
    finally:
        cap.release()

    if actual_frames_read == 0 or not motion_timeline:
        raise ValueError("No decodable video frames were found in the uploaded file.")

    final_frame_count = frame_count if frame_count > 0 else actual_frames_read
    duration_seconds = round(final_frame_count / fps, 2)

    intensities = np.array([m["motion_intensity"] for m in motion_timeline], dtype=float)
    mean_motion = round(float(intensities.mean()), 2)
    peak_motion = round(float(intensities.max()), 2)
    active_threshold = max(2.0, mean_motion * 0.65)
    active_ratio = round(float(np.mean(intensities >= active_threshold) * 100.0), 1)

    # Identify up to 4 non-overlapping peak key moments
    output_frames_dir.mkdir(parents=True, exist_ok=True)
    sorted_candidates = sorted(
        enumerate(cached_frames),
        key=lambda pair: pair[1][2],
        reverse=True,
    )
    selected_indices: List[int] = []
    min_gap = max(2, len(cached_frames) // 8)
    for idx, _item in sorted_candidates:
        if all(abs(idx - s) >= min_gap for s in selected_indices):
            selected_indices.append(idx)
        if len(selected_indices) >= 4:
            break

    # Fallback: if video is very short or static, pick evenly spaced frames
    if not selected_indices and cached_frames:
        selected_indices = [0]

    selected_indices.sort()
    key_moments: List[Dict[str, Any]] = []

    for rank, c_idx in enumerate(selected_indices, start=1):
        f_idx, ts, score, img, bbox = cached_frames[c_idx]
        annotated = img.copy()

        # Draw centroid trail up to this timestamp
        trail_pts = [
            (int(pt["x_norm"] * annotated.shape[1]), int(pt["y_norm"] * annotated.shape[0]))
            for pt in trajectory_points
            if pt["timestamp_sec"] <= ts
        ][-20:]
        for i in range(1, len(trail_pts)):
            cv2.line(annotated, trail_pts[i - 1], trail_pts[i], (0, 230, 180), 2)

        if bbox is not None:
            x, y, bw, bh = bbox
            cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (34, 211, 238), 2)
            cx, cy = x + bw // 2, y + bh // 2
            cv2.circle(annotated, (cx, cy), 4, (16, 185, 129), -1)

        # HUD overlay
        cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 28), (15, 23, 42), -1)
        hud_text = f"t={ts:.2f}s | Motion={score:.1f} | Frame #{f_idx}"
        cv2.putText(
            annotated,
            hud_text,
            (8, 19),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (241, 245, 249),
            1,
            cv2.LINE_AA,
        )

        frame_filename = f"keyframe_{rank}_f{f_idx}.png"
        frame_out_path = output_frames_dir / frame_filename
        cv2.imwrite(str(frame_out_path), annotated)

        intensity_label = (
            "Peak Burst"
            if score >= max(peak_motion * 0.85, 5.0)
            else ("Active Phase" if score >= active_threshold else "Low-Motion / Setup")
        )
        key_moments.append(
            {
                "rank": rank,
                "timestamp_sec": ts,
                "frame_idx": f_idx,
                "motion_intensity": score,
                "label": intensity_label,
                "image_filename": frame_filename,
            }
        )

    # Spatial movement analysis from centroid trajectory
    feedback_items: List[str] = []
    feedback_items.append(
        f"Processed {processed_frames} sampled frames across {duration_seconds:.1f}s ({width}x{height} @ {fps:.1f} FPS)."
    )
    if active_ratio >= 75.0:
        feedback_items.append(
            f"High continuous movement engagement ({active_ratio}% active frames; peak motion intensity {peak_motion}). Ensure structured recovery intervals if training for repeatability."
        )
    elif active_ratio >= 40.0:
        feedback_items.append(
            f"Balanced work-to-pause cadence ({active_ratio}% active frames; mean motion {mean_motion}, peak {peak_motion})."
        )
    else:
        feedback_items.append(
            f"Intermittent movement profile ({active_ratio}% active frames). Review low-motion segments for setup delays or rest pacing."
        )

    if len(trajectory_points) >= 5:
        xs = np.array([p["x_norm"] for p in trajectory_points])
        ys = np.array([p["y_norm"] for p in trajectory_points])
        x_span = float(xs.max() - xs.min())
        y_span = float(ys.max() - ys.min())
        if x_span > y_span * 1.5:
            feedback_items.append(
                f"Predominantly lateral/horizontal displacement detected (horizontal span {x_span*100:.0f}% vs vertical {y_span*100:.0f}% of frame)."
            )
        elif y_span > x_span * 1.5:
            feedback_items.append(
                f"Predominantly vertical motion detected (vertical span {y_span*100:.0f}% vs horizontal {x_span*100:.0f}% of frame), consistent with vertical jumps, squats, or overhead lifts."
            )
        else:
            feedback_items.append(
                f"Multi-directional movement coverage (horizontal {x_span*100:.0f}%, vertical {y_span*100:.0f}% of frame)."
            )
    else:
        feedback_items.append(
            "Minimal isolated foreground subject displacement detected; for sharper tracking, record from a stable tripod with clear subject contrast."
        )

    return {
        "duration_seconds": duration_seconds,
        "fps": round(fps, 2),
        "frame_count": final_frame_count,
        "resolution": f"{width}x{height}",
        "mean_motion_intensity": mean_motion,
        "peak_motion_intensity": peak_motion,
        "active_movement_ratio_pct": active_ratio,
        "motion_timeline": motion_timeline,
        "trajectory_points": trajectory_points[:120],
        "key_moments": key_moments,
        "feedback_items": feedback_items,
        "analysis_disclaimer": (
            "Visual movement metrics, bounding boxes, and key moments are computed using OpenCV "
            "(Farneback optical flow & MOG2 contour tracking). Your trained ExtraTreesRegressor ML model "
            "is a tabular calorie predictor and is only invoked separately if you link workout biometrics."
        ),
    }
