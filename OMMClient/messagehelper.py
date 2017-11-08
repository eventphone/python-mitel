from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parseString


def parse_message(messagedata):
    xml_data = parseString(messagedata.rstrip(chr(0)))
    root = xml_data.documentElement
    name = root.tagName
    attributes = {}
    children = {}
    for i in range(0, root.attributes.length):
        item = root.attributes.item(i)
        attributes[item.name] = item.value
    child = root.firstChild
    while child is not None:
        childname = child.tagName
        children[childname] = {}
        for i in range(0, child.attributes.length):
            item = child.attributes.item(i)
            children[childname][item.name] = item.value
        child = child.nextSibling
    return name, attributes, children


def construct_single_message(name, attributes):
    impl = getDOMImplementation()
    message = impl.createDocument(None, name, None)
    root_element = message.documentElement
    for key, val in attributes.items():
        root_element.setAttribute(key, val)
    return root_element.toxml()
