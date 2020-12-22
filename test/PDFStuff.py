'''
import PyPDF2
fname=u'D:\Atrium\Projects\CTFC\psgf\database\PTGMF_PORREDON.pdf'
fname=r'D:\Atrium\Projects\CTFC\psgf\psgf\test\TestePDF.pdf'
#fname=u'projeto.pdf'
pdfFileObj=open(fname, "rb")
pdfReader=PyPDF2.PdfFileReader(pdfFileObj)
pdfReader.numPages
pageObj=pdfReader.getPage(0)
pageObj.extractText()
print()
'''
import sys
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1

fname=r'D:\Atrium\Projects\CTFC\psgf\psgf\test\TestePDF.pdf'
fname=r'D:\Atrium\Projects\CTFC\psgf\psgf\test\PTGMF_PORREDON_decrypted.pdf'
fp = open(fname, 'rb')

parser = PDFParser(fp)
doc = PDFDocument(parser)
fields = resolve1(doc.catalog['AcroForm'])['Fields']
for i in fields:
    field = resolve1(i)
    name, value = field.get('T'), field.get('V')
    print('{0}: {1}'.format(name, value))
