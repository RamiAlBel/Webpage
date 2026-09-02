"""Read/patch/write the Claude Design bundle in index.html."""
import re, json

TAGS = ['__bundler/manifest', '__bundler/ext_resources',
        '__bundler/page_order', '__bundler/template']

def _span(s, tag):
    m = re.search(r'(<script type="%s"[^>]*>)(.*?)(</script>)' % re.escape(tag), s, re.S)
    if not m:
        raise KeyError(tag)
    return m

def load(path):
    s = open(path, encoding='utf-8').read()
    out = {'_raw': s}
    for t in TAGS:
        out[t] = json.loads(_span(s, t).group(2))
    return out

def save(path, bundle):
    s = bundle['_raw']
    for t in TAGS:
        m = _span(s, t)
        body = json.dumps(bundle[t], ensure_ascii=False)
        # A literal </script> inside a payload would close the host <script>
        # tag. JSON allows \/ so escape every slash after a '<'.
        body = body.replace('</', '<\\/')
        s = s[:m.start(2)] + body + s[m.end(2):]
    open(path, 'w', encoding='utf-8').write(s)
