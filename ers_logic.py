# ERS Strategy Simulator
# ers_logic.py | core ERS energy calculations and strategy logic
# Author -  cuTie

# ERS Energy Modes - constant that multiplies deployable energy per zone 
ERS_MODES = {
    'HARVEST': {'deploy_fraction': 0.35, 'description': 'Build battery. Low deploy. Used when defending or conserving for a planned attack lap.', 'color': 'red'},
    'BALANCED': {'deploy_fraction': 0.7, 'description': 'Default race pace. Sustainable over a full stint without SoC depletion.', 'color': 'orange'},
    'ATTACK': {'deploy_fraction': 0.9, 'description': 'Used during undercut/overcut windows and when chasing rivals.', 'color': 'green'},
    'OVERTAKE': {'deploy_fraction': 1.0, 'description': 'Full deployment for 3–8 seconds in one target zone only. Triggered by driver or engineer radio.', 'color': 'blue'},
}

print(f"ERS modes defined")

for name, cfg in ERS_MODES.items():
    print(f"{name:<10}: Deploy {cfg['deploy_fraction']*100:.0f}% of harvested energy.") #{cfg['description']}")

import physics as phy 

DRAG_FORCE_ESTIMATE_N = 1800 # Newtons, very rough estimate of aerodynamic drags + rolling resistance force at high speed (#TODO: depends on car, speed, etc.)

#TODO: time step simulation of lap with variable deploy fractions in different zones, and calculate resulting lap time delta compared to baseline without ERS deployment, to estimate optimal strategy for different scenarios (defending, attacking, etc.) and track characteristics (high speed vs low speed tracks, etc.)
def calc_lap_time_delta(deploy_results, deploy_fraction, tel):
    total_delta_t_s = 0
    deployed_energy_mj = 0
    zone_deltas = []
    for deploy in deploy_results:
        if deployed_energy_mj >= phy.DEPLOY_LIMIT_MJ_PER_LAP:
            break
        energy_MJ = deploy['max_deploy_mj'] * deploy_fraction
        energy_MJ = min(energy_MJ, phy.DEPLOY_LIMIT_MJ_PER_LAP - deployed_energy_mj) # ensure we don't exceed lap deploy limit
        energy_J = energy_MJ * 1e6
        # convert energy to time gain using power = energy / time, where power is roughly estimated based on drag force and speed
        v_avg_ms = phy.kmh_to_ms(deploy['avg_v_kmph'])
        distance_m = deploy['dist_m'] # distance covered in the deployment zone
        t_baseline_s = distance_m / v_avg_ms # baseline time to cover the deployment zone at average speed
        t_zone_s = deploy['duration_s'] # duration of the deployment zone
        P_ers = (energy_J * phy.DEPLOY_EFFICIENCY) / t_zone_s # effective power from ERS deployment
        F_ers = P_ers / v_avg_ms # equivalent force from ERS deployment at wheel
        total_F = phy.calc_drag_force(v_avg_ms) + F_ers # total effective force propelling the car forward
        t_ers_s = distance_m / (v_avg_ms * (total_F / phy.calc_drag_force(v_avg_ms))) # new time to cover the deployment zone with ERS assist   
        delta_t_s = t_ers_s - t_baseline_s # time gained (negative) or lost (positive) from ERS deployment in this zone
        total_delta_t_s += delta_t_s
        deployed_energy_mj += energy_MJ # track deployed energy to ensure we don't exceed lap limit
        zone_deltas.append({'zone': deploy['zone'], 'energy_deployed_mj': energy_MJ, 'time_delta_ms': delta_t_s*1000})

    return total_delta_t_s, deployed_energy_mj, zone_deltas

"""
Run all ERS strategy modes and compare results.
"""
def run_all_modes(tel, regen_results, deploy_results):
    mode_results = {}
    print("\n************************ERS Strategy Mode Comparison*************************")
    print(f"{'Mode':<10} {'Deploy%':>8} {'Energy Deployed (MJ)':>20} {'Lap Time Delta (ms)':>20} {'SoC End':>15}")
    print("*"*77)

    for mode_name, cfg in ERS_MODES.items():
        deploy_fraction = cfg['deploy_fraction']
        delta_t_s, energy_deployed_mj, zone_deltas = calc_lap_time_delta(deploy_results, deploy_fraction, tel)
        soc_events, total_deployed_mj = phy.simulate_soc(regen_results, deploy_results, deploy_fraction)
        soc_end = soc_events[-1][1] * 100 # final SoC after lap simulation
        mode_results[mode_name] = {'zone': zone_deltas[0]['zone'], 
                                   'deploy_fraction': deploy_fraction, 'energy_deployed_mj': energy_deployed_mj, 
                                   'lap_time_delta_ms': delta_t_s*1000, 'soc_end_percent': soc_end, 'zone_deltas': zone_deltas}
        print(f"{mode_name:<10} {deploy_fraction*100:>8.0f} {energy_deployed_mj:>20.2f} {delta_t_s*1000:>20.2f} {soc_end:>15.2f}")
    
    return mode_results

