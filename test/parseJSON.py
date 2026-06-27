# masscan 0.0.0.0-255.255.255.255 -p 25565 --rate 25000000 --exclude 255.255.255.255 -oJ output.json

import json
import ijson

past = set()
first = True

with open("output.json", "r") as infile, open("cleaned.json", "w") as outfile:
    outfile.write("[")

    for entry in ijson.items(infile, "item", multiple_values=True):
        ip = entry.get("ip")
        timestamp = entry.get("timestamp")

        for portInfo in entry.get("ports", []):
            port = portInfo.get("port")
            key = (ip, port)

            if key in past:
                print("Duplicate: {}:{}".format(ip, port))
                continue

            past.add(key)

            item = {"ip": ip, "port": port, "timestamp": timestamp}

            if not first:
                outfile.write(",\n")
            outfile.write(json.dumps(item))

            first = False

    outfile.write("]")

print("Done!")