import os
import urllib.request
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
import matplotlib.pyplot as plt
from instagrapi import Client
from options import PUBLISH
from custom_logger import CustomLogger

SESSION_FILE = "insta_session.json"
logger = CustomLogger(__name__)

def create_co2_image(data_points, background_path, font_paths, output_path):
    """
    Génère une image Instagram Story montrant l'évolution du taux de CO2.

    Parameters:
    - data_points: dict avec les clés '10ans', '1an', '2sem', '1sem' et leurs valeurs en ppm
    - background_path: chemin vers l'image de fond
    - font_paths: dict avec les chemins des polices 'title' et 'text'
    - output_path: chemin de sortie pour l'image générée
    """
    # 1) Création du graphique
    labels = ['10 ans', '1 an', '2 sem.', '1 sem.']
    values = [data_points['10ans'], data_points['1an'], data_points['2sem'], data_points['1sem']]

    fig, ax = plt.subplots(figsize=(4, 3), dpi=100, facecolor='none')
    bars = ax.bar(labels, values, color='#FFA500')
    for b in bars:
        h = b.get_height()
        ax.text(
            b.get_x() + b.get_width() / 2,
            h + 1,
            f"{h:.1f}",
            ha='center', va='bottom', color='white'
        )
    ax.set_title('CO₂ (ppm)', color='white')
    ax.tick_params(colors='white')
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='white')
    ax.set_ylim(min(values) - 5, max(values) + 5)

    buf = BytesIO()
    fig.savefig(buf, format='png', transparent=True, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    # 2) Composition de l'image
    bg = Image.open(background_path).convert('RGBA')
    W, H = bg.size
    draw = ImageDraw.Draw(bg)

    # Chargement des polices
    try:
        font_title = ImageFont.truetype(font_paths['title'], 60)
        font_txt   = ImageFont.truetype(font_paths['text'], 40)
    except:
        font_title = ImageFont.load_default()
        font_txt   = ImageFont.load_default()

    # Titre
    title = 'Évolution du taux de CO2'
    bbox = draw.textbbox((0,0), title, font=font_title)
    w_t, h_t = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((W - w_t) / 2, 20), title, fill='white', font=font_title)

    # Texte descriptif
    description = (
        f"La semaine dernière  : {data_points['1sem']:.2f} ppm\n"
        f"Il y a deux semaines  : {data_points['2sem']:.2f} ppm\n"
        f"Il y a 1 an          : {data_points['1an']:.2f} ppm\n"
        f"Il y a 10 ans        : {data_points['10ans']:.2f} ppm"    
    )
    lines_txt = description.splitlines()
    w0 = max(draw.textbbox((0,0), line, font=font_txt)[2] for line in lines_txt)
    x0 = (W - w0) / 2
    y_cursor = 20 + h_t + 10

    for line in lines_txt:
        _, h_line = draw.textbbox((0,0), line, font=font_txt)[2:]
        draw.text((x0, y_cursor), line, fill='white', font=font_txt)
        y_cursor += h_line + 5

    # Collage du graphique
    chart = Image.open(buf).convert('RGBA')
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = getattr(Image, 'LANCZOS', Image.BICUBIC)
    new_w = W - 80
    new_h = int(new_w * chart.height / chart.width)
    chart = chart.resize((new_w, new_h), resample=resample_filter)
    bg.paste(chart, ((W - new_w) // 2, int(y_cursor + 10)), chart)

    # Sauvegarde
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bg.save(output_path)
    return output_path


if __name__ == '__main__':
    # --- 1) Récupération des données CO₂ ---
    url = 'https://www.esrl.noaa.gov/gmd/webdata/ccgg/trends/co2/co2_weekly_mlo.txt'
    urllib.request.urlretrieve(url, 'co2.txt')

    with open('co2.txt') as f:
        lines = f.read().splitlines()

    last = lines[-1].split()
    prev = lines[-2].split()
    data = {
        '1sem': float(last[4]),
        '2sem': float(prev[4]),
        '1an':  float(last[6]),
        '10ans': float(last[7])
    }

    # --- Génération et publication ---
    out_path = create_co2_image(
        data,
        background_path='assets/images/carbonBG.jpg',
        font_paths={
            'title': 'assets/fonts/Arial.ttf',
            'text': 'assets/fonts/Arial.ttf'
        },
        output_path='Image/carbon_story.png'
    )
    print(f"Image enregistrée : {out_path}")

    if PUBLISH:
        bot = Client()
        bot.login(os.getenv('LOGIN_INSTAGRAM'), os.getenv('PASSWORD_INSTAGRAM'))

        if os.path.exists(SESSION_FILE):
            logger.debug(f"Session file found at {SESSION_FILE}, loading...")
            try:
                bot.load_settings(SESSION_FILE)
                logger.info("Loaded existing session settings successfully")
            except Exception as e:
                logger.error(f"Failed to load session settings: {e}")

        bot.photo_upload_to_story(out_path, caption='Taux de CO₂ 🌍')
        print('Publié en story !')
