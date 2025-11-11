# 013-object_tracking

## Test workflows

Download and build EDGELESS (see building instructions in that repo).
Make sure that `edgeless_inabox` and `edgeless_cli` can be executed, e.g.,
after building EDGELESS in release mode:

```shell
alias edgeless_cli=$PWD/target/release/edgeless_cli
alias edgeless_inabox=$PWD/target/release/edgeless_inabox
```

Build viewer from this repo:

```shell
cd viewer && cargo build --release && cd -
```

Build all WASM functions in this repo:

```shell
for f in rust_functions/* ; do
  cd $f
  edgeless_cli function build function.json
  cd -
done
```

### Image identification

1. Shell A: `edgeless_inabox -t`
2. Shell A: `edgeless_inabox`
3. Shell B: `ID=$(edgeless_cli workflow start workflow-identify.json)`
4. Shell C: `viewer/target/release/viewer` (from root of this repo)
5. Shell D: `wget https://upload.wikimedia.org/wikipedia/commons/b/ba/Atlanta_75.85.jpg`
6. Shell D: `curl --data-binary @Atlanta_75.85.jpg "localhost:7007?wf_id=$ID"`
7. Shell B: `edgeless_cli workflow stop all`
8. From a browser check http://localhost:3000/
   - You should see a picture of a highway in Atlanta
9. Check the content of the file `info.log` in Shell A's working directory
   - You should see a single line ending with `{"width":2492,"height":1803}` 

### Object tracking

1. Shell A: `edgeless_inabox -t`
2. Modify the file `node.toml` by adding the following lines:

```ini
[[resources.serverless_provider]]
class_type = "obj_detect"
version = "0.1"
function_url = "http://localhost:5000"
provider = "obj_detect-1"
```

3. Shell A: `edgeless_inabox`
4. Shell B: install requirements and start the `obj_detect` serverless function:

```shell
cd openfaas_resources/obj_detect
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python index.py
```

5. Shell C: `ID=$(edgeless_cli workflow start workflow-track.json)`
6. Shell D: `viewer/target/release/viewer` (from root of this repo)
8. Shell E: `wget https://upload.wikimedia.org/wikipedia/commons/b/ba/Atlanta_75.85.jpg`
9. Shell E: `curl --data-binary @Atlanta_75.85.jpg "localhost:7007?wf_id=$ID"`
10. Shell C: `edgeless_cli workflow stop all`
11. From a browser check http://localhost:3000/
   - You should see a picture of a highway in Atlanta with a bounding box
     drawn around some of the cars
