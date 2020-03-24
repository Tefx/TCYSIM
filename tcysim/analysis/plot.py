from tcysim.framework.layout.layout import LayoutItem

from bisect import bisect_left
import plotly.graph_objects as go
import numpy as np

from tcysim.utils import V3


class PlotItem:
    def __init__(self, layout_item: LayoutItem, frame=False, precision_digital=6):
        self.layout_item = layout_item
        self.x0, self.y0, _ = layout_item.transform_to(V3.zero(), "g")
        self.x1, self.y1, _ = layout_item.transform_to(layout_item.size, "g")
        self.x0 = round(self.x0, precision_digital)
        self.y0 = round(self.y0, precision_digital)
        self.x1 = round(self.x1, precision_digital)
        self.y1 = round(self.y1, precision_digital)

        if self.x0 > self.x1:
            self.x0, self.x1 = self.x1, self.x0

        if self.y0 > self.y1:
            self.y0, self.y1 = self.y1, self.y0

        self.idx_x0 = -1
        self.idx_x1 = -1
        self.idx_y0 = -1
        self.idx_y1 = -1

        self.frame = frame

    def find_range(self, plot_set):
        self.idx_x0 = bisect_left(plot_set.xs, self.x0)
        self.idx_x1 = bisect_left(plot_set.xs, self.x1)
        self.idx_y0 = bisect_left(plot_set.ys, self.y0)
        self.idx_y1 = bisect_left(plot_set.ys, self.y1)

    def assign_value(self, zs, value):
        for i in range(self.idx_x0, self.idx_x1):
            for j in range(self.idx_y0, self.idx_y1):
                zs[i, j] = value


class PlotSet:
    def __init__(self, yard_size_x, yard_size_y):
        self.max_x = yard_size_x
        self.max_y = yard_size_y
        self.items = {}
        self.xs = None
        self.ys = None
        self.built = False

    def add_item(self, idx, layout_item: LayoutItem, frame=False, precision_digital=2):
        self.items[idx] = PlotItem(layout_item, frame, precision_digital)

    @staticmethod
    def _compress_coords(ls):
        last = -1
        for x in sorted(ls):
            if x > last + 1e-6:
                yield x
                last = x

    def clear(self):
        self.items = {}
        self.built = False

    def build(self):
        if not self.built:
            self.xs = [0, self.max_x]
            self.ys = [0, self.max_y]
            for item in self.items.values():
                self.xs.extend((item.x0, item.x1))
                self.ys.extend((item.y0, item.y1))
            self.xs = list(self._compress_coords(self.xs))
            self.ys = list(self._compress_coords(self.ys))
            for item in self.items.values():
                item.find_range(self)
            self.built = True

    def plot(self, data=None, **kwargs):
        fig = go.Figure()
        fig.update_xaxes(range=(0, self.max_x), showgrid=False)
        fig.update_yaxes(range=(0, self.max_y), showgrid=False)

        all_frame = False
        if data is not None:
            self.build()
            if not isinstance(data, dict) and hasattr(data, "to_dict"):
                data = data.to_dict()
            zs = np.zeros((len(self.xs) - 1, len(self.ys) - 1), np.float)
            zmin = np.inf
            zmax = -np.inf
            for idx, value in data.items():
                if idx in self.items:
                    zmin = min(zmin, value)
                    zmax = max(zmax, value)
                    self.items[idx].assign_value(zs, value)
            color_scale = kwargs.get("colorscale", "Reds")
            zmin = kwargs.get("zmin", zmin)
            zmax = kwargs.get("zmax", zmax)
            fig.add_trace(go.Heatmap(z=zs.T, x=self.xs, y=self.ys,
                                     colorscale=color_scale,
                                     zmin=zmin, zmax=zmax, zauto=False,
                                     **kwargs))
        else:
            all_frame = True

        fig.add_shape(go.layout.Shape(type="rect",
                                      x0=0, y0=0, x1=self.max_x, y1=self.max_y,
                                      line=dict(width=1)))

        for item in self.items.values():
            if all_frame or item.frame:
                fig.add_shape(go.layout.Shape(type="rect",
                                              x0=item.x0,
                                              y0=item.y0,
                                              x1=item.x1,
                                              y1=item.y1,
                                              line=dict(width=1)))
        fig.update_shapes(dict(xref='x', yref='y'))
        return fig


def plot_layout(yard, blocks=True, lanes=False):
    fig = go.Figure()
    fig.update_xaxes(range=(0, 4000), showgrid=False)
    fig.update_yaxes(range=(0, 1000), showgrid=False)

    trace = []

    for bid, block in yard.blocks.items():
        if blocks:
            x0, y0, _ = block.offset
            x1, y1, _ = block.coord_l2g(block.size)
            fig.add_shape(x0=x0, y0=y0, x1=x1, y1=y1, layer="below",
                          line=dict(color="RoyalBlue", width=1),
                          fillcolor="LightSkyBlue")
            trace.append(block.center_coord("g").to_list()[:2] + [str(bid)])

        if lanes:
            for lid, lane in block.lanes.items():
                x0, y0, _ = lane.offset
                x1, y1, _ = lane.coord_l2g(lane.size)
                fig.add_shape(x0=x0, y0=y0, x1=x1, y1=y1, layer="below",
                              line=dict(color="LightSkyBlue"))
                trace.append(lane.center_coord("g").to_list()[:2] + [lid])

    x, y, text = zip(*trace)
    fig.add_trace(go.Scatter(x=x, y=y, text=text, mode="text"))
    return fig
