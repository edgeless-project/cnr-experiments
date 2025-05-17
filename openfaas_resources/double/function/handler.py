def handle(event, context):
    output = 2.0 * float(event.body.decode("utf8"))

    return {"statusCode": 200, "body": f"{output}".encode("utf8")}
