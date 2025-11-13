# SPDX-FileCopyrightText: © 2025 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
# SPDX-License-Identifier: MIT

import base64
import io
from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np
import json
import torch

from ultralytics import YOLO  # type: ignore


def prepare_model(model_path: str = "yolov8n.pt"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = YOLO(model_path)
    model.to(device)
    print(f"✅ Model loaded on {device}")
    return model, device


model, device = prepare_model("yolov8n.pt")


def detect_objects_from_base64(
    model, device, image_b64: str, conf_threshold: float = 0.5
) -> Dict[str, Any]:
    """Run YOLOv8 object detection on a base64-encoded JPEG."""

    # Decode image
    img = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")

    # Run inference on the image (numpy array expected)
    results = model.predict(
        source=np.array(img), conf=conf_threshold, device=device, verbose=False
    )[0]

    boxes = results.boxes.xyxy.cpu().numpy().tolist()
    confs = results.boxes.conf.cpu().numpy().tolist()
    class_ids = results.boxes.cls.cpu().numpy().astype(int).tolist()
    labels = [model.names[i] for i in class_ids]

    output: Dict[str, Any] = {
        "boxes": boxes,
        "labels": labels,
        "scores": confs,
    }

    output["image_b64"] = image_b64

    return output


def handle(event, context):
    output = detect_objects_from_base64(model, device, event.body.decode("utf8"), 0.5)

    return {"statusCode": 200, "body": f"{json.dumps(output)}"}
