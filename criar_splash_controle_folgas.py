# -*- coding: utf-8 -*-
"""Gera Logo/splash.png para o splash nativo do PyInstaller.

Execute uma vez antes de gerar o EXE:
    python criar_splash_controle_folgas.py

O script usa o logo já existente na pasta Logo e cria uma imagem RGB 620x360,
sem otimizações especiais de PNG para maximizar a compatibilidade com Tcl/Tk.
Não altera os arquivos de logo originais.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH = 620
HEIGHT = 360
OUTPUT_NAME = "splash.png"


def project_dir() -> Path:
    return Path(__file__).resolve().parent


def find_logo(logo_dir: Path) -> Path | None:
    candidates = [
        logo_dir / "logo 3D.png",
        logo_dir / "logo.png",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def load_font(size: int, semibold: bool = False):
    windows_fonts = Path("C:/Windows/Fonts")
    candidates = [
        windows_fonts / ("seguisb.ttf" if semibold else "segoeui.ttf"),
        windows_fonts / "arial.ttf",
    ]
    for path in candidates:
        try:
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def centered_x(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    return max(0, (WIDTH - width) // 2)


def main():
    root = project_dir()
    logo_dir = root / "Logo"
    logo_dir.mkdir(parents=True, exist_ok=True)
    output = logo_dir / OUTPUT_NAME

    # Fundo escuro alinhado à identidade visual atual do programa.
    image = Image.new("RGBA", (WIDTH, HEIGHT), (12, 24, 44, 255))
    draw = ImageDraw.Draw(image)

    # Leve variação vertical para evitar um fundo totalmente chapado.
    for y in range(HEIGHT):
        ratio = y / max(1, HEIGHT - 1)
        r = int(12 + (4 * ratio))
        g = int(24 + (8 * ratio))
        b = int(44 + (15 * ratio))
        draw.line((0, y, WIDTH, y), fill=(r, g, b, 255))

    logo_path = find_logo(logo_dir)
    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            max_side = 145
            logo.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            x = (WIDTH - logo.width) // 2
            y = 28
            image.alpha_composite(logo, (x, y))
        except Exception:
            pass

    title_font = load_font(25, semibold=True)
    subtitle_font = load_font(13, semibold=False)
    small_font = load_font(10, semibold=False)

    title = "Controle de Folgas e Banco de Horas"
    subtitle = "Inicializando o sistema"
    hint = "Aguarde enquanto os componentes são carregados..."

    draw.text(
        (centered_x(draw, title, title_font), 190),
        title,
        font=title_font,
        fill=(242, 247, 255, 255),
    )
    draw.text(
        (centered_x(draw, subtitle, subtitle_font), 233),
        subtitle,
        font=subtitle_font,
        fill=(118, 190, 255, 255),
    )

    # Linha discreta acima da área onde o PyInstaller mostrará o texto dinâmico.
    draw.rounded_rectangle(
        (28, 291, WIDTH - 28, 293),
        radius=1,
        fill=(55, 91, 135, 255),
    )
    draw.text(
        (centered_x(draw, hint, small_font), 302),
        hint,
        font=small_font,
        fill=(151, 169, 194, 255),
    )

    image = image.convert("RGB")
    image.save(output, "PNG", compress_level=1)
    print(f"Splash criado com sucesso: {output}")


if __name__ == "__main__":
    main()
