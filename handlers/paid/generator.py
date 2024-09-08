import requests, os, json

class PaidGenHandler:
    def __init__(self) -> None:
        self.rage_presets = None
        self.normal_presets = None
        
        self.url = "https://matcha-gen.onrender.com"
        self.predict_endpoint = self.url + "/predict"
        
        current_dir = os.path.dirname(__file__)
        handlers_dir = os.path.dirname(current_dir)
        bot_dir = os.path.dirname(handlers_dir)
        with open(os.path.join(bot_dir, 'data', 'paid', 'xy.json'), 'r', encoding='utf-8') as f:
            sets = json.load(f)["type"]
            self.rage_presets = sets["rage"]["ping"]
            self.normal_presets = sets["normal"]["ping"]
        
    def calculate(self, ping, mode: str = "Rage", ai: bool = False):
        if not ai:
            presets = None
            if mode == "rage":
                presets = self.rage_presets
            else:
                presets = self.normal_presets
                
            ping_values = sorted(map(int, presets.keys()))  
            xy_set = {"x": None, "y": None}
            
            if ping <= ping_values[0]:  
                return presets[str(ping_values[0])]
            if ping >= ping_values[-1]:  
                return presets[str(ping_values[-1])]

            for i in range(len(ping_values) - 1):
                if ping_values[i] <= ping <= ping_values[i + 1]:
                    ping1 = ping_values[i]
                    ping2 = ping_values[i + 1]

                    x1, y1 = presets[str(ping1)]["x"], presets[str(ping1)]["y"]
                    x2, y2 = presets[str(ping2)]["x"], presets[str(ping2)]["y"]

                    t = (ping - ping1) / (ping2 - ping1)
                    xy_set["x"] = x1 + t * (x2 - x1)
                    xy_set["y"] = y1 + t * (y2 - y1)

                    return xy_set
        else:
            try:
                model = 0 if mode == "Rage" else 1
                response = requests.get(f"{self.predict_endpoint}?ping={int(round(ping))}&model={model}").json()

                if "x" not in response or "y" not in response:
                    raise KeyError(f"Missing 'x' or 'y' in response: {response}")
                
                return {"x": response["x"], "y": response["y"]}
            
            except requests.exceptions.RequestException as e:
                return {"error": f"Request error: {str(e)}"}
            
            except KeyError as k:
                return {"error": f"Key error: {str(k)}"}
            
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}