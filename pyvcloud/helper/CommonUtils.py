from StringIO import StringIO


def convertPythonObjToStr(
        obj,
        name,
        namespace='',
        namespacedef='',
        pretty_print=False):
    result = StringIO()
    obj.export(
        result,
        0,
        name_=name,
        namespace_=namespace,
        namespacedef_=namespacedef,
        pretty_print=pretty_print)
    return result.getvalue()
