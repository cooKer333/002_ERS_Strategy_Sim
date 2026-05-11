# ERS Lap Energy Simuator
# main.py | entry point
# run this to execute full simulator
# Author -  cuTie 


print("ERS Simulator - starting ....")

import load_data as dat
import physics as phy
import ers_logic as ers
import visualise as vis

tel, lap = dat.load_fastest_lap_data() #TODO: add args for driver, session, etc.
braking_zones = dat.find_braking_zones(tel)
regen_results = phy.calc_regen_harvest(tel, braking_zones)
phy.print_regen_table(regen_results)
accel_zones = dat.find_accel_zones(tel)
deploy_results = phy.calc_deploy_potential(tel, accel_zones)
phy.print_deploy_table(deploy_results)
simulate_soc = phy.simulate_soc(regen_results, deploy_results)
mode_results = ers.run_all_modes(tel, regen_results, deploy_results)

# vis.plot_regen_bars(mode_results['OVERTAKE']['zone_deltas']) # example: plot zone deltas for the first mode (HARVEST)
# vis.plot_soc_trajectories(regen_results, deploy_results)
# vis.plot_lap_time_deltas(mode_results)
vis.plot_dashboard(tel, braking_zones, accel_zones, regen_results, deploy_results, mode_results)