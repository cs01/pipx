import sys
from typing import Any, Dict

WIN = sys.platform.startswith("win")


def _app_names(apps):
    app_strings = []
    app_strings = [f"{app}.exe" if WIN else app for app in apps]
    return app_strings


# Versions of all packages possibly used in our tests
# Only apply _app_names to entry_points, NOT scripts!
PKG: Dict[str, Dict[str, Any]] = {
    "ansible": {
        "spec": "ansible==2.9.13",
        "apps": [
            "ansible",
            "ansible-config",
            "ansible-connection",
            "ansible-console",
            "ansible-doc",
            "ansible-galaxy",
            "ansible-inventory",
            "ansible-playbook",
            "ansible-pull",
            "ansible-test",
            "ansible-vault",
        ],
        "apps_of_dependencies": [],
    },
    "awscli": {
        "spec": "awscli==1.18.168",
        "apps": [
            "aws",
            "aws.cmd",
            "aws_bash_completer",
            "aws_completer",
            "aws_zsh_completer.sh",
        ],
        "apps_of_dependencies": [
            "jp.py",
            "pyrsa-decrypt",
            "pyrsa-encrypt",
            "pyrsa-keygen",
            "pyrsa-priv2pub",
            "pyrsa-sign",
            "pyrsa-verify",
            "rst2html.py",
            "rst2html4.py",
            "rst2html5.py",
            "rst2latex.py",
            "rst2man.py",
            "rst2odt.py",
            "rst2odt_prepstyles.py",
            "rst2pseudoxml.py",
            "rst2s5.py",
            "rst2xetex.py",
            "rst2xml.py",
            "rstpep2html.py",
        ],
    },
    "b2": {
        "spec": "b2==2.0.2",
        "apps": ["b2"],
        "apps_of_dependencies": ["chardetect", "tqdm"],
    },
    "beancount": {
        "spec": "beancount==2.3.3",
        "apps": [
            "bean-bake",
            "bean-check",
            "bean-doctor",
            "bean-example",
            "bean-extract",
            "bean-file",
            "bean-format",
            "bean-identify",
            "bean-price",
            "bean-query",
            "bean-report",
            "bean-sql",
            "bean-web",
            "treeify",
            "upload-to-sheets",
        ],
        "apps_of_dependencies": [
            "bottle.py",
            "chardetect",
            "py.test",
            "pyrsa-decrypt",
            "pyrsa-encrypt",
            "pyrsa-keygen",
            "pyrsa-priv2pub",
            "pyrsa-sign",
            "pyrsa-verify",
            "pytest",
        ],
    },
    "beets": {
        "spec": "beets==1.4.9",
        "apps": ["beet"],
        "apps_of_dependencies": [
            "mid3cp",
            "mid3iconv",
            "mid3v2",
            "moggsplit",
            "mutagen-inspect",
            "mutagen-pony",
            "unidecode",
        ],
    },
    "black": {
        "spec": "black==20.8b1",
        "apps": ["black", "black-primer", "blackd"],
        "apps_of_dependencies": [],
    },
    "cactus": {
        "spec": "cactus==3.3.3",
        "apps": ["cactus"],
        "apps_of_dependencies": [
            "asadmin",
            "bundle_image",
            "cfadmin",
            "cq",
            "cwutil",
            "django-admin.py",
            "dynamodb_dump",
            "dynamodb_load",
            "elbadmin",
            "fetch_file",
            "glacier",
            "instance_events",
            "keyring",
            "kill_instance",
            "launch_instance",
            "list_instances",
            "lss3",
            "markdown2",
            "mturk",
            "pyami_sendmail",
            "route53",
            "s3put",
            "sdbadmin",
            "taskadmin",
        ],
    },
    "chert": {
        "spec": "chert==19.1.0",
        "apps": ["chert"],
        "apps_of_dependencies": ["ashes", "ashes.py", "markdown_py"],
    },
    "cloudtoken": {
        "spec": "cloudtoken==0.1.707",
        "apps": ["cloudtoken", "cloudtoken.app", "cloudtoken_proxy.sh", "awstoken"],
        "apps_of_dependencies": ["chardetect", "flask", "jp.py", "keyring"],
    },
    "coala": {
        "spec": "coala==0.11.0",
        "apps": [
            "coala",
            "coala-ci",
            "coala-delete-orig",
            "coala-format",
            "coala-json",
        ],
        "apps_of_dependencies": ["chardetect", "pygmentize", "unidiff"],
    },
    "cookiecutter": {
        "spec": "cookiecutter==1.7.2",
        "apps": ["cookiecutter"],
        "apps_of_dependencies": ["chardetect", "slugify"],
    },
    "cython": {
        "spec": "cython==0.29.21",
        "apps": ["cygdb", "cython", "cythonize"],
        "apps_of_dependencies": [],
    },
    "datasette": {
        "spec": "datasette==0.50.2",
        "apps": ["datasette"],
        "apps_of_dependencies": ["hupper", "pint-convert" "uvicorn"],
    },
    "diffoscope": {
        "spec": "diffoscope==154",
        "apps": ["diffoscope"],
        "apps_of_dependencies": [],
    },
    "doc2dash": {
        "spec": "doc2dash==2.3.0",
        "apps": ["doc2dash"],
        "apps_of_dependencies": [
            "chardetect",
            "pybabel",
            "pygmentize",
            "rst2html.py",
            "rst2html4.py",
            "rst2html5.py",
            "rst2latex.py",
            "rst2man.py",
            "rst2odt.py",
            "rst2odt_prepstyles.py",
            "rst2pseudoxml.py",
            "rst2s5.py",
            "rst2xetex.py",
            "rst2xml.py",
            "rstpep2html.py",
            "sphinx-apidoc",
            "sphinx-autogen",
            "sphinx-build",
            "sphinx-quickstart",
        ],
    },
    "doitlive": {
        "spec": "doitlive==4.3.0",
        "apps": ["doitlive"],
        "apps_of_dependencies": [],
    },
    "gdbgui": {
        "spec": "gdbgui==0.14.0.1",
        "apps": ["gdbgui"],
        "apps_of_dependencies": ["flask", "pygmentize"],
    },
    "gns3-gui": {
        "spec": "gns3-gui==2.2.15",
        "apps": ["gns3"],
        "apps_of_dependencies": ["distro", "jsonschema"],
    },
    "grow": {
        "spec": "grow==1.0.0a10",
        "apps": ["grow"],
        "apps_of_dependencies": [
            "chardetect",
            "gen_protorpc",
            "html2text",
            "markdown_py",
            "pybabel",
            "pygmentize",
            "pyrsa-decrypt",
            "pyrsa-encrypt",
            "pyrsa-keygen",
            "pyrsa-priv2pub",
            "pyrsa-sign",
            "pyrsa-verify",
            "slugify",
            "watchmedo",
        ],
    },
    "guake": {
        "spec": "guake==3.7.0",
        "apps": ["guake", "guake-toggle"],
        "apps_of_dependencies": ["pbr"],
    },
    "gunicorn": {
        "spec": "gunicorn==20.0.4",
        "apps": ["gunicorn"],
        "apps_of_dependencies": [],
    },
    "howdoi": {
        "spec": "howdoi==2.0.7",
        "apps": ["howdoi"],
        "apps_of_dependencies": ["chardetect", "keep", "pygmentize", "pyjwt"],
    },
    "httpie": {
        "spec": "httpie==2.3.0",
        "apps": ["http", "https"],
        "apps_of_dependencies": ["chardetect", "pygmentize"],
    },
    "hyde": {
        "spec": "hyde==0.8.9",
        "apps": ["hyde"],
        "apps_of_dependencies": ["markdown_py", "pygmentize", "smartypants"],
    },
    "ipython": {
        "spec": "ipython==7.16.1",
        "apps": ["iptest", "iptest3", "ipython", "ipython3"],
        "apps_of_dependencies": ["pygmentize"],
    },
    "isort": {"spec": "isort==5.6.4", "apps": ["isort"], "apps_of_dependencies": []},
    "jaraco-financial": {
        "spec": "jaraco.financial==2.0",
        "apps": [
            "clean-msmoney-temp",
            "fix-qif-date-format",
            "launch-in-money",
            "ofx",
            "record-document-hashes",
        ],
        "apps_of_dependencies": ["keyring", "chardetect", "calc-prorate"],
    },
    "jupyter": {
        "spec": "jupyter==1.0.0",
        "apps": [],
        "apps_of_dependencies": [
            "iptest",
            "iptest3",
            "ipython",
            "ipython3",
            "jsonschema",
            "jupyter",
            "jupyter-bundlerextension",
            "jupyter-console",
            "jupyter-kernel",
            "jupyter-kernelspec",
            "jupyter-migrate",
            "jupyter-nbconvert",
            "jupyter-nbextension",
            "jupyter-notebook",
            "jupyter-qtconsole",
            "jupyter-run",
            "jupyter-serverextension",
            "jupyter-troubleshoot",
            "jupyter-trust",
            "pygmentize",
        ],
    },
    "kaggle": {
        "spec": "kaggle==1.5.9",
        "apps": ["kaggle"],
        "apps_of_dependencies": ["chardetect", "slugify", "tqdm"],
    },
    "kibitzr": {
        "spec": "kibitzr==6.0.0",
        "apps": ["kibitzr"],
        "apps_of_dependencies": ["chardetect", "doesitcache"],
    },
    "klaus": {
        "spec": "klaus==1.5.2",
        "apps": ["klaus"],
        "apps_of_dependencies": [
            "dul-receive-pack",
            "dul-upload-pack",
            "dulwich",
            "flask",
            "pygmentize",
        ],
    },
    "kolibri": {
        "spec": "kolibri==0.14.3",
        "apps": ["kolibri"],
        "apps_of_dependencies": [],
    },
    "lektor": {
        "spec": "Lektor==3.2.0",
        "apps": ["lektor"],
        "apps_of_dependencies": [
            "EXIF.py",
            "chardetect",
            "flask",
            "pybabel",
            "slugify",
            "watchmedo",
        ],
    },
    "localstack": {
        "spec": "localstack==0.12.1",
        "apps": ["localstack", "localstack.bat"],
        "apps_of_dependencies": ["chardetect", "jp.py"],
    },
    "mackup": {
        "spec": "mackup==0.8.29",
        "apps": ["mackup"],
        "apps_of_dependencies": [],
    },  # ONLY FOR mac, linux
    "magic-wormhole": {
        "spec": "magic-wormhole==0.12.0",
        "apps": ["wormhole"],
        "apps_of_dependencies": [
            "automat-visualize",
            "cftp",
            "ckeygen",
            "conch",
            "mailmail",
            "pyhtmlizer",
            "tkconch",
            "tqdm",
            "trial",
            "twist",
            "twistd",
            "wamp",
            "xbrnetwork",
        ],
    },
    "mayan-edms": {
        "spec": "mayan-edms==3.5.2",
        "apps": ["mayan-edms.py"],
        "apps_of_dependencies": [
            "celery",
            "chardetect",
            "django-admin",
            "django-admin.py",
            "gunicorn",
            "jsonpointer",
            "jsonschema",
            "sqlformat",
            "swagger-flex",
            "update-tld-names",
        ],
    },
    "mkdocs": {
        "spec": "mkdocs==1.1.2",
        "apps": ["mkdocs"],
        "apps_of_dependencies": [
            "livereload",
            "futurize",
            "pasteurize",
            "nltk",
            "tqdm",
            "markdown_py",
        ],
    },
    "mycli": {
        "spec": "mycli==1.22.2",
        "apps": ["mycli"],
        "apps_of_dependencies": ["pygmentize", "sqlformat", "tabulate"],
    },
    "nikola": {
        "spec": "nikola==8.1.1",
        "apps": ["nikola"],
        "apps_of_dependencies": [
            "chardetect",
            "doit",
            "mako-render",
            "markdown_py",
            "natsort",
            "pybabel",
            "pygmentize",
            "rst2html.py",
            "rst2html4.py",
            "rst2html5.py",
            "rst2latex.py",
            "rst2man.py",
            "rst2odt.py",
            "rst2odt_prepstyles.py",
            "rst2pseudoxml.py",
            "rst2s5.py",
            "rst2xetex.py",
            "rst2xml.py",
            "rstpep2html.py",
            "unidecode",
        ],
    },
    "nox": {
        "spec": "nox==2020.8.22",
        "apps": ["nox", "tox-to-nox"],
        "apps_of_dependencies": [
            "activate-global-python-argcomplete",
            "python-argcomplete-check-easy-install-script",
            "python-argcomplete-tcsh",
            "register-python-argcomplete",
            "virtualenv",
        ],  # TODO: are some of these not real?
    },
    "pelican": {
        "spec": "pelican==4.5.0",
        "apps": [
            "pelican",
            "pelican-import",
            "pelican-plugins",
            "pelican-quickstart",
            "pelican-themes",
        ],
        "apps_of_dependencies": [
            "pygmentize",
            "rst2html.py",
            "rst2html4.py",
            "rst2html5.py",
            "rst2latex.py",
            "rst2man.py",
            "rst2odt.py",
            "rst2odt_prepstyles.py",
            "rst2pseudoxml.py",
            "rst2s5.py",
            "rst2xetex.py",
            "rst2xml.py",
            "rstpep2html.py",
            "unidecode",
        ],
    },
    "platformio": {
        "spec": "platformio==5.0.1",
        "apps": ["pio", "piodebuggdb", "platformio"],
        "apps_of_dependencies": [
            "bottle.py",
            "chardetect",
            "miniterm.py",
            "miniterm.pyc",
            "readelf.py",
            "tabulate",
        ],
    },
    "ppci": {
        "spec": "ppci==0.5.8",
        "apps": [
            "ppci-archive",
            "ppci-asm",
            "ppci-build",
            "ppci-c3c",
            "ppci-cc",
            "ppci-dbg",
            "ppci-disasm",
            "ppci-hexdump",
            "ppci-hexutil",
            "ppci-java",
            "ppci-ld",
            "ppci-llc",
            "ppci-mkuimage",
            "ppci-objcopy",
            "ppci-objdump",
            "ppci-ocaml",
            "ppci-opt",
            "ppci-pascal",
            "ppci-pedump",
            "ppci-pycompile",
            "ppci-readelf",
            "ppci-wabt",
            "ppci-wasm2wat",
            "ppci-wasmcompile",
            "ppci-wat2wasm",
            "ppci-yacc",
        ],
        "apps_of_dependencies": [],
    },
    "prosopopee": {
        "spec": "prosopopee==1.1.3",
        "apps": ["prosopopee"],
        "apps_of_dependencies": ["futurize", "pasteurize", "pybabel"],
    },
    "ptpython": {
        "spec": "ptpython==3.0.7",
        "apps": [
            "ptipython",
            "ptipython3",
            "ptipython3.8",
            "ptpython",
            "ptpython3",
            "ptpython3.8",
        ],
        "apps_of_dependencies": ["pygmentize"],
    },
    "pycowsay": {
        "spec": "pycowsay==0.0.0.1",
        "apps": ["pycowsay"],
        "apps_of_dependencies": [],
    },
    "pylint": {
        "spec": "pylint==2.3.1",
        "apps": ["epylint", "pylint", "pyreverse", "symilar"],
        "apps_of_dependencies": ["isort"],
    },
    "retext": {
        "spec": "ReText==7.1.0",
        "apps": ["retext"],
        "apps_of_dependencies": [
            "chardetect",
            "markdown_py",
            "pygmentize",
            "pylupdate5",
            "pyrcc5",
            "pyuic5",
            "rst2html.py",
            "rst2html4.py",
            "rst2html5.py",
            "rst2latex.py",
            "rst2man.py",
            "rst2odt.py",
            "rst2odt_prepstyles.py",
            "rst2pseudoxml.py",
            "rst2s5.py",
            "rst2xetex.py",
            "rst2xml.py",
            "rstpep2html.py",
        ],
    },
    "robotframework": {
        "spec": "robotframework==3.2.2",
        "apps": ["rebot", "robot"],
        "apps_of_dependencies": [],
    },
    "shell-functools": {
        "spec": "shell-functools==0.3.0",
        "apps": [
            "filter",
            "foldl",
            "foldl1",
            "ft-functions",
            "map",
            "sort_by",
            "take_while",
        ],
        "apps_of_dependencies": [],
    },
    "speedtest-cli": {
        "spec": "speedtest-cli==2.1.2",
        "apps": ["speedtest", "speedtest-cli"],
        "apps_of_dependencies": [],
    },
    "sphinx": {
        "spec": "Sphinx==3.2.1",
        "apps": [
            "sphinx-apidoc",
            "sphinx-autogen",
            "sphinx-build",
            "sphinx-quickstart",
        ],
        "apps_of_dependencies": [
            "chardetect",
            "pybabel",
            "pygmentize",
            "rst2html.py",
            "rst2html4.py",
            "rst2html5.py",
            "rst2latex.py",
            "rst2man.py",
            "rst2odt.py",
            "rst2odt_prepstyles.py",
            "rst2pseudoxml.py",
            "rst2s5.py",
            "rst2xetex.py",
            "rst2xml.py",
            "rstpep2html.py",
        ],
    },
    "sqlmap": {
        "spec": "sqlmap==1.4.10",
        "apps": ["sqlmap"],
        "apps_of_dependencies": [],
    },
    "streamlink": {
        "spec": "streamlink==1.7.0",
        "apps": ["streamlink"],
        "apps_of_dependencies": ["chardetect", "wsdump.py"],
    },
    "taguette": {
        "spec": "taguette==0.9.2",
        "apps": ["taguette"],
        "apps_of_dependencies": ["alembic", "mako-render", "vba_extract.py"],
    },
    "term2048": {
        "spec": "term2048==0.2.7",
        "apps": ["term2048"],
        "apps_of_dependencies": [],
    },
    "tox-ini-fmt": {
        "spec": "tox-ini-fmt==0.5.0",
        "apps": ["tox-ini-fmt"],
        "apps_of_dependencies": ["py.test", "pytest"],
    },
    "visidata": {
        "spec": "visidata==2.0.1",
        "apps": ["visidata", "vd"],
        "apps_of_dependencies": [],
    },
    "vulture": {
        "spec": "vulture==2.1",
        "apps": ["vulture"],
        "apps_of_dependencies": [],
    },
    "weblate": {
        "spec": "Weblate==4.3.1",
        "apps": ["weblate"],
        "apps_of_dependencies": [
            "borg",
            "borgfs",
            "build_firefox.sh",
            "build_tmdb",
            "buildxpi.py",
            "celery",
            "chardetect",
            "csv2po",
            "csv2tbx",
            "cygdb",
            "cython",
            "cythonize",
            "django-admin",
            "django-admin.py",
            "flatxml2po",
            "get_moz_enUS.py",
            "html2po",
            "html2text",
            "ical2po",
            "idml2po",
            "ini2po",
            "json2po",
            "jsonschema",
            "junitmsgfmt",
            "misaka",
            "moz2po",
            "mozlang2po",
            "odf2xliff",
            "oo2po",
            "oo2xliff",
            "php2po",
            "phppo2pypo",
            "po2csv",
            "po2flatxml",
            "po2html",
            "po2ical",
            "po2idml",
            "po2ini",
            "po2json",
            "po2moz",
            "po2mozlang",
            "po2oo",
            "po2php",
            "po2prop",
            "po2rc",
            "po2resx",
            "po2sub",
            "po2symb",
            "po2tiki",
            "po2tmx",
            "po2ts",
            "po2txt",
            "po2web2py",
            "po2wordfast",
            "po2xliff",
            "po2yaml",
            "poclean",
            "pocommentclean",
            "pocompendium",
            "pocompile",
            "poconflicts",
            "pocount",
            "podebug",
            "pofilter",
            "pogrep",
            "pomerge",
            "pomigrate2",
            "popuretext",
            "poreencode",
            "porestructure",
            "posegment",
            "posplit",
            "poswap",
            "pot2po",
            "poterminology",
            "pretranslate",
            "prop2po",
            "pydiff",
            "pyjwt",
            "pypo2phppo",
            "rc2po",
            "resx2po",
            "sqlformat",
            "sub2po",
            "symb2po",
            "tbx2po",
            "tiki2po",
            "tmserver",
            "ts2po",
            "txt2po",
            "web2py2po",
            "weblate-discover",
            "xliff2odf",
            "xliff2oo",
            "xliff2po",
            "yaml2po",
        ],
    },
    "youtube-dl": {
        "spec": "youtube-dl==2020.9.20",
        "apps": ["youtube-dl"],
        "apps_of_dependencies": [],
    },
    "zeo": {
        "spec": "ZEO==5.2.2",
        "apps": ["runzeo", "zeo-nagios", "zeoctl", "zeopack"],
        "apps_of_dependencies": [
            "fsdump",
            "fsoids",
            "fsrefs",
            "fstail",
            "repozo",
            "zconfig",
            "zconfig_schema2html",
            "zdaemon",
        ],
    },
}
