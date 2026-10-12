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

python manage.py migrate
python manage.py loaddata demo   # grupos, edições, destaques e fotos de exemplo
python manage.py createsuperuser # cria seu login do painel

$env:DEBUG="True"                # no Linux/macOS: export DEBUG=True
python manage.py runserver
```

- Site: http://127.0.0.1:8000/
- Painel administrativo: http://127.0.0.1:8000/admin/

`DEBUG=True` é necessário para o servidor de desenvolvimento entregar o CSS, o JavaScript e o logo.
Em produção ele fica desligado (é o padrão quando a variável não existe).

Para rodar os testes: `python manage.py test core`

## Como o conteúdo é organizado

| No painel        | O que é                                                                                   |
|------------------|-------------------------------------------------------------------------------------------|
| **Grupos da IAM** | Os grupos da IAM que usam a plataforma (nome, paróquia, cidade).                          |
| **Edições**      | As edições do jornal. Sem grupo, a edição é considerada geral da plataforma.              |
| **Destaques**    | O carrossel da página inicial. Pode apontar para a edição que conta a atividade.          |
| **Fotos de outros grupos** | O mural de fotos da página inicial, com o grupo e a data de cada atividade.     |

As imagens são cadastradas por link (URL), então não ocupam espaço no servidor.

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
