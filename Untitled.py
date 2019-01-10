#!/usr/bin/env python
# coding: utf-8

# In[2]:
import json, time, itertools
import requests as rq
import numpy as np
import ast, re

def fetch_create_graph():
    data = rq.get("http://api.steampowered.com/ISteamApps/GetAppList/v0001")
    print(data.text)
    with open("data.txt", "w") as f_data:
        f_data.write(data.text)

    parsed_data = json.loads(data.text)
    applist = parsed_data['applist']['apps']['app']

    top = rq.get("http://steamspy.com/api.php?request=all")
    parsed_top = json.loads(top.text)
    top_keys = [x for x in parsed_top.keys()]
    top_10k = {}
    for i in range(10000):
        top_10k[parsed_top[top_keys[i]]['name']] = (i, top_keys[i])

    with open("top10k.txt", "w") as f:
        json.dump(top_10k, f)

    game_info = {}
    required_keys = ["categories", "developers", "genres", "metacritic", "platforms", "required_age", "release_date"]
    sets = {k: set() for k in required_keys[:3]}
    top_keys = [x for x in top_10k.keys()]
    for lc in range(13, 30):
        for i in range(200 * lc, 200 * (lc + 1)):
            game = "https://store.steampowered.com/api/appdetails?appids=%s" % (top_10k[top_keys[i]][1])
            rq_data = rq.get(game)
            if "null" == rq_data.text:
                break
            game_data = json.loads(rq_data.text)[top_10k[top_keys[i]][1]]
            if "data" not in game_data.keys():
                continue
            else:
                game_data = game_data["data"]
            game_info[top_keys[i]] = {}
            for k in required_keys:
                if k not in game_data.keys():
                    continue
                if k == "categories" or k == "genres":
                    value = [x["description"] for x in game_data[k] if "steam" not in x["description"].lower()
                             and "in-app" not in x["description"].lower()]
                    sets[k] |= set(value)
                elif k == "metacritic":
                    value = game_data[k]["score"]
                elif k == "release_date":
                    value = game_data[k]["date"]
                else:
                    value = game_data[k]

                if k == "developers":
                    sets[k] |= set(value)
                game_info[top_keys[i]][k] = value
        with open("data_top%s.txt" % (str(lc)), "w") as f_data:
            f_data.write(json.dumps(game_info))
        time.sleep(125)

    costs = np.zeros((10000, 10000), dtype=np.int32)
    for val, k in enumerate(required_keys[:3]):
        for elem in list(sets[k]):
            games = [x for x in game_info.keys() if k in game_info[x].keys() and elem in game_info[x][k]]
            indexes = [top_10k[x][0] for x in games]
            metacritics = []
            for x in games:
                if "metacritic" in game_info[x].keys():
                    metacritics.append(game_info[x]["metacritic"])
                else:
                    metacritics.append(1)
            pairs = itertools.combinations(indexes, 2)
            for i in pairs:
                costs[i[1]][i[0]] += (val + 2) * ((metacritics[indexes.index(i[0])] / 100) + 1)
                costs[i[0]][i[1]] += (val + 2) * ((metacritics[indexes.index(i[1])] / 100) + 1)

    np.set_printoptions(threshold=np.nan)
    with open("costs.txt", "w") as f:
        f.write(str(costs))


if __name__ == "__main__":

    top_10k = {}
    costs = None

    with open('top10k.txt') as f:
        top_10k = json.load(f)

    with open('costs.txt') as f:
        costs = f.read()
        costs.spl
        ast.literal_eval(costs)

    print(costs)

    top_keys = [x for x in top_10k.keys()]
    print(top_10k["Grand Theft Auto V"])

    k = np.max(costs[top_10k["Grand Theft Auto V"][0]])
    print(costs[top_10k["Grand Theft Auto V"][0]])
    print(k)

    the_id = np.where(costs[top_10k["Grand Theft Auto V"][0]] >= 0)
    rez = [x for x in top_keys for k in the_id[0] if top_10k[x][0] == k]
    print(rez)

    k = np.max(costs[:][top_10k["Grand Theft Auto V"][0]])
    the_id = np.where(costs[:][top_10k["Grand Theft Auto V"][0]] >= k - 10)
    rez = [x for x in top_keys for k in the_id[0] if top_10k[x][0] == k]
    print(rez)
