# Jornal da IAM

Jornal comunitário online para grupos da **Infância e Adolescência Missionária (IAM)**.
Cada grupo pode publicar suas edições do jornal, mostrar destaques das atividades e compartilhar
fotos no mural "Outros Grupos". Tudo é gerenciado pelo painel administrativo do Django, sem
precisar saber programar.

## Como rodar localmente

Requisitos: Python 3.12 ou mais recente.

```powershell
cd "jornal da iam/back-end/jornal_iam"

python -m venv venv
venv\Scripts\activate            # no Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

Set-Content .env "DEBUG=True" -Encoding ascii   # no Linux/macOS: echo "DEBUG=True" > .env

python manage.py migrate
python manage.py loaddata demo   # grupos, edições, destaques e fotos de exemplo
python manage.py createsuperuser # cria seu login do painel
python manage.py runserver
```

- Site: http://127.0.0.1:8000/
- Painel administrativo: http://127.0.0.1:8000/admin/

O arquivo `.env` (ao lado do `manage.py`, fora do git) guarda as configurações de cada máquina;
o modelo comentado está em `.env.exemplo`. No seu computador basta `DEBUG=True`. Sem ele, o site
exige uma `SECRET_KEY` de verdade e se recusa a subir.

Para rodar os testes: `python manage.py test core`

## Como o conteúdo é organizado

| No painel        | O que é                                                                                   |
|------------------|-------------------------------------------------------------------------------------------|
| **Grupos da IAM** | Os grupos da IAM que usam a plataforma (nome, paróquia, cidade).                          |
| **Edições**      | As edições do jornal. Sem grupo, a edição é considerada geral da plataforma.              |
| **Destaques**    | O carrossel da página inicial. Pode apontar para a edição que conta a atividade.          |
| **Fotos de outros grupos** | O mural de fotos da página inicial, com o grupo e a data de cada atividade.     |

### Imagens

Cada imagem (foto do mural, capa de edição, destaque) pode ser **enviada pelo painel** ou vir de um
**link**. As enviadas são tratadas automaticamente:

- reduzidas para no máximo 1600 px e salvas em JPEG (uma foto de celular de ~4 MB fica com algumas
  centenas de KB);
- giradas na posição certa;
- **sem os metadados da foto original, incluindo a localização GPS**;
- apagadas do disco quando são trocadas ou quando o item é excluído.

Os arquivos ficam na pasta `media/` (fora do git). Em produção, o servidor precisa entregar essa pasta
no endereço `/media/` (no PythonAnywhere: aba *Web* → *Static files*, URL `/media/` apontando para a
pasta `media`). Inclua essa pasta nos backups junto com o banco.

### Publicando uma edição pelo Google Drive

1. Envie o PDF da edição para o Google Drive da conta do projeto.
2. Em **Compartilhar**, deixe como "Qualquer pessoa com o link".
3. Copie o link (algo como `https://drive.google.com/file/d/.../view`) e cole no campo **link** da edição.

O site reconhece links do Drive e mostra o PDF dentro da página da edição. Links de outros sites
(Canva, Issuu...) aparecem como um botão "Ler a edição completa".

> **Fotos de crianças:** só publique imagens com autorização dos pais ou responsáveis (ECA e LGPD).

### Cadastrando um coordenador

1. Em **Usuários**, crie o usuário. Marque **Membro da equipe** e coloque-o no grupo de permissões
   **Coordenadores** (já vem criado).
2. Em **Grupos da IAM**, abra o grupo e adicione a pessoa em **Coordenadores**.

O coordenador só vê e edita as edições e fotos dos grupos que coordena, e só publica nesses grupos.
Ele também não apaga edições (só fotos). Destaques da página inicial, edições gerais (sem grupo) e
usuários ficam com os superusuários.

Atenção aos nomes: **Grupos** (em *Autenticação e Autorização*) são pacotes de permissões do Django;
**Grupos da IAM** são os grupos que publicam no jornal.

## Estrutura

```
jornal da iam/
├── back-end/jornal_iam/      projeto Django (é o site de verdade)
│   ├── core/                 app principal: models, views, templates, fixtures e testes
│   ├── jornal_iam/           configurações (settings.py, urls.py)
│   └── static/               JavaScript e imagens
└── arquivo/front-end-prototipo/   protótipo inicial em HTML puro, mantido só como registro
```

## Publicando no PythonAnywhere

Os caminhos abaixo usam `seunome` como nome de usuário: troque pelo seu. Os nomes de menus e as
versões de Python disponíveis podem mudar com o tempo; use a versão mais nova oferecida (3.10 ou
superior).

### 1. Código e dependências

Abra um **Bash console** (aba *Consoles*) e rode:

```bash
git clone https://github.com/Vt-L4b/iam.git
cd ~/iam/"jornal da iam"/back-end/jornal_iam

mkvirtualenv --python=python3.13 jornal   # cria e ativa o ambiente "jornal"
pip install -r requirements.txt
```

### 2. Configuração (`.env`)

```bash
cp .env.exemplo .env
python -c "import secrets; print(secrets.token_urlsafe(50))"   # copie a chave gerada
nano .env
```

Preencha `SECRET_KEY` com a chave gerada e `ALLOWED_HOSTS=seunome.pythonanywhere.com`. Deixe
`DEBUG=False`. Salve com `Ctrl+O`, `Enter`, `Ctrl+X`.

### 3. Banco e arquivos estáticos

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Não rode `loaddata demo` no servidor: os dados de exemplo são só para testar no computador.

### 4. Aplicativo web

Na aba **Web**: *Add a new web app* → *Manual configuration* (não escolha a opção "Django") →
mesma versão de Python do ambiente. Depois, na página do app:

- **Virtualenv**: `/home/seunome/.virtualenvs/jornal`
- **Source code**: `/home/seunome/iam/jornal da iam/back-end/jornal_iam`
- **WSGI configuration file**: clique no link, apague todo o conteúdo e coloque:

  ```python
  import os
  import sys

  caminho = '/home/seunome/iam/jornal da iam/back-end/jornal_iam'
  if caminho not in sys.path:
      sys.path.insert(0, caminho)

  os.environ['DJANGO_SETTINGS_MODULE'] = 'jornal_iam.settings'

  from django.core.wsgi import get_wsgi_application
  application = get_wsgi_application()
  ```

- **Static files**: adicione duas linhas (repare que as pastas ficam em `back-end`, um nível
  acima do `manage.py`):

  | URL        | Directory                                            |
  |------------|------------------------------------------------------|
  | `/static/` | `/home/seunome/iam/jornal da iam/back-end/staticfiles` |
  | `/media/`  | `/home/seunome/iam/jornal da iam/back-end/media`       |

- **Security**: ative **Force HTTPS**.

Clique em **Reload** e abra `https://seunome.pythonanywhere.com`. Se algo der errado, o motivo
aparece no **Error log**, no fim da aba Web.

### Atualizando o site depois de mudanças no código

```bash
workon jornal
cd ~/iam/"jornal da iam"/back-end/jornal_iam
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

E clique em **Reload** na aba Web.

### Backup

Tudo o que não está no git fica em dois lugares: o banco (`back-end/db.sqlite3`) e as fotos
enviadas (`back-end/media/`). Para gerar um arquivo único e baixá-lo pela aba *Files*:

```bash
cd ~/iam/"jornal da iam"/back-end
zip -r ~/backup-$(date +%F).zip db.sqlite3 media
```

Faça isso pelo menos a cada edição publicada.

### Lembretes do plano gratuito

- O app precisa ser renovado de tempos em tempos (botão na aba Web); a PythonAnywhere avisa
  por e-mail antes de desligá-lo.
- O espaço em disco é limitado: as dependências ocupam cerca de 70 MB, e as fotos enviadas são
  reduzidas automaticamente para economizar o resto.
