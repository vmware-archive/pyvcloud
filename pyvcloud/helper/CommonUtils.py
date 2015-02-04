from StringIO import StringIO

def convertPythonObjToStr(obj, name, namespace = '', namespacedef= ''):
    result = StringIO()
    obj.export(result, 0, name_ = name, namespace_ = namespace, namespacedef_ = namespacedef ,pretty_print=False)
    return result.getvalue()
