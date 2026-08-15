# masscan 0.0.0.0-255.255.255.255 -p 25565 --rate 25000000 --exclude 255.255.255.255 -oJ output.json

import json
import ijson

past = set()
first = True

inputFiles = ["output1.json", "output2.json"]

with open("merged.json", "w") as outfile:
    outfile.write("[")

    for filename in inputFiles:
        with open(filename, "r") as infile:
            for entry in ijson.items(infile, "item", multiple_values=True):
                ip = entry.get("ip")
                port = portInfo.get("port")
                timestamp = entry.get("timestamp")

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