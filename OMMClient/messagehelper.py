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
    child_num = 0
    while child is not None and child_num < 5000:
        child_num +=1
        childname = child.tagName
        children[childname] = {}
        for i in range(0, child.attributes.length):
            item = child.attributes.item(i)
            children[childname][item.name] = item.value
        child = child.nextSibling
    return name, attributes, children


def construct_message(name, attributes=None, children=None):
    if attributes is None:
        attributes = {}
    impl = getDOMImplementation()
    message = impl.createDocument(None, name, None)
    root_element = message.documentElement
    for key, val in attributes.items():
        root_element.setAttribute(str(key), str(val))
    if children is not None:
        for key, val in children.items():
            new_child = message.createElement(key)
            if val is not None:
                for attr_key, attr_val in val.items():
                    new_child.setAttribute(str(attr_key), str(attr_val))
            root_element.appendChild(new_child)
    print root_element.toxml()
    return root_element.toxml()
