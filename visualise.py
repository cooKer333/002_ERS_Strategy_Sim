import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

plt.rcParams.update({'font.size': 12, 'figure.facecolor': 'white', 
                     'axes.facecolor': 'white', 'axes.edgecolor': 'black', 
                     'axes.grid': True, 'grid.color': 'lightgray', 
                     'text.color': 'black', 'xtick.color': 'black', 
                     'ytick.color': 'black', 'font.family': 'monospace'})

def plot_regen_bars(zone_data_list):
    """
    Plots energy harvest for a list of zones.
    Expects zone_data_list to be mode_results['MODE']['zone_deltas']
    """
    if not zone_data_list:
        print("No zone data available to plot.")
        return

    # 1. Extract values using the keys from your simulation loop
    # We use .get() as a safety net in case a key is missing
    zones = [f"Z{r.get('zone_idx', '??')}" for r in zone_data_list]
    energy = [r.get('actual_regen_mj', 0) for r in zone_data_list]
    
    # Identify if a zone hit the MGU-K power limit (usually 120kW)
    colors = ['#e8003d' if r.get('power_limited', False) else '#00d4ff' for r in zone_data_list]

    # 2. Create the plot
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(zones, energy, color=colors, width=0.6, zorder=3)

    # 3. Add text labels on top of bars
    for bar, val in zip(bars, energy):
        ax.text(bar.get_x() + bar.get_width()/2, 
                bar.get_height() + 0.01, 
                f"{val:.3f} MJ", ha='center', va='bottom', 
                fontsize=10, color='#c8d4e8', zorder=4)

    # 4. Styling (Matching the Project Guide aesthetic)
    ax.axhline(y=2.0, color='#ffd700', linestyle='--', lw=1, 
               label='FIA 2MJ Deployment Limit', zorder=2)
    
    ax.set_xlabel('Braking Zones')
    ax.set_ylabel('Energy Harvested (MJ)')
    ax.set_title('Regen Harvest per Braking Zone', fontsize=14, color='#eaf0ff')
    ax.grid(axis='y', alpha=0.2, zorder=0)
    ax.legend(loc='upper right', facecolor='#0a0c10')
    
    plt.tight_layout()
    plt.savefig('regen_harvest_bars.png', dpi=300)
    plt.show()

from physics import simulate_soc
from ers_logic import ERS_MODES

"""
SoC Trajectory Plotting Function
Simulates SoC changes over the lap for different ERS strategy modes and plots the trajectories.
"""
def plot_soc_trajectories(regen_results, deploy_results):
    fig, ax = plt.subplots(figsize=(12, 6))
    for mode_name, cfg in ERS_MODES.items():
        events, _ = simulate_soc(regen_results, deploy_results, 
                                 deploy_fraction=cfg['deploy_fraction'], initial_soc_mj=0.50)
    labels = [e[0] for e in events]
    soc_values = [e[1] for e in events]
    ax.step(range(len(soc_values)), soc_values, where='post', 
            label=mode_name, color=cfg['color'], lw=2)
    ax.axhline(100, color="#415a9a", lw=1,ls ='--')
    ax.fill_between(range(60),0,10,alpha=0.1,color='#e8003d', label='Danger Zone (0-10% SoC)')
    ax.set_ylim(-5, 110)
    ax.set_ylabel('SoC (%)')
    ax.set_xlabel('Events(regen/deploy), in lap order')
    ax.set_title('SoC Trajectories for Different ERS Modes', fontsize=14, color='#eaf0ff')
    ax.legend(loc='upper right', facecolor='#0a0c10', edgecolor='#2a3550')
    plt.savefig('soc_trajectories.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_lap_time_deltas(mode_results):
    modes = list(mode_results.keys())
    deltas = [mode_results[m]['lap_time_delta_ms'] for m in modes]
    colors = [ERS_MODES[m]['color'] for m in modes]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(modes, deltas, color=colors, height=0.5, zorder=3)
    ax.axvline(0, color='#415a9a', lw=1)
    for bar, delta in zip(bars, deltas):
        xpos = bar.get_x() + bar.get_width() + (10 if delta >= 0 else -10)
        ax.text(xpos, bar.get_y() + bar.get_height()/2,
                f"{delta:.2f} ms", ha='left' if delta>= 0 else 'right', va='center', 
                fontsize=11, color='#eaf0ff', fontweight='bold', zorder=4)
    ax.set_xlabel('Lap Time Delta (ms) vs No ERS baseline (ms) | Negative = Faster Lap, Positive = Slower Lap') 
    ax.set_title('Lap Time Delta Compared to No Deployment', fontsize=14, color='#eaf0ff')
    ax.grid(axis='x', alpha=0.2, zorder=0)
    plt.savefig('lap_time_deltas.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_dashboard(tel, braking_zones, accel_zones, regen_results, deploy_results, mode_results):
    fig = plt.figure(figsize=(18, 12))
    gs = gridspec.GridSpec(2, 2, hspace = 0.40, wspace=0.28, figure=fig)
    ax1 = fig.add_subplot(gs[0, :])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[1, 1])
    ax1.plot(tel['Distance'], tel['Speed'], color="#032458", linewidth=1.2, label='Speed (km/h)')
    for zone in braking_zones:
        ax1.axvspan(zone['start_dist'], zone['end_dist'], color='#e8003d', alpha=0.2, 
                    label='Regen Zone' if 'Regen Zone' not in ax1.get_legend_handles_labels()[1] else "")
    for zone in accel_zones:
        ax1.axvspan(zone['start_dist'], zone['end_dist'], color="#055e10", alpha=0.2, 
                    label='Deployment Zone'  if 'Deployment Zone' not in ax1.get_legend_handles_labels()[1] else "")
    ax1.set_title('Speed Trace |Regen Zones(Red) Deploy Zones(Green)', color="#0b4cf2")
    ax1.set_xlabel('Distance (m)')
    ax1.set_ylabel('Speed (km/h)')
    ax1.grid(alpha=0.15)

    zones = [f"Z{i+1}" for i in range(len(regen_results))]
    energy = [r.get('actual_harvest_mj', 0) for r in regen_results]
    colors = ['#e8003d' if r.get('power_limited', False) else '#00d4ff' for r in regen_results]

    bars = ax2.bar(zones, energy, color=colors, width=0.6, zorder=3)
    ax2.axhline(y=2.0, color='#ffd700', linestyle='--', lw=1, label='FIA 2MJ Cap', zorder=2) #FIA deployment limit reference line
    from matplotlib.patches import Patch # Legend (Manual handles for the colors)
    legend_elements = [
        Patch(facecolor='#e8003d', label='Power Limited'),
        Patch(facecolor='#00d4ff', label='Full Recovery'),
        plt.Line2D([0], [0], color='#ffd700', linestyle='--', label='FIA 2MJ Cap')
    ]
    ax2.set_title('Regen Harvest per Braking Zone', color="#020714")
    ax2.set_ylabel('Energy Harvested (MJ)')
    ax2.grid(axis='y', alpha=0.2, zorder=0)
    ax2.legend(handles=legend_elements, loc='upper right')

    if not mode_results:
        print("Warning: mode_results is empty!") #TODO: rename
    modes = list(mode_results.keys())
    deltas = [mode_results[m]['lap_time_delta_ms'] for m in modes]
    m_colors = [ERS_MODES[m]['color'] for m in modes]
    ax3.barh(modes, deltas, color=m_colors, height=0.5, zorder=3)
    ax3.axvline(0, color='#415a9a', lw=1)
    ax3.set_title('Lap Time Delta Compared vs No ERS', color='#eaf0ff')
    ax3.set_xlabel('Lap Time Delta (ms) | Negative = Faster Lap')
    ax3.grid(axis='x', alpha=0.2, zorder=0)
    
    fig.suptitle('ERS Simulator Dashboard', fontsize=16, color="#111111")
    plt.savefig('ers_simulator_dashboard.png', dpi=300, bbox_inches='tight')
    print("Dashboard plot saved as ers_simulator_dashboard.png")
    plt.show()


    