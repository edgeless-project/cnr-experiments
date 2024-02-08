# Experiment 001 - Sub-experiment chain-4-var-load

## Run

Setup the testbed with a Raspberry Pi then:

```bash
NODE=rpi ./run.sh
```

Repeat with an NVIDIA Jetson NX:

```bash
NODE=jetson ./run.sh
```

## Post-processing

Post-process `output.csv` database of output metrics with:

```bash
python3 post.py
```

## Visualization

Gnuplot scripts are included in the `graph/` directory, try:

```bash
cd graphs ; for i in *.plt ; do gnuplot -persist $i ; done ; cd -
```

## Artifacts

You can download the artifacts of the experiments with:

```bash
../../../scripts/download-artifacts.sh
```
