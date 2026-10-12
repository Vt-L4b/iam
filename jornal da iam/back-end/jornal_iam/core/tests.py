from django.test import TestCase
from django.urls import reverse

from .models import Edicao, Grupo


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
