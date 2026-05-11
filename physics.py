# ERS Strategy Simulator
# physics.py | core physics calculations for energy harvest and deployment
# Author -  cuTie


from asyncio import events


CAR_MASS_KG = 798  # kg, including driver
MGUK_MAX_POWER_KW = 120  # kW, max power of MGU-K
DEPLOY_LIMIT_MJ_PER_LAP = 2.0  # MJ, max energy deployment per lap
BATTERY_CAPACITY_MJ = 4.0  # MJ, total energy storage capacity of the battery
REGEN_EFFICIENCY = 0.85  # efficiency of energy regeneration (85% of kinetic energy can be converted to electrical energy) #TODO: change to variables
DEPLOY_EFFICIENCY = 0.92  # efficiency of energy deployment (92% of electrical energy can be converted to kinetic energy) #TODO: dynamic, efficiency map based on speed, power level, etc.
AIR_DENSITY_KG_M3 = 1.225  # kg/m^3, density of air at sea level
FRONTAL_AREA_M2 = 1.5  # m^2, estimated frontal area
DRAG_COEFFICIENT = 0.9  # estimated drag coefficient for an F1 car (varies with speed, aero setup, etc.)

#Conversion factors
def kmh_to_ms(kmh):
    return kmh / 3.6

# print(f"Physics constants loaded.")

"""
Calculatr harvestable energy in each of the braking zones.
Accounts for regen efficiency and 120kW power cap.
"""
def calc_regen_harvest(tel, braking_zones):
    results = []

    for i,zone in enumerate(braking_zones):
        v_start = kmh_to_ms(zone['start_spd_kmph'])
        v_end = kmh_to_ms(zone['end_spd_kmph'])
        delta_ke_MJ = 0.5 * CAR_MASS_KG * (v_start**2 - v_end**2) / 1e6 # theoretically max energy availablein MJ
        harvestable_MJ = delta_ke_MJ * REGEN_EFFICIENCY # accounting for regen efficiency

        t_start = tel['Time'].iloc[zone['start_idx']].total_seconds()
        # print(f"zone start time: {t_start:.2f} s, start speed: {zone['start_.spd_kmph']} km/h, end speed: {zone['end_spd_kmph']} km/h, ΔKE: {delta_ke_MJ:.4f} MJ, harvestable: {harvestable_MJ:.4f} MJ")
        t_end = tel['Time'].iloc[zone['end_idx']].total_seconds()
        zone_duration_s = t_end - t_start # duration of braking zone in seconds

        max_energy_MJ = (MGUK_MAX_POWER_KW * zone_duration_s) / 1e3 # max energy that can be harvested in this zone based on power cap and zone duration
        # print(f"max_energy_MJ: {max_energy_MJ:.4f} MJ, harvestable_MJ: {harvestable_MJ:.4f} MJ, zone_duration_s: {zone_duration_s:.2f} s")
        actual_harvest_MJ = min(harvestable_MJ, max_energy_MJ) # actual harvest is limited by both available energy and power cap
        results.append({'zone': i+1, 
                        'dist_start_m': zone['start_dist'],
                        'v_start_kmph': zone['start_spd_kmph'],
                        'v_end_kmph': zone['end_spd_kmph'],
                        'duration_s': round(zone_duration_s,2),
                        'delta_ke_mj': round(delta_ke_MJ,4),
                        'harvestable_mj': round(harvestable_MJ,4),
                        'actual_harvest_mj': round(actual_harvest_MJ,4),
                        'power_limited': harvestable_MJ > max_energy_MJ})# flag to indicate if harvest is limited by power cap #it is for the soft code
        
    # print(results[-1])
    return results

def print_regen_table(regen_results):
        print("\n***************************Regen Harvest per Braking Zone************************")
        print(f"{'Zone':>4}{'At(m)':>8} {'V_start(km/h)':>8} {'V_end(km/h)':>8} {'Duration(s)':>7} {'ΔKE(MJ)':>8} {'Harvestable(MJ)':>10} {'Cap?':>5}")
        print("*"*81)
        total = 0
        for res in regen_results:
            cap = "Yes" if res['power_limited'] else "No"
            print(f"{res['zone']:>4}{res['dist_start_m']:>8.0f}{res['v_start_kmph']:>12.0f}{res['v_end_kmph']:>12.0f}{res['duration_s']:>12.2f}{res['delta_ke_mj']:>10.4f}{res['harvestable_mj']:>15.4f}{cap:>7}")
            total += res['harvestable_mj']
        print(f"\nTotal Lap regen harvest: {total:.4f} MJ\n")            

"""
Calculate potential ERS deployment energy in each of the acceleration zones.
Accounts for deployment efficiency and 120kW power cap, and lap deployment limit.
"""
def calc_deploy_potential(tel, accel_zones):
    results = []
    for i,zone in enumerate(accel_zones):
        t_start = tel['Time'].iloc[zone['start_idx']].total_seconds()
        t_end = tel['Time'].iloc[zone['end_idx']].total_seconds()
        zone_duration_s = t_end - t_start

        max_deploy_MJ = (MGUK_MAX_POWER_KW * zone_duration_s) / 1e3 * DEPLOY_EFFICIENCY # max energy that can be deployed in this zone based on power cap, zone duration and deployment efficiency
        results.append({'zone': i+1, 
                        'dist_start_m': zone['start_dist'],
                        'dist_m': round(zone['dist_covered'],1),
                        'avg_v_kmph': zone['avg_spd_kmph'],
                        'duration_s': round(zone_duration_s,2),
                        'max_deploy_mj': round(max_deploy_MJ,4)})
        total = sum(r['max_deploy_mj'] for r in results)
    # for res in results:
    #     # res['total_deploy_mj'] = round(total,4)
    #     print(f"Total deployable energy in accel zones: {total:.4f} MJ | Lap cap: {DEPLOY_LIMIT_MJ_PER_LAP} MJ\n")
    return results

def print_deploy_table(deploy_results):
    print("\n********************Potential ERS Deployment per Accel Zone*********************")
    print(f"{'Zone':>4} {'At(m)':>8} {'Dist(m)':>8} {'AvgV(km/h)':>12} {'Duration(s)':>12} {'Max Deploy(MJ)':>15}")
    print("*"*80)
    total = 0
    for res in deploy_results:
        print(f"{res['zone']:>4}{res['dist_start_m']:>8.0f}{res['dist_m']:>10.1f}{res['avg_v_kmph']:>11.0f}{res['duration_s']:>14.2f}{res['max_deploy_mj']:>14.4f}")
        total += res['max_deploy_mj']
    print(f"\nTotal potential deployable energy in accel zones: {total:.4f} MJ | Lap cap: {DEPLOY_LIMIT_MJ_PER_LAP} MJ\n")
    
#TODO: variable deploy_fraction to simulate different ERS strategies (harvest vs attack mode, etc.)
def simulate_soc(regen_results, deploy_results, deploy_fraction = 1.0, initial_soc_mj = 0.50):
    soc = initial_soc_mj
    events = [(f"LAP START (SoC{initial_soc_mj:.2f} MJ)", 0, soc)]

    #sort all events by distanceso we step the order of occurrence in the lap
    all_events = []
    for res in regen_results:
        all_events.append(('regen', res['dist_start_m'], res['actual_harvest_mj'], res['zone'])) 
    for res in deploy_results:
        all_events.append(('deploy', res['dist_start_m'], res['max_deploy_mj'], res['zone']))
    all_events.sort(key=lambda x: x[1]) # sort by distance
    deployed_total_MJ = 0
    for typ, dist, energy_MJ, zone_num in all_events:
        if typ == 'regen':
            soc_add = energy_MJ/BATTERY_CAPACITY_MJ
            soc = min(soc + soc_add, 1.0) # cap at 100% SoC
            events.append((f"Regen Zone {zone_num} + {energy_MJ:.2f} MJ", dist, soc))
        elif typ == 'deploy':
            deploy_MJ = energy_MJ * deploy_fraction
            deploy_MJ = min(deploy_MJ, DEPLOY_LIMIT_MJ_PER_LAP - deployed_total_MJ) # cap deploy per lap
            deploy_MJ = min(deploy_MJ, soc * BATTERY_CAPACITY_MJ) # can't deploy more than current SoC
            soc -= deploy_MJ / BATTERY_CAPACITY_MJ
            deployed_total_MJ += deploy_MJ
            events.append((f"Deploy Zone {zone_num} - {deploy_MJ:.2f} MJ", dist, soc))
            events.append((f"Total Deployed: {deployed_total_MJ:.2f} MJ", dist, soc))
    return events, deployed_total_MJ

"""
very rough estimate of aerodynamic drag force based on speed
F_drag = 0.5 * rho * Cd * A * v^2, where rho is air density, Cd is drag coefficient, A is frontal area, v is speed in m/s
for simplicity, we will use a constant drag force at high speed, and ignore rolling resistance and other factors
#TODO: can be improved by using actual speed at each point and calculating variable drag force, and also accounting for rolling resistance, tire slip, etc. for more accuracy
"""
def calc_drag_force(speed_ms):
    return 0.5 * AIR_DENSITY_KG_M3 * DRAG_COEFFICIENT * FRONTAL_AREA_M2 * (speed_ms**2)

# sanity check
# import numpy as np
# v1 = kmh_to_ms(300)
# v2 = kmh_to_ms(80)
# delta_ke = 0.5 * CAR_MASS_KG * (v1**2 - v2**2) / 1e6 # in MJ
# harvestable = delta_ke * REGEN_EFFICIENCY
# print(f"Speed drop from 300 km/h to 80 km/h corresponds to {delta_ke:.2f} MJ of kinetic energy, of which {harvestable:.2f} MJ can be harvested with {REGEN_EFFICIENCY*100:.0f}% efficiency.")