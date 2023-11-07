import os
import discord
from discord.ext import commands
import fastf1 as ff1
from fastf1 import plotting
from fastf1.api import track_status_data
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.collections import LineCollection
from keep_alive import keep_alive
import requests
import seaborn as sns
prefix = "#fuan "
client = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())
#ff1.Cache.enable_cache('cache')
ff1.plotting.setup_mpl()

def ergast_retrieve(api_endpoint: str):
    url = f'https://ergast.com/api/f1/{api_endpoint}.json'
    response = requests.get(url).json()
    
    return response['MRData']


@client.event
async def on_ready():
  print(f"I am ready to go - {client.user.name}")
  await client.change_presence(activity=discord.Activity(
    type=discord.ActivityType.watching, name=f"Drive to Survive"))


@client.event
async def on_command_error(ctx, error):
  await ctx.send(f"An error occured: {str(error)}")


@client.command(name="ping")
async def _ping(ctx):
  await ctx.send(f"Ping: {client.latency}")


@client.command(name="telemetry")
async def _command(ctx, arg1, arg2, arg3, arg4, arg5):
  year = arg1
  track = arg2
  session_time = arg3
  driver_1 = arg4
  driver_2 = arg5
  await ctx.send("{},{},{},{},{}".format(year, track, session_time, driver_1,
                                         driver_2))
  progress_bar = await ctx.send('=>...............')
  session = ff1.get_session(int(arg1), str(arg2), str(arg3))
  await progress_bar.edit(content = '===>.............')
  session.load()
  await progress_bar.edit(content = '======>..........')
  laps_driver_1 = session.laps.pick_driver(str(arg4))
  laps_driver_2 = session.laps.pick_driver(str(arg5))
  await progress_bar.edit(content = '=========>.......')
  fastest_driver_1 = laps_driver_1.pick_fastest()
  fastest_driver_2 = laps_driver_2.pick_fastest()
  await progress_bar.edit(content = '============>...')
  telemetry_driver_1 = fastest_driver_1.get_telemetry()
  telemetry_driver_2 = fastest_driver_2.get_telemetry()
  await progress_bar.edit(content = '=============>..')
  delta_time, ref_tel, compare_tel = ff1.utils.delta_time(
    fastest_driver_1, fastest_driver_2)
  team_driver_1 = laps_driver_1['Team'].iloc[0]
  team_driver_2 = laps_driver_2['Team'].iloc[0]
  color_1 = ff1.plotting.team_color(team_driver_1)
  color_2 = ff1.plotting.team_color(team_driver_2)
  if color_1 == color_2:
    color_2='#ffffff'
  await progress_bar.edit(content = '================> Done!')  
  await ctx.send (str(driver_1)+':'+str(fastest_driver_1['LapTime'])[11:19])
  await ctx.send (str(driver_2)+':'+str(fastest_driver_2['LapTime'])[11:19])
  
  # Set the size of the plot
  plt.rcParams['figure.figsize'] = [20, 15]

  # Our plot will consist of 7 "subplots":
  #     - Delta
  #     - Speed
  #     - Throttle
  #     - Braking
  #     - Gear
  #     - RPM
  #     - DRS
  fig, ax = plt.subplots(7,
                         gridspec_kw={'height_ratios': [1, 3, 2, 1, 1, 2, 1]})

  # Set the title of the plot
  ax[0].title.set_text(f"Telemetry comparison {driver_1} vs. {driver_2}")

  # Subplot 1: The delta
  ax[0].plot(ref_tel['Distance'], delta_time, color=color_1)
  ax[0].axhline(0)
  ax[0].set(ylabel=f"Gap to {driver_2} (s)")

  # Subplot 2: Distance
  ax[1].plot(telemetry_driver_1['Distance'],
             telemetry_driver_1['Speed'],
             label=driver_1,
             color=color_1)
  ax[1].plot(telemetry_driver_2['Distance'],
             telemetry_driver_2['Speed'],
             label=driver_2,
             color=color_2)
  ax[1].set(ylabel='Speed')
  ax[1].legend(loc="lower right")

  # Subplot 3: Throttle
  ax[2].plot(telemetry_driver_1['Distance'],
             telemetry_driver_1['Throttle'],
             label=driver_1,
             color=color_1)
  ax[2].plot(telemetry_driver_2['Distance'],
             telemetry_driver_2['Throttle'],
             label=driver_2,
             color=color_2)
  ax[2].set(ylabel='Throttle')

  # Subplot 4: Brake
  ax[3].plot(telemetry_driver_1['Distance'],
             telemetry_driver_1['Brake'],
             label=driver_1,
             color=color_1)
  ax[3].plot(telemetry_driver_2['Distance'],
             telemetry_driver_2['Brake'],
             label=driver_2,
             color=color_2)
  ax[3].set(ylabel='Brake')

  # Subplot 5: Gear
  ax[4].plot(telemetry_driver_1['Distance'],
             telemetry_driver_1['nGear'],
             label=driver_1,
             color=color_1)
  ax[4].plot(telemetry_driver_2['Distance'],
             telemetry_driver_2['nGear'],
             label=driver_2,
             color=color_2)
  ax[4].set(ylabel='Gear')

  # Subplot 6: RPM
  ax[5].plot(telemetry_driver_1['Distance'],
             telemetry_driver_1['RPM'],
             label=driver_1,
             color=color_1)
  ax[5].plot(telemetry_driver_2['Distance'],
             telemetry_driver_2['RPM'],
             label=driver_2,
             color=color_2)
  ax[5].set(ylabel='RPM')

  # Subplot 7: DRS
  ax[6].plot(telemetry_driver_1['Distance'],
             telemetry_driver_1['DRS'],
             label=driver_1,
             color=color_1)
  ax[6].plot(telemetry_driver_2['Distance'],
             telemetry_driver_2['DRS'],
             label=driver_2,
             color=color_2)
  ax[6].set(ylabel='DRS')
  ax[6].set(xlabel='Lap distance (meters)')

  # Hide x labels and tick labels for top plots and y ticks for right plots.
  for a in ax.flat:
    a.label_outer()
  fig.savefig("telemetry.png")
  with open('telemetry.png', 'rb') as f:
    picture = discord.File(f)
    await ctx.send(file=picture)
  plt.clf()
  telemetry_driver_1['Driver'] = driver_1
  telemetry_driver_2['Driver'] = driver_2

  telemetry = pd.concat([telemetry_driver_1, telemetry_driver_2])
  num_minisectors = 25
  total_distance = max(telemetry['Distance'])
  minisector_length = total_distance / num_minisectors

  minisectors = [0]

  for i in range(0, (num_minisectors - 1)):
    minisectors.append(minisector_length * (i + 1))

  # Assign a minisector number to every row in the telemetry dataframe
  telemetry['Minisector'] = telemetry['Distance'].apply(lambda dist: (int(
    (dist // minisector_length) + 1)))
  # Calculate minisector speeds per driver
  average_speed = telemetry.groupby(['Minisector',
                                     'Driver'])['Speed'].mean().reset_index()

  # Per minisector, find the fastest driver
  fastest_driver = average_speed.loc[average_speed.groupby(
    ['Minisector'])['Speed'].idxmax()]
  fastest_driver = fastest_driver[[
    'Minisector', 'Driver'
  ]].rename(columns={'Driver': 'Fastest_driver'})

  # Merge the fastest_driver dataframe to the telemetry dataframe on minisector
  telemetry = telemetry.merge(fastest_driver, on=['Minisector'])
  telemetry = telemetry.sort_values(by=['Distance'])

  # Since our plot can only work with integers, we need to convert the driver abbreviations to integers (1 or 2)
  telemetry.loc[telemetry['Fastest_driver'] == driver_1,
                'Fastest_driver_int'] = 1
  telemetry.loc[telemetry['Fastest_driver'] == driver_2,
                'Fastest_driver_int'] = 2
  # Get the x and y coordinates
  x = np.array(telemetry['X'].values)
  y = np.array(telemetry['Y'].values)

  # Convert the coordinates to points, and then concat them into segments
  points = np.array([x, y]).T.reshape(-1, 1, 2)
  segments = np.concatenate([points[:-1], points[1:]], axis=1)
  fastest_driver_array = telemetry['Fastest_driver_int'].to_numpy().astype(
    float)
  # The segments we just created can now be colored according to the fastest driver in a minisector
  cmap = ListedColormap([color_1, color_2])
  lc_comp = LineCollection(segments,
                           norm=plt.Normalize(1, cmap.N + 1),
                           cmap=cmap)
  lc_comp.set_array(fastest_driver_array)
  lc_comp.set_linewidth(5)
  # Create the plot
  plt.rcParams['figure.figsize'] = [18, 10]
  plt.title(f'Lap Comparison between {driver_1} and {driver_2}')
  plt.gca().add_collection(lc_comp)
  plt.axis('equal')
  plt.tick_params(labelleft=False, left=False, labelbottom=False, bottom=False)

  cbar = plt.colorbar(mappable=lc_comp,
                      boundaries=np.arange(1, 4),
                      ticks=[driver_1, driver_2])
  cbar.set_ticks(np.arange(1.5, 3.5))
  cbar.set_ticklabels([driver_1, driver_2])
  await ctx.send("Sending Lap Comparison")
  plt.savefig(f"lapcomparison.png")
  with open('lapcomparison.png', 'rb') as f:
    picture = discord.File(f)
    await ctx.send(file=picture)
  ff1.Cache.clear_cache('cache')
  os. system('rm -rf cache/*')


@client.command(name="strategy")
async def _strategy(ctx,arg1,arg2):
  circuit=arg1
  year=arg2
  await ctx.send("{},{}".format(year,circuit))
  race = ff1.get_session(int(year), str(circuit), 'R')
  laps = race.load_laps(with_telemetry=True)
  driver_stints = laps[['Driver', 'Stint', 'Compound', 'LapNumber']].groupby(
    ['Driver', 'Stint', 'Compound']
).count().reset_index()
  driver_stints = driver_stints.rename(columns={'LapNumber': 'StintLength'})
  driver_stints = driver_stints.sort_values(by=['Stint'])
  if int(year) >= 2019:
    compound_colors = {
      'SOFT': '#FF3333',
      'MEDIUM': '#FFF200',
      'HARD': '#EBEBEB',
      'INTERMEDIATE': '#39B54A',
      'WET': '#00AEEF',
    }
  else:
    compound_colors = {
      'HYPERSOFT': '#FFC0CB',
      'ULTRASOFT': '#A020F0',
      'SUPERSOFT': '#FF3333',
      'SOFT': '#FFF200',
      'MEDIUM': '#EBEBEB',
      'HARD': '#ADD8E6',
      'SUPERHARD': '#FFA500',
      'INTERMEDIATE': '#39B54A',
      'WET': '#00AEEF',
    }
  plt.rcParams["figure.figsize"] = [15, 10]
  plt.rcParams["figure.autolayout"] = True

  fig, ax = plt.subplots()

  for driver in race.results['Abbreviation']:
      stints = driver_stints.loc[driver_stints['Driver'] == driver]
      
      previous_stint_end = 0
      for _, stint in stints.iterrows():
          plt.barh(
              [driver], 
              stint['StintLength'], 
              left=previous_stint_end, 
              color=compound_colors[stint['Compound']], 
              edgecolor = "black"
          )
          
          previous_stint_end = previous_stint_end + stint['StintLength']
  for compound, color in compound_colors.items():
    ax.plot([], [], color=color, label=compound)
  ax.legend(fontsize='large', loc='lower right')  
  # Set title
  plt.title(f'Race strategy - {circuit} {year}')
          
  # Set x-label
  plt.xlabel('Lap')

  # Invert y-axis 
  plt.gca().invert_yaxis()

  # Remove frame from plot
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)
  ax.spines['left'].set_visible(False)

  plt.savefig('strategy.png', dpi=300)
  with open('strategy.png', 'rb') as f:
    picture = discord.File(f)
    await ctx.send(file=picture)
  
  #ff1.Cache.clear_cache('cache')
  #os. system('rm -rf cache/*')

keep_alive()
my_secret = os.environ['TOKEN']
client.run(my_secret)
##token = os.environ.get('BOT_TOKEN')
##client.run("")
