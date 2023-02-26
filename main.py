###################################################################################################
# Imports
import os # For importing secrets from replit
from nextcord.ext import commands # # allow us to make .play a command
import nextcord # For making Bot
import datetime # For the duration of a song
import wavelink # For discord voice stuff
from wavelink.ext import spotify # For Spotify integration for wavelink
#from nextcord import Interaction, SlashOption, ChannelType # For slash commands
#from nextcord.abc import GuildChannel # 
###################################################################################################
# For intents for the bot to use when connecting to discord api
intents = nextcord.Intents.default()
intents.message_content = True
intents.voice_states = True
###################################################################################################
# Secrets imported from replit's "mySecret" feature
TOKEN = os.environ['TOKEN'] # Token for the bot to interact with discord
spotify_id = os.environ['spotify_id'] # The spotify app id
spotify_secret = os.environ['spotify_secret'] # The spotify app secret
###################################################################################################
# Sets the name from commands.Bot to just bot and sets the prefix and intents
bot = commands.Bot(command_prefix=".", intents = intents)
###################################################################################################
# Subprograms that trigger when an event is recieved from discord
@bot.event
async def on_ready(): # When the bot is connected to discord api
  print("Bot is online") # Prints to the console
  bot.loop.create_task(node_connect()) # Creates a "task" and runs the subprogram node_connect()

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
  print(f"Node {node.identifier} is connected") # Prints to console the name of the node connected

async def node_connect():
  await bot.wait_until_ready()
  await wavelink.NodePool.create_node(bot= bot, host= "eu-lavalink.lexnet.cc", port=443, password="lexn3tl@val!nk", https= True, spotify_client=spotify.SpotifyClient(client_id=spotify_id, client_secret=spotify_secret))

@bot.event 
async def on_wavelink_track_end(player: wavelink.Player, track: wavelink.Track, reason):
  ctx = player.ctx
  vc: player = ctx.voice_client

  if vc.loop:
    return await vc.play(track)

  next_song = vc.queue.get()
  await vc.play(next_song)
  await vc.send(f"Now playing: {next_song.title}")
###################################################################################################
# Play commands using text
@bot.command()
async def splay(ctx: commands.Context, *, search:str):
  if not ctx.voice_client:
    vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.reply("Join a voice channel.")
  else:
    vc: wavelink.Player = ctx.voice_client

  if vc.queue.is_empty and not vc.is_playing():
    try:
      track = await spotify.SpotifyTrack.search(query=search, return_first=True)
      await vc.play(track)
      await ctx.send(f"Playing '{track.title}'") 
    except Exception as e:
      return await ctx.reply("Please enter a valid spotify song url")
      await print(e)
  else:
    try:
      track = await spotify.SpotifyTrack.search(query=search, return_first=True)
      await vc.queue.put_wait(track)
      await ctx.send(f"Added '{track.title}' to queue")
    except Exception as e:
      return await ctx.reply("Please enter a valid spotify song url")
      await print(e)
  vc.ctx = ctx
  if vc.loop:
    return
  setattr(vc, "loop", False)

@bot.command()
async def play(ctx: commands.Context, *, search: wavelink.YouTubeTrack):
  if not ctx.voice_client:
    vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.reply("Join a voice channel.")
  else:
    vc: wavelink.Player = ctx.voice_client

  if vc.queue.is_empty and not vc.is_playing():
    await vc.play(search)
    await ctx.send(f"Playing '{search.title}'")    
  else:
    await vc.queue.put_wait(search)
    await ctx.send(f"Added '{search.title}' to queue")
  vc.ctx = ctx
  setattr(vc, "loop", False)
###################################################################################################
# Adds basic controls for the bot
@bot.command()
async def pause(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.reply("You're not playing any music...")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.reply("Join a voice channel.")
  else:
    vc: wavelink.Player = ctx.voice_client
  await vc.pause()
  await ctx.reply("Paused")

@bot.command()
async def resume(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.reply("You're not playing any music...")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.reply("Join a voice channel.")
  else:
    vc: wavelink.Player = ctx.voice_client

  await vc.resume()
  await ctx.reply("Resumed")

@bot.command()
async def skip(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.reply("You're not playing any music...")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.reply("Join a voice channel.")
  else:
    vc: wavelink.Player = ctx.voice_client

  await vc.stop()
  await ctx.reply("Skipped the song")

@bot.command()
async def leave(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.reply("You're not playing any music...")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.reply("Join a voice channel.")
  else:
    vc: wavelink.Player = ctx.voice_client

  await vc.disconnect()
  await ctx.reply("I have left the vc 😢")

@bot.command()
async def loop(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.reply("I'm not in a vc...")
  elif not ctx.author.voice:
    return await ctx.reply("You're not in a voice channel...")
  else:
    vc: wavelink.Player = ctx.voice_client

  try:
    vc.loop ^= True
  except Exception:
    setattr(vc, "loop", False)

  if vc.loop:
    return await ctx.reply("Loop is now Enabled")
  else:
    return await ctx.reply("Loop is now Disabled")

@bot.command()
async def queue(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.reply("I'm not in a vc...")
  elif not ctx.author.voice:
    return await ctx.reply("You're not in a voice channel...")
  else:
    vc: wavelink.Player = ctx.voice_client

  if vc.queue.is_empty:
    return await ctx.send("Queue is empty")

  em = nextcord.Embed(title="Queue")
  queue = vc.queue.copy()
  song_count = 0
  for song in queue:
    song_count += 1
    em.add_field(name=f"Song {song_count}", value=f"{song.title}")
  return await ctx.send(embed=em)

@bot.command()
async def volume(ctx: commands.Context, volume: int):
  if not ctx.voice_client:
    return await ctx.reply("I'm not in a vc")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.reply("Join a vc first")
  else:
    vc: wavelink.Player = ctx.voice_client

  if volume > 100:
    return await ctx.reply("Voulume cannot be above 100%")
  elif volume < 0:
    return await ctx.reply("Volume cannot be below 0%")
  else:
    await vc.set_volume(volume)
    return await ctx.send(f"Volume has been set to {volume}%")

@bot.command()
async def nowplaying(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.reply("I'm not in a vc")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.reply("Join a vc first")
  else:
    vc: wavelink.Player = ctx.voice_client

  if not vc.is_playing(): 
    return await ctx.reply("Nothing is playing")

  em = nextcord.Embed(title=f"Now Playing {vc.track.title}", description=f"By {vc.track.author}")
  em.add_field(name="Duration", value=f"`{str(datetime.timedelta(seconds=vc.track.length))}`")
  em.add_field(name="Extra Info", value=f"[Song Url]({str(vc.track.uri)})")
  return await ctx.send(embed=em)
###################################################################################################
# Begining of slash commands
#@bot.slash_command()
#async def join(interaction: Interaction):
#  """Joins your voice channel"""
#  
#  await interaction.response.send_message("I have joined your vc")
###################################################################################################
# Main Program
bot.run(TOKEN) # Runs the whole bot using the bot's discord token