import requests

repo = "kgurchiek/Minecraft-Server-Scanner"
path = "ips"

request = requests.get("https://api.github.com/repos/{}/contents/{}?ref=main".format(repo, path))
if request.status_code == 200:
    data = request.json()

    contentSHA = data["sha"]
    download = data["download_url"]

commitDate = None

request = requests.get("https://api.github.com/repos/{}/commits?path={}&sha=main".format(repo, path))
if request.status_code == 200:
    found = False

    for commit in request.json():
        commitSHA = commit["sha"]

        request = requests.get("https://api.github.com/repos/{}/commits/{}".format(repo, commitSHA))
        if request.status_code == 200:
            commitData = request.json()

            for record in commitData["files"]:
                if record["filename"] == "ips" and record["sha"] == contentSHA:
                    found = True

                    commitDate = commitData["commit"]["committer"]["date"]
                    break

        if found:
            break

request = requests.get(download)
if request.status_code == 200:
    with open("ips-{}".format(commitDate), "wb") as file:
        file.write(request.content)

print("Downloaded. Commit date:", commitDate)