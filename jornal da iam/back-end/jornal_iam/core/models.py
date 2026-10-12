import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from .imagens import reduzir_imagem


class ComImagem:
    """Para models com uma imagem que pode ser enviada (campo `foto`) ou vir de um link (campo `imagem`)."""

    def clean(self):
        super().clean()
        if not self.foto and not self.imagem:
            raise ValidationError("Envie uma imagem ou cole o link de uma.")

    @property
    def url_da_imagem(self):
        return self.foto.url if self.foto else self.imagem

    def save(self, *args, **kwargs):
        antiga = None
        if self.pk:
            antiga = type(self).objects.filter(pk=self.pk).values_list('foto', flat=True).first()

        if self.foto and not self.foto._committed:  # arquivo recém-enviado
            self.foto = reduzir_imagem(self.foto)

        super().save(*args, **kwargs)

        # Foto trocada ou removida: apaga o arquivo antigo para não ocupar disco
        if antiga and antiga != self.foto.name:
            self.foto.storage.delete(antiga)


class Grupo(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Usado no endereço da página do grupo, ex.: iam-sao-jose")
    paroquia = models.CharField("paróquia", max_length=150, blank=True)
    cidade = models.CharField(max_length=100)
    uf = models.CharField("UF", max_length=2)
    logo = models.URLField(blank=True)
    coordenadores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='grupos_iam',
        help_text="Quem pode publicar edições e fotos deste grupo no painel.",
    )

    class Meta:
        ordering = ['nome']
        verbose_name = "grupo da IAM"
        verbose_name_plural = "grupos da IAM"

    def __str__(self):
        return f"{self.nome} ({self.cidade}/{self.uf})"


class Edicao(ComImagem, models.Model):
    # Sem grupo = edição geral da plataforma
    grupo = models.ForeignKey(Grupo, on_delete=models.SET_NULL, null=True, blank=True, related_name='edicoes')
    numero = models.PositiveIntegerField("número", null=True, blank=True)
    titulo = models.CharField("título", max_length=100)
    descricao = models.TextField("descrição")
    foto = models.ImageField("enviar capa", upload_to='capas/%Y/', blank=True)
    imagem = models.URLField("ou link da capa", blank=True)
    link = models.URLField(
        blank=True,
        help_text="Link do PDF no Google Drive (compartilhado com 'qualquer pessoa com o link') "
                  "ou de outro site, como Canva ou Issuu.",
    )
    publicado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-publicado_em']
        verbose_name = "edição"
        verbose_name_plural = "edições"

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('edicao', args=[self.pk])

    @property
    def link_incorporavel(self):
        """Endereço de visualização do Drive para usar num <iframe>, ou None se o link não for do Drive."""
        encontrado = re.search(r'drive\.google\.com/file/d/([\w-]+)', self.link)
        if encontrado:
            return f"https://drive.google.com/file/d/{encontrado.group(1)}/preview"
        return None


class Destaques(ComImagem, models.Model):
    titulo = models.CharField("título", max_length=100, blank=True)
    descricao = models.CharField("descrição", max_length=200, blank=True)
    foto = models.ImageField("enviar imagem", upload_to='destaques/', blank=True)
    imagem = models.URLField("ou link da imagem", blank=True)
    # Quando a atividade saiu no jornal, o destaque leva até a edição
    edicao = models.ForeignKey(Edicao, on_delete=models.SET_NULL, null=True, blank=True, related_name='destaques')
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = "destaque"
        verbose_name_plural = "destaques"

    def __str__(self):
        return self.titulo or f"Imagem {self.id}"


class Outros_grupos(ComImagem, models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.SET_NULL, null=True, blank=True, related_name='fotos')
    foto = models.ImageField("enviar foto", upload_to='fotos/%Y/%m/', blank=True)
    imagem = models.URLField("ou link da foto", blank=True)
    descricao = models.TextField("descrição")
    data = models.DateField(null=True, blank=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = "foto de outro grupo"
        verbose_name_plural = "fotos de outros grupos"

    def __str__(self):
        return f"Imagem {self.id}"


@receiver(post_delete, sender=Edicao)
@receiver(post_delete, sender=Destaques)
@receiver(post_delete, sender=Outros_grupos)
def apagar_arquivo_da_imagem(sender, instance, **kwargs):
    if instance.foto:
        instance.foto.delete(save=False)
