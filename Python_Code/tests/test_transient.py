"""Run: python -m unittest discover -s tests -v"""
import unittest
from dataclasses import replace
import numpy as np
from transient_model import TransientSettings, simulate_case, phase_times, crossing_time

class TransientSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = TransientSettings(power_w_cm2=300,heating_s=.2,cooling_s=.2,points_per_phase=27)
        cls.a = simulate_case(cls.cfg,630.)
        cls.b = simulate_case(cls.cfg,50.)

    def test_time_grids_strictly_increasing_and_bounded(self):
        t = phase_times(.3,25)
        self.assertEqual(t[0],0)
        self.assertAlmostEqual(t[-1],.3)
        self.assertTrue(np.all(np.diff(t)>0))

    def test_on_off_switch_is_exactly_continuous(self):
        for c in (self.a,self.b):
            self.assertEqual(c.off_s[0],0)
            self.assertAlmostEqual(c.off_c[0],c.on_c[-1],places=10)

    def test_heating_then_cooling_monotonic(self):
        for c in (self.a,self.b):
            self.assertGreater(c.on_c[-1],c.on_c[0])
            self.assertLess(c.off_c[-1],c.off_c[0])
            self.assertGreaterEqual(np.min(np.diff(c.on_c)),-1.e-8)
            self.assertLessEqual(np.max(np.diff(c.off_c)),1.e-8)

    def test_zero_power_no_transient(self):
        c=simulate_case(replace(self.cfg,power_w_cm2=0,heating_s=.005,cooling_s=.005,points_per_phase=20),50.)
        self.assertLess(np.ptp(c.on_c),1e-8)
        self.assertLess(np.ptp(c.off_c),1e-8)
        self.assertEqual(c.source_power_w,0)

    def test_numerical_energy_conservation(self):
        for c in (self.a,self.b):
            self.assertLess(c.max_step_residual,1.e-6)
            self.assertLess(c.heat_balance_error,2.e-5)

    def test_different_thickness_thermal_response(self):
        self.assertLess(self.b.end_on_c,self.a.end_on_c)
        self.assertLess(self.b.summary()['rise_time_to_90pct_steady_s'],
                        self.a.summary()['rise_time_to_90pct_steady_s'])

    def test_heat_capacity_changes_transient_not_steady_state(self):
        p=replace(self.cfg,heating_s=.004,cooling_s=.004,points_per_phase=24)
        lo=simulate_case(replace(p,cp_j_kgk=300),630.)
        hi=simulate_case(replace(p,cp_j_kgk=800),630.)
        self.assertGreater(lo.end_on_c,hi.end_on_c)
        self.assertAlmostEqual(lo.steady_on_c,hi.steady_on_c,places=6)

    def test_temperature_dependent_is_distinct(self):
        p=replace(self.cfg,conductivity='temperature',heating_s=.15,cooling_s=.15,points_per_phase=24)
        hot=simulate_case(p,630.)
        self.assertGreater(hot.steady_on_c,self.a.steady_on_c)
        self.assertLess(hot.max_step_residual,1.e-6)

    def test_boundary_initial_ambient_difference(self):
        p=replace(self.cfg,power_w_cm2=0,ambient_k=330.,h_w_m2k=1000.,heating_s=.01,cooling_s=.01,points_per_phase=20)
        c=simulate_case(p,50.)
        self.assertGreater(c.baseline_c,p.sink_k-273.15)
        self.assertLess(np.ptp(c.on_c),1.e-7)

    def test_crossing_time_does_not_extrapolate(self):
        self.assertIsNone(crossing_time([0,1],[0,5],10,True))
        self.assertAlmostEqual(crossing_time([0,1],[0,10],5,True),.5)

if __name__ == '__main__':
    unittest.main()
