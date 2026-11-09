from __future__ import annotations

import time
from collections import deque

import pyqtgraph as pg
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout, QWidget

from . import theme
from ..i18n import tr

pg.setConfigOptions(antialias=True)


def _brush(color: str, alpha: int):
    value = QColor(color)
    value.setAlpha(alpha)
    return pg.mkBrush(value)


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
            brush=_brush(theme.DOWN, 38),
            name=tr("chart.down"),
        )
        self.curve_up = self.plot.plot(
            [], [],
            pen=pg.mkPen(theme.UP, width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(theme.UP),
            fillLevel=0,
            brush=_brush(theme.UP, 30),
            name=tr("chart.up"),
        )

        self.legend = self.plot.addLegend(offset=(-10, 10))
        self.apply_theme()
        # Curves are created before the legend, so populate it immediately.
        # Otherwise the legend stays empty until the language changes.
        self.retranslate()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.plot)

        now = time.time()
        self.plot.setYRange(0, 5, padding=0)
        self.plot.setXRange(now - float(window_sec), now, padding=0)

    def apply_theme(self) -> None:
        self.plot.setBackground(theme.SURFACE)
        self.plot.setLabel("left", "KB/s", color=theme.MUTED)
        for axis in (self.plot.getAxis("left"), self.plot.getAxis("bottom")):
            axis.setPen(pg.mkPen(theme.BORDER))
            axis.setTextPen(pg.mkPen(theme.MUTED))

        self.curve_down.setPen(pg.mkPen(theme.DOWN, width=2))
        self.curve_down.setSymbolBrush(pg.mkBrush(theme.DOWN))
        self.curve_down.setBrush(_brush(theme.DOWN, 38))
        self.curve_up.setPen(pg.mkPen(theme.UP, width=2))
        self.curve_up.setSymbolBrush(pg.mkBrush(theme.UP))
        self.curve_up.setBrush(_brush(theme.UP, 30))
        self.legend.setLabelTextColor(theme.TEXT)

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

    def retranslate(self) -> None:
        self.legend.clear()
        self.legend.addItem(self.curve_down, tr("chart.down"))
        self.legend.addItem(self.curve_up, tr("chart.up"))

    def clear(self) -> None:
        now = time.time()
        self.plot.setYRange(0, 5, padding=0)
        self.plot.setXRange(now - float(self.window_sec), now, padding=0)
        self.t.clear()
        self.down.clear()
        self.up.clear()
        self.curve_down.setData([], [])
        self.curve_up.setData([], [])
