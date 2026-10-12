from django.contrib.auth.management import create_permissions
from django.db import migrations

# O que cada coordenador pode fazer no painel. A restrição ao próprio grupo fica no admin.py.
PERMISSOES = [
    'view_grupo', 'change_grupo',
    'view_edicao', 'add_edicao', 'change_edicao',
    # Fotos podem ser apagadas, por exemplo se uma família retirar a autorização de imagem
    'view_outros_grupos', 'add_outros_grupos', 'change_outros_grupos', 'delete_outros_grupos',
]


def criar_coordenadores(apps, schema_editor):
    # Num banco novo as permissões só seriam criadas no fim do migrate; criamos agora
    app_config = apps.get_app_config('core')
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)
    app_config.models_module = None

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    grupo, _ = Group.objects.get_or_create(name='Coordenadores')
    grupo.permissions.set(Permission.objects.filter(content_type__app_label='core', codename__in=PERMISSOES))


def remover_coordenadores(apps, schema_editor):
    apps.get_model('auth', 'Group').objects.filter(name='Coordenadores').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('core', '0008_coordenadores_dos_grupos'),
    ]

    operations = [
        migrations.RunPython(criar_coordenadores, remover_coordenadores),
    ]
