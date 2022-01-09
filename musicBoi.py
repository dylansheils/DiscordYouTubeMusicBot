import os
import random
import time
from discord.ext import commands
import discord
from pytube import YouTube
import os
import asyncio

TOKEN = "NOTAPPLICABLE"

bot = commands.Bot(command_prefix=("?"))

class OurBot(commands.Cog):
    import portalocker
    enumeration = 0
    songsInQueue = []
    peopleQueue = []
    issuers = []
    locked = False
    endSong = False
    fileLatest = "temp.mp3"
    filesToRemove = []

    def __init__(self, bot):
        self.bot = bot
        print("Bot in Server")

    def isFileLocked(self, filePath):
        if not (os.path.exists(filePath)):
            return False
        try:
            f = open(filePath, 'r')
            f.close()
        except IOError:
            return True

        lockFile = filePath + ".lckchk"
        if (os.path.exists(lockFile)):
            os.remove(lockFile)
        try:
            os.rename(filePath, lockFile)
            os.rename(lockFile, filePath)
            return False
        except WindowsError:
            return True

    def keepTrying(self, name):
        while self.isFileLocked(name):
            time.sleep(1)
        os.remove(name)

    def deleteFile(self, name):
        if not os.path.exists(name):
            return
        try:
            os.remove(name)
        except:
            self.filesToRemove.append(name)
            return

    async def playMusic(self, vc):
        while vc != None and vc.is_playing() and self.endSong == False:
            await asyncio.sleep(1)
        try:
            self.songsInQueue.pop(0)
            self.peopleQueue.pop(0)
            self.issuers.pop(0)
        except:
            pass
        self.locked = False
        self.deleteFile(self.fileLatest)
        print("Called Deleted File...continuing queue...")
        time.sleep(1)
        self.endSong = False
        await self.continueQueue()

    async def continueQueue(self):
        if (len(self.songsInQueue) > 0):
            print("Continuing Queue...", " with: ", self.songsInQueue[0])
            ctxVC, channel = self.peopleQueue[0]
            self.locked = True
            if ctxVC is not None:
                await ctxVC.move_to(channel)
            if ctxVC is None:
                try:
                    ctxVC = await channel.connect()
                except:
                    pass
            time.sleep(1)
            self.fileLatest = self.songsInQueue[0]
            if ctxVC != None and ctxVC.is_playing:
                ctxVC.stop()
            try:
                ctxVC.play(discord.FFmpegPCMAudio(self.songsInQueue[0]))
            except:
                pass
            await self.playMusic(ctxVC)
        if(len(self.filesToRemove) > 0):
            fileRemove = self.filesToRemove.pop(0)
            self.keepTrying(fileRemove)
            await self.continueQueue()


    @commands.command()
    async def play(self, ctx):
        urlLink = ctx.message.content[5:]
        if "https://" not in urlLink:
            return
        yt = YouTube(str(urlLink))
        video = yt.streams.filter(only_audio=True).first()
        out_file = video.download(output_path=".")
        base, ext = os.path.splitext(out_file)
        tempEnum = str(self.enumeration)
        new_file = tempEnum + '.mp3'
        self.enumeration += 1
        time.sleep(2)
        try:
            os.rename(out_file, new_file)
        except:
            self.deleteFile(new_file)
            os.rename(out_file, new_file)
            pass
        self.songsInQueue.append(new_file)
        self.peopleQueue.append((ctx.voice_client, ctx.message.author.voice.channel))
        self.issuers.append(ctx.author.name)
        if not self.locked:
            self.fileLatest = new_file
            await self.continueQueue()

    @commands.command()
    async def queue(self, ctx):
        title = ctx.author.name
        response = ""
        position = -1
        if title in self.issuers:
            position = self.issuers.index(title) + 1
        if position != -1:
            response += "Hello " + title + ", your position in the queue is: " + str(position)
        else:
            response += "Hello " + title + ", you are not currently in the queue"
        await ctx.send(response)

    @commands.command()
    async def shuffle(self, ctx):
        print("Recieved Shuffle Command...")
        person = ctx.author.name
        songsOrdered = []
        index = 0
        for i in self.issuers:
            if self.fileLatest != self.songsInQueue[index] and i == person:
                songsOrdered.append(self.songsInQueue[index])
            index += 1
        print(self.songsInQueue)
        print(songsOrdered)
        random.shuffle(songsOrdered)
        index = 0
        indexInOrdering = 0
        for i in self.issuers:
            if self.fileLatest != self.songsInQueue[index] and i == person:
                self.songsInQueue[index] = songsOrdered[indexInOrdering]
                indexInOrdering += 1
            index += 1
        print(self.songsInQueue)
        print(songsOrdered)
        await ctx.send("Please note that Shuffling only shuffles songs not actively playing...please skip to "
                       "experience the shuffle")



    @commands.command()
    async def leave(self, ctx):
        print("Recieved Leave Command...")
        title = ctx.author.name
        while title in self.issuers:
            removeThisFile = self.songsInQueue[self.issuers.index(title)]
            if removeThisFile == self.fileLatest and title not in self.issuers[1:]:
                self.endSong = True
                if ctx != None:
                    await ctx.voice_client.disconnect()
            else:
                if title in self.issuers[1:]:
                    self.endSong = True
                    self.locked = False
                    while title in self.issuers[1:]:
                        indice = self.issuers[1:].index(title)
                        self.issuers.pop(indice)
                        self.peopleQueue.pop(indice)
                        self.deleteFile(self.songsInQueue[indice])
                        self.songsInQueue.pop(indice)
                    await self.continueQueue()
                else:
                    self.deleteFile(removeThisFile)
                    self.songsInQueue.pop(self.issuers.index(title))
                    self.peopleQueue.pop(self.issuers.index(title))


    @commands.command()
    async def skip(self, ctx):
        print("Recieved Skip Command...")
        title = ctx.author.name
        if self.issuers[0] != title:
            await ctx.send("Sorry, you are not playing and, so, you cannot skip, please leave the queue")
            return
        while title in self.issuers:
            removeThisFile = self.songsInQueue[self.issuers.index(title)]
            if removeThisFile == self.fileLatest and title not in self.issuers[1:]:
                self.endSong = True
                if ctx != None:
                    await ctx.voice_client.disconnect()
            else:
                if title in self.issuers[1:]:
                    self.endSong = True
                    self.locked = False
                    await self.continueQueue()
                else:
                    self.deleteFile(removeThisFile)
                    self.songsInQueue.pop(self.issuers.index(title))
                    self.peopleQueue.pop(self.issuers.index(title))

    @commands.Cog.listener() #Let's not be antisocial
    async def on_message(self, message):
        if message.author.bot:
            return  # ignore bots

bot.add_cog(OurBot(bot))
bot.run(TOKEN)