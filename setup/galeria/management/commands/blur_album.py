import os
import shutil

import cv2
import numpy as np
from django.core.management.base import BaseCommand, CommandError

from galeria.models import Album, Fotografia


# cv2.imread/imwrite falham com acentos no caminho no Windows; estas funções não
def ler_imagem(caminho):
    dados = np.fromfile(caminho, dtype=np.uint8)
    return cv2.imdecode(dados, cv2.IMREAD_COLOR)


def salvar_imagem(caminho, img, qualidade):
    ext = os.path.splitext(caminho)[1].lower() or ".jpg"
    params = [cv2.IMWRITE_JPEG_QUALITY, qualidade] if ext in (".jpg", ".jpeg") else []
    ok, buffer = cv2.imencode(ext, img, params)
    if not ok:
        raise IOError(f"Falha ao salvar {caminho}")
    buffer.tofile(caminho)


def ler_poligono(texto):
    try:
        pontos = [tuple(float(v) for v in par.split(",")) for par in texto.split()]
    except ValueError:
        raise CommandError('Formato do polígono: "x,y x,y x,y ..."')
    if len(pontos) < 3:
        raise CommandError("O polígono precisa de pelo menos 3 pontos.")
    return pontos


def desenhar_poligono(img):
    """Abre uma janela para desenhar o polígono. Retorna pontos em pixels da imagem."""
    pontos = []
    h, w = img.shape[:2]
    escala = min(1600 / w, 800 / h, 1.0)
    tela = cv2.resize(img, (int(w * escala), int(h * escala)))

    def mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            pontos.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN and pontos:
            pontos.pop()

    janela = "Poligono (Esq: adiciona | Dir: desfaz | C: limpa | Enter: confirma | Esc: cancela)"
    cv2.namedWindow(janela)
    cv2.setMouseCallback(janela, mouse)

    while True:
        temp = tela.copy()
        for pt in pontos:
            cv2.circle(temp, pt, 5, (0, 0, 255), -1)
        if len(pontos) >= 2:
            cv2.polylines(temp, [np.array(pontos, np.int32)],
                          isClosed=len(pontos) >= 3, color=(0, 255, 0), thickness=2)
        cv2.imshow(janela, temp)

        tecla = cv2.waitKey(20) & 0xFF
        if tecla == 13 and len(pontos) >= 3:   # Enter
            break
        if tecla == ord("c"):
            pontos.clear()
        if tecla == 27:                         # Esc
            cv2.destroyAllWindows()
            raise CommandError("Cancelado.")

    cv2.destroyAllWindows()
    return [(x / escala, y / escala) for x, y in pontos]


def aplicar_blur(img, pontos_norm, forca, suavizar):
    h, w = img.shape[:2]
    pts = np.array([(int(x * w), int(y * h)) for x, y in pontos_norm], np.int32)

    # Trabalha só na região do polígono (com margem) para ser rápido
    x, y, bw, bh = cv2.boundingRect(pts)
    pad = int(forca * 2)
    x1, y1 = max(0, x - pad), max(0, y - pad)
    x2, y2 = min(w, x + bw + pad), min(h, y + bh + pad)

    roi = img[y1:y2, x1:x2]
    mascara = np.zeros(roi.shape[:2], np.uint8)
    cv2.fillPoly(mascara, [pts - np.array([x1, y1], np.int32)], 255)
    if suavizar > 0:
        mascara = cv2.GaussianBlur(mascara, (0, 0), suavizar)

    borrada = cv2.GaussianBlur(roi, (0, 0), forca)
    alpha = (mascara / 255.0)[..., None]
    img[y1:y2, x1:x2] = (borrada * alpha + roi * (1 - alpha)).astype(np.uint8)
    return img


class Command(BaseCommand):
    help = "Aplica blur numa área (polígono) em todas as fotos de um álbum."

    def add_arguments(self, parser):
        parser.add_argument("album_id", type=int, help="ID do álbum")
        parser.add_argument("--poligono", type=str,
                            help='Pontos em pixels da 1ª foto: "x,y x,y x,y ...". '
                                 "Se omitido, abre uma janela para desenhar.")
        parser.add_argument("--forca", type=float, default=40,
                            help="Intensidade do blur (sigma). Padrão 40")
        parser.add_argument("--suavizar", type=float, default=15,
                            help="Suavização da borda do polígono. 0 = borda seca")
        parser.add_argument("--qualidade", type=int, default=90)
        parser.add_argument("--backup", type=str,
                            help="Pasta para copiar os originais antes de alterar")
        parser.add_argument("--dry-run", action="store_true",
                            help="Apenas mostra o que seria feito")

    def handle(self, *args, **opts):
        try:
            album = Album.objects.get(pk=opts["album_id"])
        except Album.DoesNotExist:
            raise CommandError(f"Álbum {opts['album_id']} não existe.")

        fotos = [f for f in Fotografia.objects.filter(album=album).order_by("id") if f.foto]
        if not fotos:
            raise CommandError("O álbum não tem fotos.")
        self.stdout.write(f"Álbum: {album.title} — {len(fotos)} fotos")

        # A primeira foto serve de referência para o polígono
        ref = ler_imagem(fotos[0].foto.path)
        if ref is None:
            raise CommandError(f"Não consegui abrir {fotos[0].foto.path}")
        rh, rw = ref.shape[:2]

        if opts["poligono"]:
            pontos_px = ler_poligono(opts["poligono"])
        else:
            pontos_px = desenhar_poligono(ref)

        # Guarda em proporção, para funcionar mesmo se alguma foto tiver outro tamanho
        pontos_norm = [(x / rw, y / rh) for x, y in pontos_px]

        texto = " ".join(f"{int(x)},{int(y)}" for x, y in pontos_px)
        self.stdout.write(f'Polígono: --poligono "{texto}"')

        if opts["dry_run"]:
            for f in fotos:
                self.stdout.write(f"  [dry] {f.id}: {os.path.basename(f.foto.path)}")
            return

        if opts["backup"]:
            os.makedirs(opts["backup"], exist_ok=True)

        for f in fotos:
            caminho = f.foto.path
            img = ler_imagem(caminho)
            if img is None:
                self.stdout.write(self.style.WARNING(f"  pulei {f.id}: não abriu"))
                continue

            if opts["backup"]:
                destino = os.path.join(opts["backup"], f"{f.id}_{os.path.basename(caminho)}")
                shutil.copy2(caminho, destino)

            img = aplicar_blur(img, pontos_norm, opts["forca"], opts["suavizar"])
            salvar_imagem(caminho, img, opts["qualidade"])
            self.stdout.write(f"  ok {f.id}: {os.path.basename(caminho)}")

        self.stdout.write(self.style.SUCCESS("Blur aplicado em todas as fotos."))