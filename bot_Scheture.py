import discord
import os
from dotenv import load_dotenv
from discord.ext import commands, tasks
from tabulate import tabulate
from datetime import datetime
import sqlite3

conn = sqlite3.connect('jadwal.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS kuliah
               (hari TEXT, jam TEXT, mata_kuliah TEXT, channel_id INTEGER)''')
conn.commit()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@tasks.loop(seconds=60)
async def cek_jadwal():
    sekarang = datetime.now()
    hari_inggris = sekarang.strftime("%A")
    jam_sekarang = sekarang.strftime("%H:%M")

    kamus_hari = {
        "Monday": "Senin", 
        "Tuesday": "Selasa", 
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat", 
        "Saturday": "Sabtu",
        "Sunday": "Minggu"
    }

    hari_indo = kamus_hari.get(hari_inggris, hari_inggris)

    cursor.execute("SELECT mata_kuliah, channel_id from kuliah WHERE hari=? AND jam=?", (hari_indo, jam_sekarang))
    hasil = cursor.fetchall()

    for row in hasil:
        channel = bot.get_channel(row[1])
        await channel.send(f' **PENGINGAT KULIAH** {row[0]} dimulai sekarang!')

@bot.command()
async def tambah_jadwal(ctx, hari, jam, *, matkul):
    daftar_hari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

    if hari.capitalize() not in daftar_hari:
        await ctx.send(f"**Hari tidak valid!** Kamu memasukkan '{hari}'.\nFormat: `!tambah_jadwal [Hari] [Jam] [Matkul]`")
        return
    
    if ":" not in jam:
        await ctx.send(f"❌ **Format Jam salah!** Kamu memasukkan '{jam}'. Gunakan format HH:MM (Contoh: 08:00)")
        return
    
    cursor.execute("INSERT INTO kuliah VALUES(?, ?, ?, ?)", (hari, jam, matkul, ctx.channel.id))
    conn.commit()
    await ctx.send(f"jadwal {matkul} hari {hari} jam {jam} berhasil disimpan!")

@tambah_jadwal.error
async def tambah_jadwal_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('**Format Salah!** Gunakan: `!tambah_jadwal [hari] [jam] [nama_matkul]`')
    else:
        await ctx.send(f'Terjadi Kesalahan {error}')


@bot.command()
async def list_jadwal(ctx):
    cursor.execute("SELECT rowid, hari, jam, mata_kuliah FROM kuliah")
    rows = cursor.fetchall()

    if not rows:
        await ctx.send("Belum ada jadwal yang tersimpan")
        return
    
    headers = ["ID", "Hari", "Jam", "Mata Kuliah"]

    tabel_output = tabulate(rows, headers=headers, tablefmt="grid")

    await ctx.send(f"**Daftar Jadwal Kuliah:**\n```\n{tabel_output}\n```")
    # pesan = "**Daftar Jadwal Kuliah:**\n"
    # for row in rows:
    #     pesan += f"**ID: {row[0]}** | {row[1]} - {row[2]} : {row[3]}\n"

    # await ctx.send(pesan)

@bot.command()
async def hari_ini(ctx):
    hari_inggris = datetime.now().strftime("%A")
    kamus_hari = {
        "Monday": "Senin",
        "Tuesday": "Selasa",
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat",
        "Saturday": "Sabtu",
        "Sunday": "Minggu"
    }

    hari_indo = kamus_hari.get(hari_inggris, hari_inggris)
    cursor.execute('SELECT rowid, hari, jam, mata_kuliah FROM kuliah WHERE hari=? ORDER BY jam ASC', (hari_indo,))
    rows = cursor.fetchall()


    if not rows:
        await ctx.send(f"Hari ini hari {hari_indo}, tidak ada jadwal perkuliahan")
        return
    
    pesan = f'**Jadwal Kuliah Hari Ini {hari_indo}**\n'
    pesan += "```\n"
    pesan += f"{'ID':<4} | {'JAM':<7} | {'MATA KULIAH'}\n"
    pesan += "-" * 35 + '\n'

    for row in rows:
        pesan += f"{str(row[0]):<4} | {row[2]:<7} | {row[3]}\n"

    pesan += "```"

    await ctx.send(pesan)
        
        # await ctx.send(f'**ID: {row[0]}** | {row[1]} - {row[2]} : {row[3]}')
    

@bot.command()
async def hapus_jadwal(ctx, id_jadwal: int):
    cursor.execute("SELECT mata_kuliah FROM kuliah WHERE rowid=?", (id_jadwal,))
    data = cursor.fetchone()

    if data:
        cursor.execute("DELETE FROM kuliah WHERE rowid=?", (id_jadwal,))
        conn.commit()
        await ctx.send(f'Jadwal **{data[0]}** (ID: {id_jadwal}) telah dihapus!')
    else:
        await ctx.send(f'Tidak ditemukan jadwal dengan ID: {id_jadwal}')

@bot.command()
async def ubah_jam(ctx, id_jadwal: int, jam_baru: str):
    cursor.execute('SELECT mata_kuliah FROM kuliah WHERE rowid=?', (id_jadwal,))
    data = cursor.fetchone()

    if data:
        cursor.execute("UPDATE kuliah SET jam=? WHERE rowid=?",(jam_baru, id_jadwal))
        conn.commit()
        await ctx.send(f'Jam kuliah **{data[0]}** berhasil diubah menjadi **{jam_baru}**')
    else:
        await ctx.send(f'Tidak ditemukan jadwal dengan ID: {id_jadwal}')

@bot.command()
async def ubah_matkul(ctx, id_jadwal: int, matkul_baru: str):
    cursor.execute('SELECT mata_kuliah FROM kuliah WHERE rowid=?', (id_jadwal,))
    data = cursor.fetchone()

    if data:
        cursor.execute('UPDATE kuliah SET mata_kuliah=? WHERE rowid=?', (matkul_baru, id_jadwal))
        conn.commit()
        await ctx.send(f'Mata kuliah **{data[0]}** berhasil diubah menjadi **{matkul_baru}**')
    else:
        await ctx.send(f'Tidak ditemukan matkul dengan ID: {id_jadwal}')

@bot.command()
async def phelp(ctx):
    await ctx.send(f'''Command:
                   !list_jadwal: Melihat jadwal
                   !hari_ini: Melihat jadwal hari ini
                   !tambah_jadwal: Menambahkan jadwal [hari] [jam] [matkul]
                   !hapus_jadwal: Menghapus jadwal [id_jadwal]
                   !ubah_jam: Merubah atau Update jam jadwal [jam] [id_jadwal]
                   !ubah_matkul: Merubah atau Update Mata Kuliah [id_jadwal] [matkul]''')


@bot.event
async def on_ready():
    cek_jadwal.start()
    print(f'Bot {bot.user} sudah online!')


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)