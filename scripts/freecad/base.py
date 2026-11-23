"""Utilidades base para modelar muebles con FreeCAD sin interfaz (freecadcmd).
Pendiente de probar contra la versión de FreeCAD que confirme el usuario."""
import FreeCAD as App
import Part


def nuevo_documento(nombre):
    doc = App.newDocument(nombre)
    hoja = doc.addObject("Spreadsheet::Sheet", "Parametros")
    return doc, hoja


def tablero(doc, codigo, largo, ancho, grosor, pos=(0, 0, 0), material=""):
    """Pieza rectangular (tablero/listón). Medidas en unidades del documento (mm)."""
    obj = doc.addObject("Part::Feature", codigo)
    obj.Label = codigo
    obj.Shape = Part.makeBox(largo, ancho, grosor, App.Vector(*pos))
    for prop, val in (("Material", material), ("Grosor", str(grosor))):
        obj.addProperty("App::PropertyString", prop, "Mueble")
        setattr(obj, prop, val)
    return obj


def tubo(doc, codigo, longitud, d_ext, d_int, pos=(0, 0, 0), direccion=(0, 0, 1), material="PVC"):
    """Tramo de tubo circular hueco."""
    base, dir_ = App.Vector(*pos), App.Vector(*direccion)
    ext = Part.makeCylinder(d_ext / 2, longitud, base, dir_)
    inn = Part.makeCylinder(d_int / 2, longitud, base, dir_)
    obj = doc.addObject("Part::Feature", codigo)
    obj.Label = codigo
    obj.Shape = ext.cut(inn)
    obj.addProperty("App::PropertyString", "Material", "Mueble")
    obj.Material = material
    return obj


def guardar_y_exportar(doc, ruta_fcstd, ruta_step=None):
    doc.recompute()
    doc.saveAs(ruta_fcstd)
    if ruta_step:
        import Import
        Import.export([o for o in doc.Objects if hasattr(o, "Shape")], ruta_step)
