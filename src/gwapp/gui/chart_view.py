from __future__ import annotations

from collections import deque
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg


class ChartView(QWidget):
    def __init__(self, maxpts=120):
        super().__init__()
        self.maxpts = maxpts
        self.x = deque(maxlen=maxpts)
        self.down = deque(maxlen=maxpts)
        self.up = deque(maxlen=maxpts)
        self.t = 0
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#1f1f24')
        self.plot.setLabel('bottom', 'الزمن', color='#e5e5e5')
        self.plot.setLabel('left', 'سرعة (KB/s)', color='#e5e5e5')
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.curve_down = self.plot.plot(self.x, self.down, pen=pg.mkPen('#4f9bff', width=2), name='تحميل')
        self.curve_up = self.plot.plot(self.x, self.up, pen=pg.mkPen('#3fb984', width=2), name='رفع')
        self.plot.addLegend()
        lay = QVBoxLayout(self)
        lay.addWidget(self.plot)
        lay.setContentsMargins(4, 4, 4, 4)

    def append(self, dt, down_kbps, up_kbps):
        self.t += 1
        self.x.append(self.t)
        self.down.append(down_kbps)
        self.up.append(up_kbps)
        self.curve_down.setData(self.x, self.down)
        self.curve_up.setData(self.x, self.up)
