import xml.etree.ElementTree as ET
try:
    tree = ET.parse('test.xml')
    for node in tree.iter('node'):
        text = node.attrib.get('text', '').lower()
        desc = node.attrib.get('content-desc', '').lower()
        if 'anirudh' in text or 'anirudh' in desc or 'meta' in text or 'meta' in desc:
            print(f"[{node.attrib.get('class')}] Text: '{text}' | Desc: '{desc}' | bounds: {node.attrib.get('bounds')}")
except Exception as e:
    print(e)
