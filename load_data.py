# ERS Strategy Simulator
# load_data.py | data loading and processing functions for ERS strategy simulator
# Author -  cuTie

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('cache')

# Example function to load telemetry data for the fastest lap of a given driver in a specified session
def load_fastest_lap_data(year=2021, gp='AbuDhabi', session_type='Q', driver='4'):
    session = fastf1.get_session(year, gp, session_type)
    session.load()
    lap = session.laps.pick_drivers(driver).pick_fastest()
    tel = lap.get_telemetry()

    # Adding extra to see if car is decelerating? for ERS deployment
    tel['dSpeed'] = tel['Speed'].diff() #speed change per sample
    print(f"Loaded data for fastest lap of driver {driver} in {gp} {session_type} {year}")
    # print(tel[['Speed','Distance','Brake','Throttle','DRS']].describe())#,'dSpeed']].head())
    return tel, lap

import numpy as np

"""
find all the braking and decelerating(lift and coast) zones in a lap. 
return a list of dicts with start and end info.
min_speed_drop: minimum speed drop to consider it a braking zone (in km/h)
min_zone_length: minimum number of samples to consider it a valid zone (to filter out noise)

math: 1000 samples in a second, so 10 samples = 0.01s, 50 samples = 0.05s, 100 samples = 0.1s, etc.
TODO: may need to optimize these parameters based on sample rate, track characteristics, etc. to capture meaningful zones without too much noise
"""
def find_braking_zones(tel, min_speed_drop = 30, min_zone_length = 10):
    zones = []
    in_zone = False
    start_idx = 0

    for i in range(1,len(tel)):
        decelerating = tel['dSpeed'].iloc[i] < 0 # negative speed change indicates deceleration
        braking = tel['Brake'].iloc[i] == True 

        if (decelerating or braking) and not in_zone:
            in_zone = True
            start_idx = i
        elif not decelerating and not braking and in_zone:
            in_zone = False
            end_idx = i # keeping only zones where speed drop is significant and zone is long enough
            #TODO: better use min_dist or min_duration instead of samples? as sample length may not be consistent
            v_start = tel['Speed'].iloc[start_idx]
            v_end = tel['Speed'].iloc[end_idx] 
            speed_drop = v_start - v_end
            zone_length = end_idx - start_idx

            if speed_drop >= min_speed_drop and zone_length >= min_zone_length:
                zones.append({'start_idx': start_idx, 'end_idx': end_idx,
                              'start_dist': tel['Distance'].iloc[start_idx],
                              'end_dist': tel['Distance'].iloc[end_idx], 
                              'start_spd_kmph': v_start, 'end_spd_kmph': v_end, 
                              'speed_drop_kmph': speed_drop, 'zone_length': zone_length})
    
    print(f"Identified {len(zones)} braking zones.")
    return zones

"""
find high-throttle acceleration zones for potential ERS deployment opportunities.
"""
def find_accel_zones(tel, throttle_threshold = 0.8, min_zone_length = 5): #TODO: optimal zone length may depend on sample rate, track, etc. need to experiment
    zones = []
    in_zone = False
    start_idx = 0
    for i in range(1,len(tel)):
        accelerating = tel['Throttle'].iloc[i] > throttle_threshold

        if accelerating and not in_zone:
            in_zone = True
            start_idx = i
        elif not accelerating and in_zone:
            in_zone = False
            end_idx = i 
            zone_length = end_idx - start_idx

            if zone_length >= min_zone_length:
                dist_covered = tel['Distance'].iloc[end_idx] - tel['Distance'].iloc[start_idx]
                zones.append({'start_idx': start_idx, 'end_idx': end_idx, 'start_dist': tel['Distance'].iloc[start_idx], 'end_dist': tel['Distance'].iloc[end_idx], 'dist_covered': dist_covered, 'avg_spd_kmph': tel['Speed'].iloc[start_idx:end_idx].mean(), 'zone_length': zone_length})
    
    print(f"Identified {len(zones)} acceleration zones.")
    return zones

import matplotlib.pyplot as plt

def plot_lap_zones(tel, braking_zones, accel_zones, title = "Lap Speed Profile"):
    fig, ax = plt.subplots(figsize=(14,5))
    fig.patch.set_facecolor('lightblue')
    ax.set_facecolor('lightgreen') #speedtrace
    ax.plot(tel['Distance'], tel['Speed'],color='blue', linewidth=1.2, label='Speed (km/h)') 
    # highlight braking zones: red = regen harvest #TODO: use different color for regen vs friction braking if possible
    for zone in braking_zones:
        ax.axvspan(zone['start_dist'], zone['end_dist'], color='red', alpha=0.3, 
                   label='Regen Zone') # if 'Regen Zone' not in ax.get_legend_handles_labels()[1] else "")
    #highlight accel zones: green = potential ERS deployment
    # TODO: use different color for high-throttle accel vs potential ERS deployment zones if possible
    for zone in accel_zones:
        ax.axvspan(zone['start_dist'], zone['end_dist'], 
                   color='green', alpha=0.3, label='Deployment Zone') #if 'Deployment Zone' not in ax.get_legend_handles_labels()[1] else "") 
    ax.legend(loc='upper right', facecolor='lightyellow')
    ax.set_xlabel('Distance (m)')
    ax.set_ylabel('Speed (km/h)')
    ax.set_title(title, fontsize=13)
    ax.tick_params(color='darkblue')
    for spine in ax.spines.values():
        spine.set_edgecolor('darkblue')
        plt.tight_layout()
        plt.savefig('lap_zones.png', dpi=300,bbox_inches='tight')
    plt.show()
    print("Lap zones plot saved as lap_zones.png")




# Example usage
# if __name__ == "__main__":
#     tel, lap = load_fastest_lap_data()
#     # print("\nFirst 5 rows of telemetry data:")
#     # print(tel.head())
#     zones = find_braking_zones(tel)
#     print("\nBraking zones identified:")
#     for i, zone in enumerate(zones):
#         print(f"Zone {i+1}: Start Dist {zone['start_dist']:.2f} m, End Dist {zone['end_dist']:.2f} m, Speed Drop {zone['speed_drop_kmph']:.2f} km/h, Zone Length {zone['zone_length']} samples")
#     accel_zones = find_accel_zones(tel)
#     print("\nAcceleration zones identified:")
#     for i, zone in enumerate(accel_zones):
#         print(f"Zone {i+1}: Start Dist {zone['start_dist']:.2f} m, End Dist {zone['end_dist']:.2f} m, Dist Covered {zone['dist_covered']:.2f} m, Avg Speed {zone['avg_spd_kmph']:.2f} km/h, Zone Length {zone['zone_length']} samples")
#     plot_lap_zones(tel, zones, accel_zones, title = f"Fastest Lap Braking and Accel Zones - Driver {lap['Driver']} - {lap['Team']} - {lap['LapTime']}")
