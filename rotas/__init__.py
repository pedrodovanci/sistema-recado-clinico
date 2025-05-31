# Importa os blueprints
from .comuns import comuns_routes
from .responsavel import responsavel_routes
from .admin import admin_routes

__all__ = ['comuns_routes', 'responsavel_routes', 'admin_routes']