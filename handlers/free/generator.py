class FreeGenHandler:
    def __init__(self) -> None:
        self.preset_x = [
            (1, 10), (40, 7.12), (80, 6.24), (120, 5.76), (140, 4.8),
            (160, 4.32), (180, 3.84), (200, 3.36)
        ]
        self.preset_y = [
            (1, 10), (40, 9.01), (80, 8.12), (120, 7.63), (140, 6.8),
            (160, 6.32), (180, 5.84), (200, 5.36)
        ]
    
    def calculate(self, ping):
        def interpolate(preset, ping):
            settings = sorted(preset)
            if ping <= settings[0][0]:  
                return settings[0][1]
            if ping >= settings[-1][0]: 
                return settings[-1][1]

            for i in range(len(settings) - 1):
                if settings[i][0] <= ping <= settings[i + 1][0]:
                    x1, y1 = settings[i]
                    x2, y2 = settings[i + 1]
                    t = (ping - x1) / (x2 - x1)
                    return y1 + t * (y2 - y1)

        x = interpolate(self.preset_x, ping)
        y = interpolate(self.preset_y, ping)

        return {"x": x, "y": y}
