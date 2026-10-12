import shutil
import tempfile
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Edicao, Grupo, Outros_grupos


class LinkIncorporavelTests(TestCase):
    def test_link_do_drive_vira_preview(self):
        edicao = Edicao(link="https://drive.google.com/file/d/1AbC-d_E/view?usp=sharing")
        self.assertEqual(edicao.link_incorporavel, "https://drive.google.com/file/d/1AbC-d_E/preview")

    def test_link_de_outro_site_nao_e_incorporado(self):
        self.assertIsNone(Edicao(link="https://www.canva.com/design/abc/view").link_incorporavel)

    def test_sem_link(self):
        self.assertIsNone(Edicao(link="").link_incorporavel)


class PaginasTests(TestCase):
    fixtures = ['demo']

    def test_home(self):
        resposta = self.client.get(reverse('home'))
        self.assertContains(resposta, "Outubro é mês missionário")
        self.assertContains(resposta, "IAM Pequenos Missionários · Fortaleza/CE")

    def test_lista_de_edicoes(self):
        resposta = self.client.get(reverse('edicoes'))
        self.assertContains(resposta, "Nº 3 · Outubro, mês missionário")
        self.assertContains(resposta, "Edição completa em breve")

    def test_edicao_com_link_externo(self):
        resposta = self.client.get(reverse('edicao', args=[1]))
        self.assertContains(resposta, 'href="https://iam.pom.org.br/"')
        self.assertNotContains(resposta, "<iframe")

    def test_edicao_do_drive_aparece_dentro_do_site(self):
        Edicao.objects.filter(pk=2).update(link="https://drive.google.com/file/d/XYZ123/view")
        resposta = self.client.get(reverse('edicao', args=[2]))
        self.assertContains(resposta, 'src="https://drive.google.com/file/d/XYZ123/preview"')

    def test_sobre(self):
        resposta = self.client.get(reverse('sobre'))
        self.assertContains(resposta, "Minha caminhada na IAM")
        self.assertContains(resposta, 'id="contato"')
        self.assertContains(resposta, 'aria-current="page">Sobre')
        self.assertNotContains(resposta, "Trocar por")  # dicas das fotos não vão para o HTML

    def test_edicao_inexistente(self):
        self.assertEqual(self.client.get(reverse('edicao', args=[999])).status_code, 404)


class RestricaoPorGrupoTests(TestCase):
    fixtures = ['demo']

    def setUp(self):
        from django.contrib.auth.models import Group, User
        # Coordena só o grupo 1 (Sementes da Missão, Belo Horizonte)
        self.coordenador = User.objects.create_user('coord', password='x', is_staff=True)
        self.coordenador.groups.add(Group.objects.get(name='Coordenadores'))
        Grupo.objects.get(pk=1).coordenadores.add(self.coordenador)
        self.client.force_login(self.coordenador)

    def test_ve_so_as_fotos_do_proprio_grupo(self):
        resposta = self.client.get(reverse('admin:core_outros_grupos_changelist'))
        self.assertContains(resposta, "jornada diocesana")       # foto do grupo 1
        self.assertNotContains(resposta, "Oficina de cartazes")  # foto do grupo 2

    def test_ve_so_as_edicoes_do_proprio_grupo(self):
        resposta = self.client.get(reverse('admin:core_edicao_changelist'))
        self.assertContains(resposta, "Encontro de setembro")          # edição do grupo 1
        self.assertNotContains(resposta, "Outubro, mês missionário")   # edição geral

    def test_nao_abre_conteudo_de_outro_grupo(self):
        resposta = self.client.get(reverse('admin:core_outros_grupos_change', args=[1]))  # foto do grupo 2
        self.assertRedirects(resposta, reverse('admin:index'))

    def test_so_pode_publicar_no_proprio_grupo(self):
        dados = {'titulo': 'Teste', 'descricao': 'x', 'imagem': 'https://exemplo.com/capa.png',
                 'link': '', 'publicado_em_0': '01/10/2026', 'publicado_em_1': '10:00:00'}
        url = reverse('admin:core_edicao_add')
        self.client.post(url, {**dados, 'grupo': 2})   # grupo dos outros
        self.client.post(url, dados)                   # sem grupo (edição geral)
        self.assertFalse(Edicao.objects.filter(titulo='Teste').exists())
        self.client.post(url, {**dados, 'grupo': 1})   # o próprio grupo
        self.assertEqual(Edicao.objects.get(titulo='Teste').grupo_id, 1)

    def test_nao_mexe_nos_destaques_nem_nos_usuarios(self):
        self.assertEqual(self.client.get(reverse('admin:core_destaques_changelist')).status_code, 403)
        self.assertEqual(self.client.get(reverse('admin:auth_user_changelist')).status_code, 403)

    def test_superusuario_ve_tudo(self):
        from django.contrib.auth.models import User
        self.client.force_login(User.objects.create_superuser('chefe', password='x'))
        resposta = self.client.get(reverse('admin:core_outros_grupos_changelist'))
        self.assertContains(resposta, "jornada diocesana")
        self.assertContains(resposta, "Oficina de cartazes")


def foto_de_celular(largura=4000, altura=3000):
    """JPEG grande, com metadados e marcado como 'tirado com o celular deitado' (orientação 6)."""
    exif = Image.Exif()
    exif[0x010F] = "Fabricante do celular"
    exif[0x0112] = 6
    arquivo = BytesIO()
    Image.new('RGB', (largura, altura), 'orange').save(arquivo, 'JPEG', exif=exif)
    return SimpleUploadedFile('IMG_0001.jpeg', arquivo.getvalue(), content_type='image/jpeg')


class EnvioDeFotosTests(TestCase):
    fixtures = ['demo']

    def setUp(self):
        self.pasta_media = tempfile.mkdtemp()
        configuracao = override_settings(MEDIA_ROOT=self.pasta_media)
        configuracao.enable()
        self.addCleanup(configuracao.disable)
        self.addCleanup(shutil.rmtree, self.pasta_media, ignore_errors=True)

        from django.contrib.auth.models import Group, User
        coordenador = User.objects.create_user('coord', password='x', is_staff=True)
        coordenador.groups.add(Group.objects.get(name='Coordenadores'))
        Grupo.objects.get(pk=1).coordenadores.add(coordenador)
        self.client.force_login(coordenador)

    def enviar(self, **extra):
        dados = {'grupo': 1, 'foto': foto_de_celular(), 'imagem': '', 'descricao': 'Encontro', 'data': '',
                 'ordem': 0, **extra}
        return self.client.post(reverse('admin:core_outros_grupos_add'), dados)

    def test_foto_enviada_e_reduzida_girada_e_sem_metadados(self):
        self.enviar()
        foto = Outros_grupos.objects.get(descricao='Encontro')
        with Image.open(foto.foto.path) as imagem:
            self.assertEqual(imagem.format, 'JPEG')
            self.assertEqual(imagem.size, (1200, 1600))  # deitada 4000x3000 -> em pé, máx. 1600
            self.assertEqual(len(imagem.getexif()), 0)
        self.assertEqual(foto.url_da_imagem, foto.foto.url)
        self.assertTrue(foto.foto.name.startswith('fotos/'))

    def test_trocar_a_foto_apaga_o_arquivo_antigo(self):
        self.enviar()
        foto = Outros_grupos.objects.get(descricao='Encontro')
        caminho_antigo = foto.foto.path
        foto.foto = foto_de_celular(800, 600)
        foto.save()
        self.assertFalse(Path(caminho_antigo).exists())
        self.assertTrue(Path(foto.foto.path).exists())

    def test_apagar_o_registro_apaga_o_arquivo(self):
        self.enviar()
        foto = Outros_grupos.objects.get(descricao='Encontro')
        caminho = foto.foto.path
        foto.delete()
        self.assertFalse(Path(caminho).exists())

    def test_precisa_de_foto_ou_link(self):
        self.enviar(foto='')
        self.assertFalse(Outros_grupos.objects.filter(descricao='Encontro').exists())
        with self.assertRaises(ValidationError):
            Outros_grupos(descricao='x').full_clean()

    def test_link_continua_funcionando(self):
        foto = Outros_grupos.objects.get(pk=1)
        self.assertFalse(foto.foto)
        self.assertTrue(foto.url_da_imagem.startswith('https://'))
