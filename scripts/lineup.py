
import pandas as pd
import tabulate
import json
import datetime


PLAYERS_URL = "https://fantasy.premierleague.com/drf/elements/"


class Lineup(object):

    def __init__(self, starting=None, bench=None, cap=None, vice_cap=None,
                 prices=None):
        if starting is None:
            starting = "lineups/latest.json"
        if type(starting) == list:
            self.starting = starting
            self.bench = bench
            self.cap = cap
            self.vice_cap = vice_cap
            self.prices = prices
            self.players = None
        elif type(starting) == str:
            with open(starting) as f:
                lu_dict = json.loads(f.read())
                self.starting = lu_dict["starting"]
                self.bench = lu_dict["bench"]
                self.cap = lu_dict["captain"]
                self.vice_cap = lu_dict["vice_captain"]
                self.prices = lu_dict["prices"]

    def connect(self, players=None):
        if players is None:
            self.players = pd.read_json(PLAYERS_URL)
            self.players.set_index("code", drop=False, inplace=True)
        else:
            self.players = players
        return self

    def get_name(self, player_id):
        p = self.get_player(player_id)
        return p["first_name"] + " " + p["second_name"]

    def get_player(self, player_id):
        return self.players.loc[player_id]

    def get_cur_cost(self, player_id):
        return self.players.loc[player_id]["now_cost"]

    def get_org_cost(self, player_id):
        return self.prices[str(player_id)]

    def get_selling_price(self, player_id):
        cur_cost = self.get_cur_cost(player_id)
        org_cost = self.get_org_cost(player_id)
        if cur_cost < org_cost:
            return cur_cost
        else:
            profit = cur_cost - org_cost
            fee = profit / 2 + 1
            return org_cost + profit - fee

    def to_dict(self):
        lineup_dict = dict()
        lineup_dict["starting"] = self.starting
        lineup_dict["bench"] = self.bench
        lineup_dict["captain"] = self.cap
        lineup_dict["vice_captain"] = self.vice_cap
        lineup_dict["prices"] = self.prices
        return lineup_dict

    def write(self):
        lu_dict = self.to_dict()
        j_str = json.dumps(lu_dict)
        now = datetime.datetime.now()
        now_f = "lineups/{}.json".format(now.strftime("%d-%m-%y-%H-%M-%S"))
        lat_f = "lineups/latest.json"
        with open(now_f, "w") as f_now, open(lat_f, "w") as f_lat:
            f_now.write(j_str)
            f_lat.write(j_str)

    def __str__(self):
        pos = ["GK", "DEF", "MID", "FOR"]
        s_names, b_names = list(), list()
        s_pos, b_pos = list(), list()
        s_form, b_form = [], []
        s_ppg, b_ppg = [], []

        cap_name = self.get_name(self.cap)
        vice_cap_name = self.get_name(self.vice_cap)

        for i in self.starting:
            name = self.get_name(i)
            if name == cap_name:
                name += " (C)"
            if name == vice_cap_name:
                name += " (VC)"
            s_names.append(name)
            s_pos.append(pos[self.players.loc[i]["element_type"] - 1])
            s_form.append(self.players.loc[i]["form"])
            s_ppg.append(self.players.loc[i]["points_per_game"])

        for i in self.bench:
            p = self.get_player(i)
            b_names.append(p["first_name"] + " " + p["second_name"])
            b_pos.append(pos[p["element_type"] - 1])
            b_form.append(self.players.loc[i]["form"])
            b_ppg.append(self.players.loc[i]["points_per_game"])

        headers = ["Name", "Position", "Form", "PPG"]
        kwargs = dict(headers=headers, tablefmt="fancy_grid")
        s_tab_data = zip(s_names, s_pos, s_form, s_ppg)
        b_tab_data = zip(b_names, b_pos, b_form, b_ppg)
        s_tab = tabulate.tabulate(s_tab_data, **kwargs)
        b_tab = tabulate.tabulate(b_tab_data, **kwargs)
        ret_str = unicode()
        ret_str += "Starting 11\n"
        ret_str += s_tab
        ret_str += "\n\nBench\n"
        ret_str += b_tab
        return ret_str.encode("utf-8", "ignore")



    def __contains__(self, item):
        return item in self.starting or item in self.bench
