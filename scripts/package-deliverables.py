"""Build clean source and submission ZIPs; validate document structure and hashes."""
from pathlib import Path
import zipfile,json,hashlib
from pypdf import PdfReader
from docx import Document
from pptx import Presentation
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables'
skip_dirs={'node_modules','.next','.git','data','artifacts','__pycache__','.venv','.pytest_cache'}
root_files={'README.md','Dockerfile','render.yaml','start.mjs','.gitignore','.dockerignore','.gitattributes'}
source_roots={'web','backend','contract','docs','scripts'}
files=[]
for p in sorted(ROOT.rglob('*')):
 if not p.is_file() or p.name=='.DS_Store':continue
 rel=p.relative_to(ROOT)
 if any(x in skip_dirs for x in rel.parts):continue
 if p.name.startswith('.env') and p.name!='.env.example':continue
 if p.name.endswith(('.tsbuildinfo','.log')):continue
 if (len(rel.parts)==1 and p.name in root_files) or rel.parts[0] in source_roots:files.append(p)
 if rel.parts[0]=='deliverables' and (p.suffix in {'.md','.mmd','.svg','.png','.json','.log'}):files.append(p)
with zipfile.ZipFile(OUT/'SOURCE_CODE.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(ROOT))
assert len(PdfReader(OUT/'TECHNICAL_REPORT.pdf').pages)==14
assert len(Presentation(OUT/'PRESENTATION.pptx').slides)==12
assert len(PdfReader(OUT/'PRESENTATION.pdf').pages)==12
for name in ['TECHNICAL_REPORT','USER_MANUAL','INDIVIDUAL_CONTRIBUTION']:
 doc=Document(OUT/(name+'.docx'));text='\n'.join(p.text for p in doc.paragraphs)+'\n'+'\n'.join(c.text for t in doc.tables for r in t.rows for c in r.cells)
 assert 'Zeran Yao' in text and 'G2509029A' in text
for p in (OUT/'diagrams').glob('*.svg'):ET.parse(p)
with zipfile.ZipFile(OUT/'SOURCE_CODE.zip') as z:
 assert z.testzip() is None
 assert not any(Path(n).name.startswith('.env') and Path(n).name!='.env.example' for n in z.namelist())
 assert not any('/node_modules/' in n for n in z.namelist())
checks={'technicalReportPdfPages':14,'presentationSlides':12,'diagramSets':5,'sourceArchiveFiles':len(files),'privateEnvFilesInArchive':0,'docxIdentityChecks':'pass','svgXmlChecks':'pass','status':'Artifacts validated; agreed scope and pending public evidence remain documented.'}
(OUT/'evidence/artifact-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
# Artifact checks are generated after the source snapshot; bundle includes them directly.
entries=[p for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in {'SUBMISSION_BUNDLE.zip','SHA256SUMS.txt'}]
(OUT/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT)) for p in entries)+'\n')
with zipfile.ZipFile(OUT/'SUBMISSION_BUNDLE.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in entries+[OUT/'SHA256SUMS.txt']:z.write(p,Path('saving-deliverables')/p.relative_to(OUT))
with zipfile.ZipFile(OUT/'SUBMISSION_BUNDLE.zip') as z:assert z.testzip() is None
print(json.dumps(checks,indent=2));print('Submission bundle:',OUT/'SUBMISSION_BUNDLE.zip')
