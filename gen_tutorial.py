#!/usr/bin/env python3
"""Generates omnist-web/tutorial/*.html from one shared template + this
file's STEPS list. Single source of truth for the nav/header/footer chrome
-- edit here, regenerate, never hand-edit the generated files directly."""
import html
import os

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tutorial")

SITE = "https://omnist.dev"

def code(text, lang="python"):
    return f'<pre class="code"><code>{html.escape(text)}</code></pre>'

def output(text):
    return f'<div class="output-label">Output</div><pre class="output"><code>{html.escape(text)}</code></pre>'

def p(text):
    return f"<p>{text}</p>"

def learn_more(*links):
    items = "".join(f'<li><a href="{href}">{label}</a></li>' for label, href in links)
    return f'<div class="learn-more"><h3>Learn more</h3><ul>{items}</ul></div>'

# Each step: (slug, title, short description for the index, body_html)
STEPS = []

def step(slug, title, description, body):
    STEPS.append({"slug": slug, "title": title, "description": description, "body": body})

# ---------------------------------------------------------------------------

step("00-why-omnist", "Why Omnist", "The problem this exists to solve, and what it makes possible.", "".join([
    p("JSON, YAML, TOML, and XML all encode the same kind of tree-shaped data — but each ships its own parser, its own types, and its own edge cases. There's no shared model underneath, so converting between them, validating one against a shared shape, or safely evolving that shape over time all end up hand-rolled and unchecked."),
    p("Omnist exists to close three gaps specifically:"),
    '<ul class="bullets"><li><b>One model, many formats.</b> Read JSON, YAML, TOML, XML, or Omnist\'s own OML into the same tree, validate it against one schema, write it back out to any of the others — a genuine <i>read one, write another</i>, not a lossy best-effort conversion.</li>'
    '<li><b>Schema evolution you can prove, not guess at.</b> "Will every document written under the old schema still validate under the new one?" is a question <code>compatible_with</code> answers with a proven yes or no — the kind of check a CI gate runs before a schema change merges, not something a reviewer eyeballs.</li>'
    '<li><b>Operations that work on the whole schema, not one document at a time.</b> Trimming a schema down to what one service actually uses, or drafting one from real examples instead of writing it by hand, are both single decidable operations here — <code>extract</code> and <code>infer</code> — not scripts you'
    "'"
    'd have to write yourself.</li></ul>',
    p("The reason all of this is <i>decidable</i> — provably correct, not a heuristic that mostly works — is a deliberate constraint: records are closed by default, and scalar types are never composed into enums or unions. The one deliberate opening is an explicitly marked <code>any</code>. That discipline is what the rest of this tutorial actually demonstrates, one operation at a time."),
    p("This tutorial uses <b>Python</b> — one of five independent language ports, all built against the same <a href=\"https://spec.omnist.dev\">specification</a>. Everything from here on exists the same way in the other four; only the surface syntax changes."),
    learn_more(
        ("omnist.dev/presentation.html — the introduction slides", "https://omnist.dev/presentation.html"),
        ("spec.omnist.dev — the specification", "https://spec.omnist.dev"),
    ),
]))

step("01-setup", "Setup", "Install the Python port and import what you need.", "".join([
    p("This tutorial uses <b>Python</b> — one of five independent language ports of Omnist, all built against the same <a href=\"https://spec.omnist.dev\">specification</a>. Everything here — the Document model, the schema algebra, the operations — exists the same way in the other four; only the surface syntax changes."),
    p("Install the package:"),
    code("pip install omnist          # core + JSON\npip install omnist[all]     # + pyyaml, tomli_w, defusedxml", "bash"),
    p("Then import what you need as you go — this tutorial imports a few new names in each step, shown at the top of that step's first example."),
    learn_more(
        ("py.omnist.dev — full Python docs", "https://py.omnist.dev"),
        ("spec.omnist.dev — the language-agnostic specification", "https://spec.omnist.dev"),
    ),
]))

step("02-documents", "The Document model", "Build, navigate, and mutate a Document — the one tree every format reads into.", "".join([
    p("A <b>Document</b> is a tree: an ordered list of labeled edges. There is no separate array type — a label that repeats <i>is</i> the array. This one idea is why JSON, YAML, TOML, XML, and Omnist's own OML format can all be read into (and written back out from) the exact same structure."),
    p("<code>doc(value)</code> builds a Document from plain Python — a dict becomes an edge list, and a key whose value is a list expands into one edge per item:"),
    code('from omnist import doc\n\nd = doc({"name": "Ann", "tag": ["x", "y"]})\nd.labels()                 # every distinct label present\nd.count("tag")             # how many edges share this label\nd.get_one("name").value    # the single edge under a non-repeated label\n[t.value for t in d.get("tag")]   # every value under a repeated label\nd.to_data()                # the raw edge list\nd.to_grouped()             # JSON-shaped: repeated labels become a list'),
    output("labels: ['name', 'tag']\ncount tag: 2\nget_one name value: Ann\nget tag values: ['x', 'y']\nto_data: [('name', 'Ann'), ('tag', 'x'), ('tag', 'y')]\nto_grouped: {'name': 'Ann', 'tag': ['x', 'y']}"),
    p("A Document is mutated through a guarded API — <code>add</code> is how an array grows, <code>set</code> replaces every edge under a label with one, and <code>remove</code> drops a label entirely:"),
    code('d.add("tag", "z")           # append an edge -- the array grows\nd.set("name", "Bob")        # replace every \'name\' edge with one\nd.remove("tag")             # drop every \'tag\' edge'),
    output("after add:    {'name': 'Ann', 'tag': ['x', 'y', 'z']}\nafter set:    {'name': 'Bob', 'tag': ['x', 'y', 'z']}\nafter remove: {'name': 'Bob'}"),
    learn_more(
        ("spec.omnist.dev — §2 The Document model", "https://spec.omnist.dev/02-document-model/"),
        ("py.omnist.dev — Documents", "https://py.omnist.dev/guide/#documents"),
    ),
]))

step("03-oml", "OML — the native format", "Omnist's own text syntax for the Document model.", "".join([
    p("<b>OML</b> (Omnist Markup Language) is the native, human-readable syntax for a Document — the same tree every other format reads into, written in Omnist's own grammar instead of borrowing JSON's, YAML's, or XML's."),
    code('from omnist import write_oml\n\nnode = [("name", "Ada"), ("tags", [("tag", "x"), ("tag", "y")])]\nwrite_oml(node, indent=None)   # compact, single-line layout\nwrite_oml(node)                # indented, multi-line layout (the default)'),
    output('compact:   name: "Ada"; tags: { tag: "x"; tag: "y" }\nindented:\nname: "Ada"\ntags: {\n  tag: "x"\n  tag: "y"\n}'),
    p("Both layouts round-trip through the reader to the identical Document — <code>indent</code> only changes formatting, never meaning. The compact form is handy for log lines or diffless storage; the indented form is what you'd hand-author."),
    learn_more(
        ("spec.omnist.dev — §4 OML grammar", "https://spec.omnist.dev/04-oml-grammar/"),
        ("py.omnist.dev — OML", "https://py.omnist.dev/guide/#oml-the-native-format"),
    ),
]))

step("04-osd", "OSD — schema syntax", "Named records, cardinality, and the three kinds of field a schema can declare.", "".join([
    p("<b>OSD</b> (Omnist Schema Definition) describes a schema as named <b>records</b> — each a closed set of fields, every field with a declared <b>cardinality</b> (how many times its label may occur) and a <b>type</b>: a scalar, a reference to another record, or the explicit escape hatch <code>any</code>."),
    code('record Address {\n    "street": string,\n    "city": string,\n}\nrecord User {\n    "name": string,\n    "emails" [1,]: string,     # one or more -- cardinality [min,]\n    "address": Address,        # a reference to another record\n    "note": string?,           # nullable scalar\n}\nroot User', "osd"),
    p("Cardinality shorthand: field with no bracket means exactly one (<code>[1,1]</code>); <code>[0,1]</code> is optional; <code>[0,]</code> is zero-or-more (an array that may be empty); <code>[1,]</code> is one-or-more. <code>?</code> makes a <i>scalar</i> nullable — a separate question from cardinality entirely (a field can be optional, nullable, both, or neither)."),
    p("Records are <b>closed by default</b> — a document with a field the record doesn't declare is invalid. The one deliberate opening is <code>any</code>, which accepts anything and stops all further checking beneath it."),
    learn_more(
        ("spec.omnist.dev — §5 OSD grammar", "https://spec.omnist.dev/05-osd-grammar/"),
        ("py.omnist.dev — Schemas: OSD", "https://py.omnist.dev/guide/#schemas-osd"),
    ),
]))

step("05-schema-builder", "Building and reading a schema in Python", "Construct a Schema from Python instead of OSD text — and inspect one already in hand.", "".join([
    p("The same schema can be built from Python instead of parsed from OSD text — useful when a schema is generated programmatically rather than hand-written:"),
    code('from omnist import schema, record, field, ref, nullable, t\n\naddress = record(field("street", t.string),\n                 field("city",   t.string))\nuser = record(\n    field("name",    t.string),\n    field("emails",  t.string, min=1, max=None),   # [1,]\n    field("address", ref("Address")),\n    field("note",    nullable(t.string)),          # nullable scalar\n)\ns = schema(ref("User"), User=user, Address=address)\nprint(s.to_osd())'),
    output('record User {\n    "name": string,\n    "emails" [1,]: string,\n    "address": Address,\n    "note": string?,\n}\nrecord Address {\n    "street": string,\n    "city": string,\n}\nroot User'),
    p("A schema already in hand — whether built this way or parsed from OSD text — can be walked the same way at runtime: <code>.root</code> is the entry-point reference, <code>.env</code> is the full name→record map, and each <code>Record</code> exposes its <code>.fields</code>:"),
    code('print(s.root)\nprint(list(s.env.keys()))\nfor f in s.env["User"].fields:\n    print(f.label, f.type, f.min, f.max)'),
    output("ref(User)\n['Address', 'User']\nname string 1 1\naddress ref(Address) 1 1"),
    p("This is how you'd introspect a schema at runtime — answering \"what fields does this record declare, and what are their types and cardinalities?\" — without re-parsing or guessing from the OSD text."),
    learn_more(
        ("spec.omnist.dev — §3 The Schema model", "https://spec.omnist.dev/03-schema-model/"),
        ("py.omnist.dev — Schemas: the Python builder", "https://py.omnist.dev/schema/#the-python-builder"),
    ),
]))

step("06-validation", "Validation", "Check whether a Document conforms to a Schema, and read the real diagnostics.", "".join([
    p("<code>schema.validate(doc)</code> returns a <code>ValidationResult</code> with <code>.ok</code> and <code>.errors</code> — validation ignores edge order entirely, since a schema describes a set of possible documents, not a sequence."),
    code('from omnist import parse_schema, doc\n\ns = parse_schema(\'record R { "items" [1,]: integer }\\nroot R\')\nr = s.validate(doc({"items": []}))\nr.ok\nprint(r)'),
    output("ok: False\ninvalid:\n  at $: field 'items' occurs 0 time(s), expected at least 1"),
    p("Each <code>Error</code> carries a <code>.path</code>, a human-readable <code>.message</code>, and a stable, machine-readable <code>.code</code> (here, <code>validate.cardinality</code>) — the code is what you'd branch on in real code; the message is for a human reading logs."),
    learn_more(
        ("spec.omnist.dev — §3.6 Validation", "https://spec.omnist.dev/03-schema-model/#36-validation"),
        ("py.omnist.dev — Validation", "https://py.omnist.dev/guide/#validation"),
    ),
]))

step("07-materialization", "Materialization", "Upgrade untyped leaves (a JSON string) to the type a schema declares.", "".join([
    p("Without a schema, a reader's leaves are exactly whatever the format's own native parser produces — JSON has no date type, so a date always comes back as a plain string. Pass <code>schema=</code> to a reader to <b>upgrade</b> leaves to match what the schema declares, whenever the conversion is value-exact:"),
    code('from omnist import parse_schema, Doc\n\ns = parse_schema(\'record R { "d": date }\\nroot R\')\nraw = Doc.from_json(\'{"d": "2024-01-01"}\')                 # no schema\nmat = Doc.from_json(\'{"d": "2024-01-01"}\', schema=s)      # schema-directed\ntype(raw.get_one("d").value), raw.get_one("d").value\ntype(mat.get_one("d").value), mat.get_one("d").value'),
    output("raw:          <class 'str'> 2024-01-01\nmaterialized: <class 'datetime.date'> 2024-01-01"),
    p("The Document's <i>shape</i> is unchanged either way — materialization only ever upgrades a leaf's type, in place, never restructures anything."),
    learn_more(
        ("spec.omnist.dev — §7 Codecs and deserialization", "https://spec.omnist.dev/07-codecs-and-deserialization/"),
        ("py.omnist.dev — Schema-directed deserialization", "https://py.omnist.dev/deserialization/"),
    ),
]))

step("08-other-formats", "Reading and writing JSON, YAML, TOML, XML", "The other four codecs — and what happens when a value doesn't fit.", "".join([
    p("<code>Doc.from_*</code> reads a format into a Document; <code>Doc.to_*</code> writes one back out. JSON, YAML, TOML, and XML all read into the exact same Document that OML does — converting between any of the five is just <i>read one, write another</i>:"),
    code('from omnist import Doc\n\nDoc.from_json(\'{"name": "Ann", "tags": ["x", "y"]}\').to_toml()\nDoc.from_yaml("name: Ann\\n").to_json()'),
    output('to_toml():\nname = "Ann"\ntags = [\n    "x",\n    "y",\n]\n\nto_json(): {"name": "Ann"}'),
    p("Writing is lenient by default — a value a format can't hold the way it was typed (JSON/XML have no native date type) gets adjusted, and the adjustment is <i>recorded</i>, not silently lost:"),
    code('from omnist import doc, WriteReport, WriteError\nimport datetime\n\nd = doc({"d": datetime.date(2024, 1, 1)})\nd.to_json()                          # stringified, still succeeds\n\nrep = WriteReport()\nd.to_json(report=rep)                # inspect what changed\n[(a.code, a.severity) for a in rep]\n\nd.to_json(strict=True)               # raises instead of adjusting'),
    output("to_json(): {\"d\": \"2024-01-01\"}\nreport: [('temporal.stringified', 'warning')]\nstrict raised WriteError: warning: $.d: temporal value written as an ISO-8601 string"),
    p("A value with <b>no legal representation at all</b> (TOML has no <code>null</code>, and there's no safe substitute) fails unconditionally instead of guessing — <code>check_json</code>/<code>check_yaml</code>/<code>check_toml</code>/<code>check_xml</code> (and the matching <code>Doc</code> methods) simulate a write and return the report without producing output, so you can ask \"would this be lossy?\" without writing anything:"),
    code("d.check_json()"),
    output("warning: $.d: temporal value written as an ISO-8601 string"),
    learn_more(
        ("spec.omnist.dev — §8.3.8 Format codec adjustments", "https://spec.omnist.dev/08-conformance-and-errors/#838-format-codec-adjustments"),
        ("py.omnist.dev — Reading & writing other formats", "https://py.omnist.dev/guide/#reading--writing-other-formats"),
    ),
]))

step("09-schema-algebra", "Schema algebra", "Six decidable operations over schemas — comparison, minimization, extraction.", "".join([
    p("Most schema tools check one document at a time. Omnist's algebra <b>compares two whole schemas</b> and proves the answer — decidable because a schema is a closed automaton, not a heuristic over examples."),

    p("<b>Why <code>compatible_with</code> matters:</b> you're about to ship a schema change. Will every document ever written under the old schema still validate against the new one? That's not a question you want a reviewer guessing at — it's exactly what a CI gate can prove before merging:"),
    code('v1 = parse_schema(\'record R { "host": string }\\nroot R\')\nv2 = parse_schema(\'record R { "host": string, "port" [0,1]: integer }\\nroot R\')\n\nv1.compatible_with(v2)     # can readers of v2 still read v1\'s documents?\nv2.compatible_with(v1)     # the reverse -- v1 has no \'port\' field to require'),
    output("v1.compatible_with(v2): True   -- adding an optional field is backward compatible\nv2.compatible_with(v1): False  -- v1 can't produce the 'port' field v2 might require"),

    p("<b>Why <code>equivalent</code> matters:</b> two schemas can describe the exact same set of documents while looking structurally nothing alike — different record names, different nesting, the same shape underneath. That happens constantly: two teams independently modeling the same data, or a refactor that reorganizes records without changing what they accept. <code>equivalent</code> answers \"did anything actually change?\" without a human eyeballing a diff:"),
    code('a = parse_schema(\'record Left  { "x": string, "y": integer }\\n\'\n                  \'record Right { "x": string, "y": integer }\\n\'\n                  \'record Root  { "a": Left, "b": Right }\\nroot Root\')\nb = parse_schema(\'record Pair { "x": string, "y": integer }\\n\'\n                  \'record Root { "a": Pair, "b": Pair }\\nroot Root\')\n\na.equivalent(b)'),
    output("True   -- Left and Right are two different names for the same shape;\n         a and b accept exactly the same documents"),

    p("<b>Why <code>normalize</code> matters:</b> the schema above (<code>a</code>) carries dead weight — <code>Left</code> and <code>Right</code> are two spellings of one record. That's easy to end up with after independent authoring, or after <code>infer</code> (next step) drafts one record per sample instead of noticing the repeat. <code>normalize</code> collapses it to the canonical minimal form — same documents accepted, fewer records to maintain:"),
    code("a.normalize()"),
    output('record Left {\n    "x": string,\n    "y": integer,\n}\nrecord Root {\n    "a": Left,\n    "b": Left,\n}\nroot Root'),

    p("<b>Why <code>extract</code> matters:</b> a shared schema often has more fields than any one consumer needs — a microservice reading only <code>host</code> shouldn't have to carry <code>port</code>'s validation rules too. <code>extract(*labels)</code> computes the minimal subschema recognizing only documents built from the kept labels, dropping anything the removal makes unreachable. Deleting a <i>mandatory</i> field is an error, not silently allowed:"),
    code('v2.extract("host")   # subschema with only "host" -- "port" dropped'),
    output('record R {\n    "host": string,\n}\nroot R'),

    p("<b>Why <code>is_empty</code>/<code>prune</code> matter:</b> a schema can accidentally describe <b>no documents at all</b> — a mandatory reference cycle with no base case, easy to introduce by typo in a large hand-written schema and very hard to spot by reading. <code>is_empty()</code> catches it before it ships; <code>prune()</code> strips never-emittable fields and unreachable records left over from other edits:"),
    code('empty = parse_schema(\'record A { "x": B }\\nrecord B { "y": A }\\nroot A\')\nempty.is_empty()\nempty.compatible_with(v1)   # vacuous: an empty schema accepts no documents'),
    output("is_empty: True\nempty.compatible_with(v1): True"),

    p("<b>Why <code>lint</code> matters:</b> a pre-flight check for a schema you're about to ship or one a tool generated — the same duplication <code>normalize</code> fixes, flagged first without changing anything, so a CI gate can require a human look at it:"),
    code('from omnist import lint\n\ndup = parse_schema(\'record A { "x": string }\\nrecord B { "x": string }\\n\'\n                    \'record Root { "a": A, "b": B }\\nroot Root\')\nfor finding in lint(dup):\n    print(finding)'),
    output("LintFinding(code='lint.duplicate-record', severity='warning', location='A, B',\n            message=\"records 'B' are structurally identical to 'A'; merge them with `schema normalize`\")"),
    learn_more(
        ("spec.omnist.dev — §6 The Schema Algebra", "https://spec.omnist.dev/06-schema-algebra/"),
        ("py.omnist.dev — Operations", "https://py.omnist.dev/guide/#operations"),
    ),
]))

step("10-inferring", "Inferring a schema", "Draft a schema from example documents instead of writing one by hand.", "".join([
    p("<code>infer(samples)</code> drafts a schema mechanically from a list of example Documents:"),
    code('from omnist import infer, doc\n\ns = infer([doc({"id": 1, "tags": ["a"]}), doc({"id": 2, "tags": ["b", "c"]})])\nprint(s.to_osd())'),
    output('record Root {\n    "id": integer,\n    "tags" [0,]: string,\n}\nroot Root'),
    p("<code>infer</code> returns the raw mechanical inference — it does <b>not</b> normalize. Nested-record names stay 1:1 with the sample's own labels, so structurally-identical shapes under different labels come out as duplicate records. Call <code>.normalize()</code> on the result where a canonical minimal schema is wanted."),
    learn_more(
        ("spec.omnist.dev — §6.10 infer(samples)", "https://spec.omnist.dev/06-schema-algebra/#610-infersamples"),
        ("py.omnist.dev — Inferring a schema", "https://py.omnist.dev/guide/#inferring-a-schema"),
    ),
]))

step("11-custom-formats", "Custom formats", "Register your own format plugin — usable everywhere Doc reads and writes by name.", "".join([
    p("Formats are plugins. Registering one makes it usable everywhere a <code>Doc</code> reads or writes a format by name, the same way JSON or YAML are:"),
    code('from omnist import Format, register_format, Doc\n\nregister_format(Format(\n    name="lines",\n    read=lambda text: [("n", int(x)) for x in text.split()],\n    write=lambda node, **opts: " ".join(str(v) for _, v in node),\n))\nDoc.from_format("lines", "1 2 3").to_format("lines")'),
    output("'1 2 3'"),
    learn_more(
        ("py.omnist.dev — Custom formats", "https://py.omnist.dev/guide/#custom-formats"),
    ),
]))

step("12-real-life-example", "A real-life example", "Named records, a required array, an optional field, and recursion-free reuse — built once, validated across formats.", "".join([
    p("An order schema, combining several of the ideas from earlier steps into one working example:"),
    code('ORDER = \'\'\'\nrecord Address  { "street": string, "city": string }\nrecord LineItem { "sku": string, "qty": integer, "price": number }\nrecord Order {\n    "id":       string,\n    "status":   string,\n    "total":    number,\n    "address":  Address,\n    "items" [1,]: LineItem,        # at least one line item\n    "coupon" [0,1]: string,         # optional\n}\nroot Order\n\'\'\'\ns = parse_schema(ORDER)'),
    p("The records form a graph, linked by references, each with the field's cardinality attached:"),
    '<pre class="mermaid">\ngraph LR\n    Order["Order"] -->|"address [1,1]"| Address["Address"]\n    Order -->|"items [1,]"| LineItem["LineItem"]\n</pre>',
    code('good = Doc.from_oml(\'\'\'\nid: "A1"\nstatus: "shipped"\ntotal: 29.97\naddress: { street: "1 Main St"; city: "London" }\nitems: { sku: "W"; qty: 3; price: 9.99 }\n\'\'\')\ns.validate(good).ok'),
    output("True"),
    p("As a tree of labeled edges, this is the same document every format above would read into:"),
    '<pre class="mermaid">\ngraph LR\n    order["(root)"] --> id["id: A1"]\n    order --> status["status: shipped"]\n    order --> total["total: 29.97"]\n    order --> address["address"]\n    address --> street["street: 1 Main St"]\n    address --> city["city: London"]\n    order --> items["items"]\n    items --> sku["sku: W"]\n    items --> qty["qty: 3"]\n    items --> price["price: 9.99"]\n</pre>',
    code('bad = Doc.from_oml(\'\'\'\nid: "A2"\nstatus: "shipped"\ntotal: "ten"\naddress: { street: "x"; city: "y" }\n\'\'\')\nprint(s.validate(bad))'),
    output("invalid:\n  at $.total: expected number, got string ('ten')\n  at $: field 'items' occurs 0 time(s), expected at least 1"),
    p("Two independent problems, both reported — a missing type match and a missing required field — since validation collects every failure rather than stopping at the first."),
    learn_more(
        ("py.omnist.dev — A real-life example", "https://py.omnist.dev/guide/#a-real-life-example"),
    ),
]))

step("13-cli", "The command line", "Every operation above, without writing any code.", "".join([
    p("Every operation this tutorial has shown as a Python call is also available as a shell command — the <code>omnist</code> CLI wraps the same library, one subcommand per operation:"),
    code("omnist convert doc.oml --from oml --to json", "bash"),
    output('{"name": "Ann"}'),
    code("omnist validate doc.json --from json --schema order.osd", "bash"),
    p("(same <code>ok</code>/error-path output as <code>schema.validate</code> above, formatted for a terminal)"),
    code("omnist schema compatible-with v1.osd v2.osd", "bash"),
    p("(the same question as <code>v1.compatible_with(v2)</code> from the schema algebra step, answered without Python)"),
    p("The full subcommand surface:"),
    '<table class="cmdtable"><thead><tr><th>Command</th><th>Does what</th></tr></thead><tbody>'
    '<tr><td><code>omnist format</code></td><td>reformat OML (compact ↔ indented)</td></tr>'
    '<tr><td><code>omnist convert</code></td><td>read one format, write another</td></tr>'
    '<tr><td><code>omnist check</code></td><td>simulate a write, report adjustments, without writing</td></tr>'
    '<tr><td><code>omnist infer</code></td><td>draft a schema from example documents</td></tr>'
    '<tr><td><code>omnist validate</code></td><td>validate a document against a schema</td></tr>'
    '<tr><td><code>omnist schema format</code></td><td>reformat OSD (compact ↔ indented)</td></tr>'
    '<tr><td><code>omnist schema normalize</code></td><td>canonical minimal form</td></tr>'
    '<tr><td><code>omnist schema prune</code></td><td>drop unreachable/unsatisfiable structure</td></tr>'
    '<tr><td><code>omnist schema is-empty</code></td><td>does this schema accept any document at all?</td></tr>'
    '<tr><td><code>omnist schema lint</code></td><td>diagnose structural problems, without mutating</td></tr>'
    '<tr><td><code>omnist schema extract</code></td><td>minimal subschema for a kept label set</td></tr>'
    '<tr><td><code>omnist schema compatible-with</code></td><td>can readers of B still read A\'s documents?</td></tr>'
    '<tr><td><code>omnist schema equivalent</code></td><td>same documents, different shape?</td></tr>'
    '</tbody></table>',
    learn_more(
        ("py.omnist.dev — CLI reference", "https://py.omnist.dev/cli/"),
    ),
]))

step("14-next-steps", "Next steps", "Where to go from here.", "".join([
    p("This tutorial covered the Document model, OML, OSD, validation, materialization, the other four codecs, the full schema algebra, inference, and the CLI — the complete feature set, in Python."),
    p("Everything here exists the same way in the other four independent ports, each built spec-first against the same conformance suite:"),
    '<table class="cmdtable"><thead><tr><th>Language</th><th>Docs</th></tr></thead><tbody>'
    '<tr><td>Python (used in this tutorial)</td><td><a href="https://py.omnist.dev">py.omnist.dev</a></td></tr>'
    '<tr><td>TypeScript</td><td><a href="https://ts.omnist.dev">ts.omnist.dev</a></td></tr>'
    '<tr><td>Rust</td><td><a href="https://rs.omnist.dev">rs.omnist.dev</a></td></tr>'
    '<tr><td>Go</td><td><a href="https://go.omnist.dev">go.omnist.dev</a></td></tr>'
    '<tr><td>Java</td><td><a href="https://j.omnist.dev">j.omnist.dev</a></td></tr>'
    '</tbody></table>',
    learn_more(
        ("spec.omnist.dev — the full specification", "https://spec.omnist.dev"),
        ("omnist.dev — project home", "https://omnist.dev"),
        ("omnist.dev/presentation.html — the introduction slides", "https://omnist.dev/presentation.html"),
        ("github.com/omnist-dev — all five ports + the spec", "https://github.com/omnist-dev"),
    ),
]))

# ---------------------------------------------------------------------------

CSS = """
:root {
  --bg: #fff1e5; --fg: #1a1a1a; --muted: #5a5a5a; --accent: #3f51b5;
  --border: #e2e2e2; --card-bg: #fafafa; --code-bg: #f2f2f5;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #14161a; --fg: #e8e8ea; --muted: #a0a3ab; --accent: #8c9eff; --border: #2a2d33; --card-bg: #1c1f24; --code-bg: #22252b; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; }
header.site { display: flex; align-items: center; gap: 0.6rem; padding: 1.2rem 1.5rem; border-bottom: 1px solid var(--border); }
header.site img { width: 32px; height: 32px; }
header.site a.home { color: var(--fg); text-decoration: none; font-weight: 700; font-size: 1.1rem; }
header.site .step-count { margin-left: auto; color: var(--muted); font-size: 0.9rem; }
main { max-width: 720px; margin: 0 auto; padding: 2.5rem 1.5rem 4rem; }
h1 { font-size: 2rem; margin: 0 0 0.3rem; letter-spacing: -0.01em; }
.description { color: var(--muted); font-size: 1.05rem; margin: 0 0 2rem; }
p { margin: 0 0 1.1rem; }
code { background: var(--code-bg); padding: 0.15em 0.4em; border-radius: 4px; font-size: 0.92em; font-family: "SFMono-Regular", Consolas, monospace; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
pre.code, pre.output { background: var(--code-bg); border-radius: 8px; padding: 0.9rem 1rem; overflow-x: auto; font-size: 0.88rem; margin: 0 0 1.3rem; }
pre.code code, pre.output code { background: none; padding: 0; font-size: inherit; }
.output-label { font-size: 0.78rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin: -0.6rem 0 0.4rem; }
.mermaid { display: flex; justify-content: center; margin: 1.5rem 0; background: var(--card-bg); border-radius: 8px; padding: 1rem; }
table.cmdtable { width: 100%; border-collapse: collapse; margin: 1rem 0 1.5rem; font-size: 0.92rem; }
table.cmdtable th, table.cmdtable td { text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid var(--border); }
table.cmdtable th { color: var(--muted); font-weight: 600; }
.learn-more { margin-top: 2rem; padding-top: 1.2rem; border-top: 1px solid var(--border); }
.learn-more h3 { font-size: 0.95rem; color: var(--muted); margin: 0 0 0.5rem; text-transform: uppercase; letter-spacing: 0.04em; }
.learn-more ul { margin: 0; padding-left: 1.2rem; }
nav.steps { display: flex; justify-content: space-between; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border); font-size: 0.95rem; }
nav.steps a { font-weight: 600; }
nav.steps .placeholder { color: var(--border); }
.index-list { list-style: none; padding: 0; margin: 1.5rem 0; }
.index-list li { border: 1px solid var(--border); border-radius: 10px; padding: 0.9rem 1.1rem; margin-bottom: 0.7rem; }
.index-list a { font-weight: 700; font-size: 1.05rem; }
.index-list .n { color: var(--muted); font-weight: 400; margin-right: 0.4rem; }
.index-list p { margin: 0.3rem 0 0; color: var(--muted); font-size: 0.92rem; }
"""

def render_body_parts(parts):
    return "".join(x if isinstance(x, str) and x.startswith("<") else x for x in parts)

def page_shell(title, step_no, body_inner, prev_link, next_link):
    step_count_html = f'<span class="step-count">Step {step_no} of {len(STEPS)}</span>' if step_no else '<span class="step-count">Tutorial overview</span>'
    prev_html = f'<a href="{prev_link[0]}">&larr; {prev_link[1]}</a>' if prev_link else '<span class="placeholder">&larr;</span>'
    next_html = f'<a href="{next_link[0]}">{next_link[1]} &rarr;</a>' if next_link else '<span class="placeholder">&rarr;</span>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — Omnist Tutorial</title>
<meta name="description" content="A hands-on, verified-code tutorial covering every model and feature of Omnist, using the Python port.">
<meta property="og:title" content="{html.escape(title)} — Omnist Tutorial">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/tutorial/">
<link rel="icon" type="image/svg+xml" href="../logo.svg">
<style>{CSS}</style>
</head>
<body>
<header class="site">
  <img src="../logo.svg" alt="Omnist logo">
  <a class="home" href="../index.html">Omnist</a>
  <a href="index.html" style="margin-left:1rem;">Tutorial</a>
  {step_count_html}
</header>
<main>
{body_inner}
<nav class="steps">
  {prev_html}
  {next_html}
</nav>
</main>
<!-- mermaid.js (MIT) -- vendored, no CDN. See ../assets/reveal/LICENSE for the same-license note. -->
<script src="../assets/mermaid.min.js"></script>
<script>
if (document.querySelector('.mermaid')) {{
  mermaid.initialize({{
    startOnLoad: false, theme: 'base',
    themeVariables: {{ primaryColor: '#f9f4ed', primaryBorderColor: '#645c50', primaryTextColor: '#201e1d', lineColor: '#645c50', fontFamily: 'inherit' }}
  }});
  document.querySelectorAll('pre.mermaid').forEach(async function (el, i) {{
    try {{
      var out = await mermaid.render('mmd-' + i, el.textContent.trim());
      el.innerHTML = out.svg;
    }} catch (e) {{ console.error('mermaid render failed', e); }}
  }});
}}
</script>
</body>
</html>
"""

def build():
    os.makedirs(OUT_DIR, exist_ok=True)

    # index.html
    items = []
    for i, s in enumerate(STEPS, start=1):
        items.append(f'<li><a href="{s["slug"]}.html"><span class="n">{i:02d}</span>{html.escape(s["title"])}</a><p>{s["description"]}</p></li>')
    index_body = (
        "<h1>Omnist Tutorial</h1>"
        '<p class="description">A hands-on, verified-code walkthrough of every model and feature, using the Python port. '
        "Every example on every page was actually run against the real library — the output shown is real output, not typed by hand.</p>"
        f'<ul class="index-list">{"".join(items)}</ul>'
    )
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(page_shell("Overview", 0, index_body, None, (STEPS[0]["slug"] + ".html", STEPS[0]["title"])))

    # step pages
    for i, s in enumerate(STEPS):
        step_no = i + 1
        prev_link = (STEPS[i-1]["slug"] + ".html", STEPS[i-1]["title"]) if i > 0 else ("index.html", "Overview")
        next_link = (STEPS[i+1]["slug"] + ".html", STEPS[i+1]["title"]) if i < len(STEPS) - 1 else None
        body_inner = f'<h1>{html.escape(s["title"])}</h1><p class="description">{s["description"]}</p>{s["body"]}'
        with open(os.path.join(OUT_DIR, s["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(page_shell(s["title"], step_no, body_inner, prev_link, next_link))

    print(f"Wrote {len(STEPS) + 1} files to {OUT_DIR}")

if __name__ == "__main__":
    build()
