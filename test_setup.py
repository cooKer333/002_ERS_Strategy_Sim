import fastf1

# fastf1 will store downloaded data in cache
fastf1.Cache.enable_cache('cache')

# load Italian GP 2023 Qualifying session
# Monza is a high speed track, with long straights = lots of ERS action
session = fastf1.get_session(2023, 'Italy', 'Q')
# session = fastf1.get_session(2023, 'Monza', 'Q')
session.load()

# get Leclerc's fastest Lap
lec_fastest = session.laps.pick_drivers('16').pick_fastest()
tel = lec_fastest.get_telemetry()

#printing stats
print(f"Lap time: {lec_fastest['LapTime']}")
print(f"Top speed: {tel['Speed']} km/h")
# print(f"ERS deployment: {tel['ERSDeploy']}%")       
# print(f"ERS energy used: {tel['ERSEnergy']} MJ")
# print(f"ERS deployment time: {tel['ERSDeployTime']} seconds")
# print(f"ERS deployment power: {tel['ERSDeployPower']} kW")
print(f"Data points: {len(tel)} samples")
print(f"Columns: {list(tel.columns)}")
