from __future__ import annotations

import time
from collections import deque

import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget

from . import theme

pg.setConfigOptions(antialias=True)


class ChartView(QWidget):
    """مخطط زمني لسرعات التحميل والرفع الإجمالية."""

    def __init__(self, max_points: int = 240, window_sec: int = 300, parent=None):
        super().__init__(parent)
        self.window_sec = window_sec
        self.t: deque[float] = deque(maxlen=max_points)
        self.down: deque[float] = deque(maxlen=max_points)
        self.up: deque[float] = deque(maxlen=max_points)

        axis = pg.DateAxisItem(orientation="bottom")
        self.plot = pg.PlotWidget(axisItems={"bottom": axis})
        self.plot.setBackground(theme.SURFACE)
        self.plot.showGrid(x=True, y=True, alpha=0.18)
        self.plot.setMouseEnabled(x=True, y=False)
        self.plot.setLabel("left", "KB/s", color=theme.MUTED)
        self.plot.getAxis("left").enableAutoSIPrefix(False)
        self.plot.getAxis("left").setPen(pg.mkPen(theme.BORDER))
        self.plot.getAxis("bottom").setPen(pg.mkPen(theme.BORDER))
        self.plot.getAxis("left").setTextPen(pg.mkPen(theme.MUTED))
        self.plot.getAxis("bottom").setTextPen(pg.mkPen(theme.MUTED))

        self.curve_down = self.plot.plot(
            [], [],
            pen=pg.mkPen(theme.DOWN, width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(theme.DOWN),
            fillLevel=0,
            brush=pg.mkBrush(56, 189, 248, 38),
            name="التحميل",
        )
        self.curve_up = self.plot.plot(
            [], [],
            pen=pg.mkPen(theme.UP, width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(theme.UP),
            fillLevel=0,
            brush=pg.mkBrush(52, 211, 153, 30),
            name="الرفع",
        )

        legend = self.plot.addLegend(offset=(-10, 10))
        legend.setLabelTextColor(theme.TEXT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.plot)

    def add_point(self, down_bps: float, up_bps: float, ts: float | None = None) -> None:
        ts = time.time() if ts is None else ts
        self.t.append(ts)
        # نعرض بالقيم بالكيلوبايت لتكون الأرقام مريحة على المحور
        self.down.append(max(0.0, down_bps) / 1024.0)
        self.up.append(max(0.0, up_bps) / 1024.0)
        xs = list(self.t)
        self.curve_down.setData(xs, list(self.down))
        self.curve_up.setData(xs, list(self.up))
        peak = max(max(self.down, default=0.0), max(self.up, default=0.0), 5.0)
        self.plot.setYRange(0, peak * 1.25, padding=0)
        span = max(0.0, ts - xs[0])
        window = max(60.0, min(float(self.window_sec), span + 15.0))
        self.plot.setXRange(ts - window, ts, padding=0)

    def clear(self) -> None:
        self.t.clear()
        self.down.clear()
        self.up.clear()
        self.curve_down.setData([], [])
        self.curve_up.setData([], [])
