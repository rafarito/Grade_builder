HORARIOS_MAP = {
    "1": ("08:40", "09:30"),
    "2": ("09:30", "10:20"),
    "3": ("10:20", "11:10"),
    "4": ("11:10", "12:00"),
    "5": ("12:00", "12:50"),
    "6": ("12:50", "13:40"),
    "7": ("13:40", "14:30"),
    "8": ("14:30", "15:20"),
    "9": ("15:20", "16:10"),
    "10": ("16:10", "17:00"),
    "11": ("17:00", "17:50"),
    "12": ("17:50", "18:40"),
    "13": ("18:40", "19:30"),
    "14": ("19:30", "20:20"),
    "15": ("20:20", "21:10"),
    "16": ("21:10", "22:00")
}

def get_real_time(codigo):
    return HORARIOS_MAP.get(str(codigo), ("??:??", "??:??"))

def get_slots_range(ini, fim):
    try:
        start_code = int(ini)
        end_code = int(fim)
        if start_code <= end_code:
            return [str(c) for c in range(start_code, end_code + 1)]
    except ValueError:
        pass
    return []
