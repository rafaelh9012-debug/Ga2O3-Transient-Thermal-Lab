"""Finite-volume transient thermal model for beta-Ga2O3 Schottky diodes.

Reuses the conductive operator, source geometry and boundary conditions of the
independent steady_reference.py model. The new mass term is rho * cp * V [J/K].
All internal temperatures are Kelvin, time is seconds and power density is W/cm^2.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Optional
import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve
from steady_reference import Parameters, mesh, geometry_arrays, assemble, conductivity_values, solve

MESHES = {
    "Fast": (24, 24, 6),
    "Balanced": (34, 34, 8),
    "Detailed": (48, 48, 10),
}


@dataclass(frozen=True)
class TransientSettings:
    power_w_cm2: float = 500.0
    substrate_a_um: float = 630.0
    substrate_b_um: float = 50.0
    drift_um: float = 10.0
    contact_radius_um: float = 500.0
    domain_radius_um: float = 1000.0
    sink_k: float = 300.0
    ambient_k: float = 300.0
    h_w_m2k: float = 10.0
    conductivity: str = "frozen"  # frozen, temperature, constant
    constant_k: float = 14.0
    density_kg_m3: float = 5950.0
    cp_j_kgk: float = 490.0
    heating_s: float = 0.3
    cooling_s: float = 0.3
    points_per_phase: int = 55
    mesh_name: str = "Fast"
    surface_readout: str = "Center"  # Center or Contact average

    def validate(self):
        if self.mesh_name not in MESHES:
            raise ValueError("Unknown mesh resolution")
        if self.conductivity not in ("frozen", "temperature", "constant"):
            raise ValueError("Unknown conductivity model")
        if self.surface_readout not in ("Center", "Contact average"):
            raise ValueError("Unknown surface reading")
        values = [self.density_kg_m3, self.cp_j_kgk, self.heating_s, self.cooling_s]
        if not all(np.isfinite(v) and v > 0 for v in values):
            raise ValueError("Density, heat capacity, and durations must be positive and finite")
        if not 15 <= self.points_per_phase <= 160:
            raise ValueError("Time samples must be between 15 and 160")
        if self.heating_s > 100 or self.cooling_s > 100:
            raise ValueError("Heating and cooling intervals must each be <= 100 seconds")
        if not np.isfinite(self.power_w_cm2) or self.power_w_cm2 < 0:
            raise ValueError("Power must be nonnegative")
        if self.contact_radius_um > self.domain_radius_um:
            raise ValueError("Contact must be inside the domain")


@dataclass
class Curve:
    thickness_um: float
    on_s: np.ndarray
    on_c: np.ndarray
    off_s: np.ndarray
    off_c: np.ndarray
    baseline_c: float
    end_on_c: float
    end_off_c: float
    steady_on_c: float
    source_power_w: float
    final_on_field_c: np.ndarray
    final_off_field_c: np.ndarray
    x_um: np.ndarray
    z_um: np.ndarray
    max_step_residual: float
    heat_balance_error: float

    def summary(self):
        start, end, target = self.baseline_c, self.end_on_c, self.steady_on_c
        heat_delta = target - start
        rise90 = crossing_time(self.on_s, self.on_c, start + 0.9 * heat_delta, ascending=True) if heat_delta > 1e-8 else None
        off_delta = end - self.baseline_c
        cooldown90 = crossing_time(self.off_s, self.off_c, self.baseline_c + 0.1 * off_delta, ascending=False) if off_delta > 1e-8 else None
        return {"substrate_um": self.thickness_um, "baseline_C": start,
                "on_end_C": end, "off_end_C": self.end_off_c,
                "steady_on_C": target, "source_power_W": self.source_power_w,
                "rise_time_to_90pct_steady_s": rise90,
                "cooling_time_to_10pct_switch_off_excess_s": cooldown90,
                "max_linear_residual_relative": self.max_step_residual,
                "max_step_energy_balance_relative": self.heat_balance_error}


def crossing_time(times, values, target, ascending=True) -> Optional[float]:
    values = np.asarray(values, dtype=float)
    times = np.asarray(times, dtype=float)
    if ascending:
        hit = np.flatnonzero(values >= target)
    else:
        hit = np.flatnonzero(values <= target)
    if len(hit) == 0:
        return None
    j = int(hit[0])
    if j == 0:
        return float(times[0])
    a, b = values[j-1], values[j]
    if abs(b-a) < 1e-14:
        return float(times[j])
    frac = np.clip((target-a)/(b-a), 0, 1)
    return float(times[j-1] + frac * (times[j]-times[j-1]))


def phase_times(duration_s: float, count: int) -> np.ndarray:
    # A geometric schedule resolves the first microseconds AND late equilibration.
    first = max(1.e-10, duration_s * 1.e-6)
    return np.r_[0.0, np.geomspace(first, duration_s, count)]


def make_parameters(settings: TransientSettings, thickness_um: float) -> Parameters:
    nx, nz, nd = MESHES[settings.mesh_name]
    return Parameters(substrate_um=thickness_um, drift_um=settings.drift_um,
                      contact_radius_um=settings.contact_radius_um,
                      domain_radius_um=settings.domain_radius_um,
                      power_w_cm2=settings.power_w_cm2,
                      sink_k=settings.sink_k, ambient_k=settings.ambient_k,
                      h_w_m2k=settings.h_w_m2k,
                      geometry="axisymmetric", lateral_axis="effective",
                      conductivity=settings.conductivity,
                      constant_k=settings.constant_k,
                      nx=nx, nz_substrate=nz, nz_drift=nd)


def surface_temperature_c(t_k: np.ndarray, p: Parameters, ze: np.ndarray,
                          xe: np.ndarray, mode: str) -> float:
    # Report the actual Robin boundary surface temperature, not a cell-centre proxy.
    _, kz = conductivity_values(t_k[0, :], p)
    conductance_per_area = 2.0 * kz / (ze[1] - ze[0])
    surface = (conductance_per_area * t_k[0] + p.h_w_m2k * p.ambient_k) / (conductance_per_area + p.h_w_m2k)
    if mode == "Center":
        return float(surface[0] - 273.15)
    face_areas = np.pi * (xe[1:]**2 - xe[:-1]**2)
    contact_mask = (0.5*(xe[:-1]+xe[1:])) < p.contact_radius_um*1.e-6
    return float(np.average(surface[contact_mask], weights=face_areas[contact_mask]) - 273.15)


def simulate_case(settings: TransientSettings, thickness_um: float) -> Curve:
    settings.validate()
    p = make_parameters(settings, thickness_um)
    p.validate()
    xe, ze = mesh(p)
    _, _, area, _, volumes = geometry_arrays(p, xe, ze)
    xc = 0.5 * (xe[:-1] + xe[1:])
    zc = 0.5 * (ze[:-1] + ze[1:])
    active = (zc[:, None] < p.drift_um * 1.e-6) & (xc[None, :] < p.contact_radius_um * 1.e-6)
    source = np.where(active, p.power_w_cm2 * 1.e4/(p.drift_um*1.e-6)*volumes, 0.0)
    mass = (settings.density_kg_m3 * settings.cp_j_kgk * volumes).ravel()
    zero_source = np.zeros_like(source)

    # True zero-power thermal equilibrium accommodates ambient != sink.
    equilibrium = solve(replace(p, power_w_cm2=0.0))
    t0 = equilibrium.temperature_k.copy()
    steady_on = solve(p).temperature_k if p.power_w_cm2 else t0.copy()

    on_times = phase_times(settings.heating_s, settings.points_per_phase)
    off_times = phase_times(settings.cooling_s, settings.points_per_phase)
    on_values = [surface_temperature_c(t0, p, ze, xe, settings.surface_readout)]
    off_values = []
    temp = t0.copy()
    max_resid, max_balance = 0., 0.

    def advance(previous: np.ndarray, delta_s: float, power: np.ndarray):
        nonlocal max_resid, max_balance
        old = previous.ravel()-p.sink_k
        capacity_over_dt = mass / delta_s
        guess = previous.copy()
        is_nonlinear = p.conductivity == "temperature"
        for _ in range(24 if is_nonlinear else 1):
            A, rhs, bottom, top = assemble(guess, p, xe, ze, power)
            system = A + diags(capacity_over_dt, 0, format="csr")
            # Solve directly for the increment: avoids catastrophic cancellation
            # when dt is tiny and the old field is already near equilibrium.
            solve_rhs = rhs - A @ old
            increment = spsolve(system, solve_rhs)
            new_u = old + increment
            candidate = new_u.reshape(previous.shape) + p.sink_k
            if not np.all(np.isfinite(candidate)) or np.min(candidate) <= 0 or np.max(candidate) >= 10000:
                raise RuntimeError("Numerical temperature guard exceeded. Lower power or switch to frozen conductivity.")
            change = float(np.max(np.abs(candidate-guess)))
            # Picard damping; required only for nonlinear conductivity.
            guess = (0.7*candidate + 0.3*guess) if is_nonlinear else candidate
            if not is_nonlinear or change < 1.e-5:
                guess = candidate
                break
        else:
            raise RuntimeError("Nonlinear time step did not converge. Try lower power or frozen conductivity.")
        # Reassemble at converged new temperatures; quantify discrete energy balance.
        A, rhs, bottom, top = assemble(guess, p, xe, ze, power)
        u = guess.ravel()-p.sink_k
        # Recover a stable increment from the final frozen-conductivity operator.
        delta_final = spsolve(A + diags(capacity_over_dt, 0, format="csr"), rhs - A @ old)
        mass_change = float(np.dot(mass, delta_final))
        boundary_flux = (float(np.dot(bottom, guess[-1]-p.sink_k))
                         + float(np.dot(top, guess[0]-p.ambient_k)))
        source_energy = float(power.sum()*delta_s)
        imbalance = abs(mass_change + boundary_flux*delta_s - source_energy)
        denom = max(abs(mass_change), abs(boundary_flux*delta_s), abs(source_energy), 1.e-14)
        if denom > 1.e-9:
            max_balance = max(max_balance, imbalance/denom)
        residual = A @ (old + delta_final) + capacity_over_dt * delta_final - rhs
        denom_res = max(np.linalg.norm(rhs, 1), np.linalg.norm(A @ old, 1), 1.e-10)
        if denom_res > 1.e-8:
            max_resid = max(max_resid, float(np.linalg.norm(residual, 1)/denom_res))
        return guess

    for prev_time, next_time in zip(on_times[:-1], on_times[1:]):
        temp = advance(temp, float(next_time-prev_time), source)
        on_values.append(surface_temperature_c(temp, p, ze, xe, settings.surface_readout))
    end_on_field = temp.copy()
    off_values.append(on_values[-1])  # continuous at switch-off (t=0)
    for prev_time, next_time in zip(off_times[:-1], off_times[1:]):
        temp = advance(temp, float(next_time-prev_time), zero_source)
        off_values.append(surface_temperature_c(temp, p, ze, xe, settings.surface_readout))

    return Curve(float(thickness_um), on_times, np.array(on_values),
                 off_times, np.array(off_values), on_values[0], on_values[-1],
                 off_values[-1], surface_temperature_c(steady_on, p, ze, xe, settings.surface_readout),
                 float(source.sum()), end_on_field-273.15, temp-273.15,
                 xc*1e6, zc*1e6, max_resid, max_balance)


def simulate_comparison(settings: TransientSettings) -> tuple[Curve, Curve]:
    return (simulate_case(settings, settings.substrate_a_um),
            simulate_case(settings, settings.substrate_b_um))


def as_records(curves: tuple[Curve, Curve], settings: TransientSettings):
    return {"model": "2D axisymmetric transient conduction; backward Euler + Picard for k(T)",
            "settings": asdict(settings),
            "cases": [c.summary() for c in curves]}
