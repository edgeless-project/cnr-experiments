# obj_detection

Perform object detection on an incoming image encoded with base64.

## Test

In one shell:

```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python index.py
```

In another shell download an example photo of a highway from Wikipedia:

```shell
wget https://upload.wikimedia.org/wikipedia/commons/b/ba/Atlanta_75.85.jpg
```

Then from Mac OS:

```shell
base64 -i Atlanta_75.85.jpg -o - | curl -d@- localhost:5000 > output
```

Or from Linux:

```shell
base64 < Atlanta_75.85.jpg  | curl -d@- localhost:5000 > output
```

You should obtain in output a JSON file with the following fields:

- `boxes`: the bounding boxes (xyxy) for each object;
- `labels`: the labels associated with objects;
- `scores`: the detections' confidence scores;
- `image`: the base64-encoded input image.

Try:

```shell
python3 -m json.tool output | head -n 20
```

Should give:

```
{
    "boxes": [
        [
            303.7247314453125,
            1392.460693359375,
            459.79669189453125,
            1510.0565185546875
        ],
        [
            376.9408874511719,
            1492.3743896484375,
            563.012939453125,
            1640.4410400390625
        ],
        [
            1959.7264404296875,
            1576.38818359375,
            2150.977294921875,
            1716.72216796875
        ],
```

## Docker instructions

Tested on NVIDIA AGX Orin at R35 (Jetpack5), which also needed:

```shell
apt-get install nvidia-jetpack
```

Build Docker image with:

```shell
docker build -t obj_detect .
```

Run container with:

```shell
docker run -d --runtime nvidia -p 5000:5000 obj_detect
```
