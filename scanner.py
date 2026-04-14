import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from telegram import Bot
import asyncio
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime, timedelta

# GitHub Secrets'tan al
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

async def send_telegram(message, image_path=None):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    if image_path:
        with open(image_path, 'rb') as img:
            await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=img, caption=message)
    else:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def create_fethinho_image(rows, date_str, time_str, out_file="fethinho_ai_gunluk.png"):
    plt.rcParams["figure.dpi"] = 150
    fig, ax = plt.subplots(figsize=(12, 7))
    cmap = LinearSegmentedColormap.from_list("sea", [(0/6, "#010614"), (3/6, "#003366"), (6/6, "#0088aa")])
    for i in range(400):
        ax.axhspan(i, i+1, color=cmap(i/400), linewidth=0)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.text(50, 93, "FETHİNH0 AI GÜNLÜK TARAMA", ha="center", va="center", fontsize=26, color="#ffd87a", weight="bold")
    ax.text(50, 86, "GÜÇLÜ AL SİNYALLERİ", ha="center", va="center", fontsize=20, color="#00ffff", weight="bold")
    ax.text(50, 80, f"{date_str} | {time_str} (UTC+3)", ha="center", va="center", fontsize=13, color="#ffffff")
    panel_x, panel_y = 15, 12
    panel_w, panel_h = 70, 62
    rect = Rectangle((panel_x, panel_y), panel_w, panel_h, linewidth=2.5, edgecolor="#00ffff", facecolor=(0, 0, 0, 0.6))
    ax.add_patch(rect)
    headers = ["No", "Sembol", "Fiyat", "RSI", "Not"]
    cols_x = [panel_x + 5, panel_x + 18, panel_x + 35, panel_x + 50, panel_x + 62]
    for h, x in zip(headers, cols_x):
        ax.text(x, panel_y + panel_h - 5, h, ha="center", va="center", fontsize=14, color="#00ffff", weight="bold")
    start_y = panel_y + panel_h - 12
    dy = 6.0
    for i, r in enumerate(rows):
        y = start_y - i * dy
        if y < panel_y + 6: break
        ax.text(cols_x[0], y, str(i+1), ha="center", color="#ffffff", fontsize=12)
        ax.text(cols_x[1], y, r["sembol"], ha="center", color="#ffffff", weight="bold", fontsize=15)
        ax.text(cols_x[2], y, f"{r['fiyat']:.2f}", ha="center", color="#ffff00", fontsize=13, weight="bold")
        ax.text(cols_x[3], y, f"{r['rsi']:.2f}", ha="center", color="#ffffff", fontsize=13)
        ax.text(cols_x[4], y, "Güçlü al", ha="center", color="#00ff00", fontsize=13, weight="bold")
    msg = "Grafiğe değil, sisteme sadık kalan kazandı. Disiplin = Güç."
    ax.text(50, panel_y + 3, msg, ha="center", va="center", fontsize=12, color="#00ffff", style="italic", weight="bold")
    plt.tight_layout()
    fig.savefig(out_file, dpi=200, bbox_inches="tight")
    plt.close(fig)

async def main():
    # Tickers listesi (Colab'den alınacak veya burada tanımlanacak)
    # Kısaltılmış liste örnek olarak
    tickers = ["ARDYZ.IS", "CEOEM.IS", "TCELL.IS", "THYAO.IS", "EREGL.IS", "ASELS.IS", "AKBNK.IS", "ISCTR.IS", "GARAN.IS", "KCHOL.IS"] 
    # Not: Gerçekte tüm listeyi Colab'den kopyalayıp buraya koymak daha iyi olur.
    
    uygun_hisseler = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 50: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            df["EMA_20"] = ta.ema(df["Close"], length=20)
            df["EMA_50"] = ta.ema(df["Close"], length=50)
            df["RSI_14"] = ta.rsi(df["Close"], length=14)
            df["Vol_Ort_10"] = ta.sma(df["Volume"], length=10)
            if len(df) < 2: continue
            son_gun = df.iloc[-1]
            onceki_gun = df.iloc[-2]
            
            fiyat = son_gun["Close"]
            ema20_bugun = son_gun["EMA_20"]
            ema50_bugun = son_gun["EMA_50"]
            ema20_dun = onceki_gun["EMA_20"]
            ema50_dun = onceki_gun["EMA_50"]
            rsi = son_gun["RSI_14"]
            hacim = son_gun["Volume"]
            hacim_ort = son_gun["Vol_Ort_10"]
            
            if pd.isna(ema50_bugun) or pd.isna(ema20_bugun) or pd.isna(rsi): continue
            
            if fiyat >= ema20_bugun and 40 < rsi < 89 and hacim > hacim_ort and ema20_dun <= ema50_dun and ema20_bugun > ema50_bugun:
                uygun_hisseler.append({"sembol": ticker, "fiyat": fiyat, "rsi": rsi})
        except: continue
    
    if uygun_hisseler:
        now = datetime.utcnow() + timedelta(hours=3)
        date_str = now.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M")
        img_path = "fethinho_ai_gunluk.png"
        create_fethinho_image(uygun_hisseler, date_str, time_str, img_path)
                msg = "Fethinho AI Gunluk Tarama - " + date_str + "\n" + str(len(uygun_hisseler)) + " adet guclu sinyal bulundu."
        await send_telegram(msg, img_path)
    else:
        print("Uygun hisse bulunamadı.")

if __name__ == "__main__":
    asyncio.run(main())
