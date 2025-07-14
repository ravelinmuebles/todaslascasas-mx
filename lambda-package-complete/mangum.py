"""Shim para exponer paquete mangum cuando está dentro de lambda_build.
Permite importar `mangum` de forma transparente sin modificar sys.path."""
from importlib import import_module as _import_module
globals().update(_import_module('lambda_build.mangum').__dict__) 