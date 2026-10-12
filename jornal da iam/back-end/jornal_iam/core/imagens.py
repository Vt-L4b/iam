from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

LADO_MAXIMO = 1600  # px: suficiente para tela cheia sem pesar no disco
QUALIDADE_JPEG = 82


def reduzir_imagem(arquivo):
    """Gira a foto conforme o celular a tirou, reduz para no máximo LADO_MAXIMO px e salva em JPEG.

    Como o JPEG é gerado do zero, os metadados da foto original (inclusive a localização GPS)
    não vão junto, o que importa em fotos de crianças.
    """
    imagem = Image.open(arquivo)
    imagem = ImageOps.exif_transpose(imagem)

    if imagem.mode in ('RGBA', 'LA', 'P'):
        # JPEG não tem transparência: coloca um fundo branco no lugar
        imagem = imagem.convert('RGBA')
        fundo = Image.new('RGB', imagem.size, 'white')
        fundo.paste(imagem, mask=imagem.getchannel('A'))
        imagem = fundo
    else:
        imagem = imagem.convert('RGB')

    imagem.thumbnail((LADO_MAXIMO, LADO_MAXIMO))

    saida = BytesIO()
    imagem.save(saida, 'JPEG', quality=QUALIDADE_JPEG, optimize=True)
    return ContentFile(saida.getvalue(), name=f"{Path(arquivo.name).stem}.jpg")
