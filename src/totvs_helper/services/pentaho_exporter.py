"""Compatibility shim — use totvs_helper.services.pentaho."""

from totvs_helper.services.pentaho.exporter import PentahoExporter, PentahoExportResult

__all__ = ["PentahoExporter", "PentahoExportResult"]
