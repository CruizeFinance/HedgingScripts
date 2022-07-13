import math
import time
import matplotlib.pyplot as plt
import numpy as np

from scripts import aave
from scripts import dydx
from scripts import intervals


class StgyApp(object):

    def __init__(self,
                 stk,
                 relevant_prices,
                 # P_floor,
                 # P_close_AAVE,
                 # P_add_coll_AAVE,
                 # P_remove_coll_DyDx,
                 # P_add_coll_DyDx,
                 # P_put_limit_order,
                 # P_floor_threshold,
                 # P_close_short,
                 aave_parameters,
                 dydx_parameters):
        p_floor, p_close_AAVE, p_add_coll_AAVE, p_remove_coll_DyDx, p_add_coll_DyDx, \
        p_put_limit_order, p_floor_threshold, p_close_short = relevant_prices
        self.stk = 1
        self.p_floor = 1140
        self.p_close_AAVE = 1250
        self.p_add_coll_AAVE = 1200
        self.p_remove_coll_DyDx = 1190
        self.p_add_coll_DyDx = 1180
        self.p_put_limit_order = 1170
        self.p_floor_threshold = 1160
        self.p_close_short = 1150
        self._aave = aave.Aave(aave_parameters)
        self._dydx = dydx.Dydx(aave_parameters)

        interval_infty = intervals.Interval(self.p_close_AAVE, math.inf, 'I_infty')
        interval_close_AAVE = intervals.Interval(self.p_add_coll_AAVE, self.p_close_AAVE, 'I_close_AAVE')
        interval_add_coll_AAVE = intervals.Interval(self.p_remove_coll_DyDx, self.p_add_coll_AAVE, 'I_add_coll_AAVE')
        interval_remove_coll_DyDx = intervals.Interval(sself.p_add_coll_DyDx, self.p_remove_coll_DyDx, 'I_remove_coll_DyDx')
        interval_add_coll_DyDx = intervals.Interval(sself.p_put_limit_order, self.p_add_coll_DyDx, 'I_add_coll_DyDx')
        interval_put_limit_order = intervals.Interval(self.p_close_short, self.p_put_limit_order, 'I_put_limit_order')
        interval_close_short = intervals.Interval(self.p_floor_threshold, self.p_close_short, 'I_close_short')
        interval_open_short = intervals.Interval(self.p_floor, self.p_floor_threshold, 'I_open_short')
        interval_minus_infty = intervals.Interval(-math.inf, self.p_floor, 'I_minus_infty')
        # interval_AAVE_LTV_limit = intervals.Interval(float('nan'),float('nan'),'I_'

    def launch(self):
        self._run_scenarios()

    def _run_scenarios(self):