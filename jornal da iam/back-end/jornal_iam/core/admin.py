from django.contrib import admin
from django.utils.html import format_html

from .models import Grupo, Edicao, Destaques, Outros_grupos


def grupos_do_usuario(request):
    return Grupo.objects.filter(coordenadores=request.user)


class RestritoAoGrupoAdmin(admin.ModelAdmin):
    """Coordenadores só veem e editam o conteúdo dos grupos que coordenam.
    Superusuários continuam vendo tudo, inclusive o que não tem grupo (conteúdo geral)."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(grupo__in=grupos_do_usuario(request))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'grupo' and not request.user.is_superuser:
            kwargs['queryset'] = grupos_do_usuario(request)
            kwargs['required'] = True  # conteúdo geral (sem grupo) é só para superusuários
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_list_filter(self, request):
        filtros = super().get_list_filter(request)
        if request.user.is_superuser:
            return filtros
        return [f for f in filtros if f != 'grupo']


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'paroquia', 'cidade', 'uf']
    search_fields = ['nome', 'paroquia', 'cidade']
    prepopulated_fields = {'slug': ['nome']}
    filter_horizontal = ['coordenadores']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(coordenadores=request.user)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        # Coordenador pode atualizar os dados do grupo, mas não o endereço nem quem coordena
        return ['slug', 'coordenadores']

    def get_prepopulated_fields(self, request, obj=None):
        return self.prepopulated_fields if request.user.is_superuser else {}


@admin.register(Edicao)
class EdicaoAdmin(RestritoAoGrupoAdmin):
    list_display = ['titulo', 'numero', 'grupo', 'publicado_em']
    search_fields = ['titulo']
    list_filter = ['grupo', 'publicado_em']


@admin.register(Destaques)
class DestaquesAdmin(admin.ModelAdmin):
    # O carrossel da página inicial é da plataforma toda: fica com os superusuários
    list_display = ['id', 'titulo', 'edicao', 'ordem']
    ordering = ['ordem']


@admin.register(Outros_grupos)
class Outros_gruposAdmin(RestritoAoGrupoAdmin):
    list_display = ['miniatura', 'grupo', 'descricao', 'data', 'ordem']
    list_filter = ['grupo']
    ordering = ['ordem']

    @admin.display(description="foto")
    def miniatura(self, obj):
        return format_html('<img src="{}" style="height:48px;border-radius:4px">', obj.url_da_imagem)
