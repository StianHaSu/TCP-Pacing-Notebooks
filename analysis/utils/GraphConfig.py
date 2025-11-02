
class GraphConfig:

    def __init__(self, filename: str, title: str, cutoff: int,  label: str, include_acks: bool = False, save_plot: bool = False, color = None, marker=None,):
        self.filename: str = filename
        self.title: str = title
        self.cutoff: int = cutoff
        self.label: str = label
        self.include_acks: bool = include_acks
        self.save_plot: bool = save_plot
        self.color: str = color
        self.marker: str = marker