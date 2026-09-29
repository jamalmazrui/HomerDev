# Conversions by format pair

EdSharp's Import and Export tables, which have been used for years, hold a
tested command for each pair. The Pandoc ones are below, with the source as
`in` and the target as `out`; `-s` makes a standalone document. Pairs that
run a helper (any2htm, pdf2md, sheet2md, mdx2htm, mdx2docx) are EdSharp
scripts in its configs/convert folder; 2htm or inixVert does the same work
outside EdSharp.

Two differences from a Homer document: these pairs read and write GitHub's
Markdown (`gfm`), where a Homer document uses Pandoc's own (`-f markdown`); and
they accept `.html` as well as `.htm`, where a Homer program writes `.htm`.

## Contents
- Pandoc pairs
- Other tools

## Pandoc pairs

- **adoc2htm**: `pandoc in -f asciidoc -t html -s -o out`
- **adoc2md**: `pandoc in -f asciidoc -t gfm -o out`
- **adoc2txt**: `pandoc in -f asciidoc -t plain -o out`
- **docx2htm**: `pandoc in -f docx -t html -s -o out`
- **docx2html**: `pandoc in -f docx -t html -s -o out`
- **docx2md**: `pandoc in -f docx -t gfm -o out`
- **docx2mw**: `pandoc in -f docx -t mediawiki -o out`
- **docx2rst**: `pandoc in -f docx -t rst -o out`
- **docx2tex**: `pandoc in -f docx -t latex -s -o out`
- **docx2txt**: `pandoc in -f docx -t plain -o out`
- **epub2htm**: `pandoc in -f epub -t html -s -o out`
- **epub2html**: `pandoc in -f epub -t html -s -o out`
- **epub2md**: `pandoc in -f epub -t gfm -o out`
- **epub2mw**: `pandoc in -f epub -t mediawiki -o out`
- **epub2tex**: `pandoc in -f epub -t latex -s -o out`
- **epub2txt**: `pandoc in -f epub -t plain -o out`
- **htm2md**: `pandoc in -f html -t gfm -o out`
- **htm2mw**: `pandoc in -f html -t mediawiki -o out`
- **htm2rst**: `pandoc in -f html -t rst -o out`
- **htm2tex**: `pandoc in -f html -t latex -s -o out`
- **htm2txt**: `pandoc in -f html -t plain -o out`
- **html2md**: `pandoc in -f html -t gfm -o out`
- **html2mw**: `pandoc in -f html -t mediawiki -o out`
- **html2rst**: `pandoc in -f html -t rst -o out`
- **html2tex**: `pandoc in -f html -t latex -s -o out`
- **html2txt**: `pandoc in -f html -t plain -o out`
- **md2docx**: `pandoc in -f gfm -t docx -o out`
- **md2docxrefs**: `pandoc in -f markdown -t docx -o out`
- **md2epub**: `pandoc in -f gfm -t epub -o out`
- **md2epub3**: `pandoc in -f gfm -t epub3 -o out`
- **md2htm**: `pandoc in -f gfm -t html -s -o out`
- **md2html**: `pandoc in -f gfm -t html -s -o out`
- **md2mw**: `pandoc in -f gfm -t mediawiki -o out`
- **md2pptx**: `pandoc in -f markdown -t pptx -o out`
- **md2rst**: `pandoc in -f gfm -t rst -o out`
- **md2rtf**: `pandoc in -f gfm -t rtf -s -o out`
- **md2tex**: `pandoc in -f gfm -t latex -s -o out`
- **md2txt**: `pandoc in -f gfm -t plain -o out`
- **odt2htm**: `pandoc in -f odt -t html -s -o out`
- **odt2html**: `pandoc in -f odt -t html -s -o out`
- **odt2md**: `pandoc in -f odt -t gfm -o out`
- **odt2txt**: `pandoc in -f odt -t plain -o out`
- **pptx2htm**: `pandoc in -f pptx -t html -s -o out`
- **pptx2md**: `pandoc in -f pptx -t gfm -o out`
- **pptx2txt**: `pandoc in -f pptx -t plain -o out`
- **rst2docx**: `pandoc in -f rst -t docx -o out`
- **rst2epub**: `pandoc in -f rst -t epub -o out`
- **rst2epub3**: `pandoc in -f rst -t epub3 -o out`
- **rst2htm**: `pandoc in -f rst -t html -s -o out`
- **rst2html**: `pandoc in -f rst -t html -s -o out`
- **rst2md**: `pandoc in -f rst -t gfm -o out`
- **rst2mw**: `pandoc in -f rst -t mediawiki -o out`
- **rst2rtf**: `pandoc in -f rst -t rtf -s -o out`
- **rst2tex**: `pandoc in -f rst -t latex -s -o out`
- **rst2txt**: `pandoc in -f rst -t plain -o out`
- **rtf2docx**: `pandoc in -f rtf -t docx -o out`
- **rtf2htm**: `pandoc in -f rtf -t html -s -o out`
- **rtf2html**: `pandoc in -f rtf -t html -s -o out`
- **rtf2md**: `pandoc in -f rtf -t gfm -o out`
- **rtf2txt**: `pandoc in -f rtf -t plain -o out`
- **tex2docx**: `pandoc in -f latex -t docx -o out`
- **tex2epub**: `pandoc in -f latex -t epub -o out`
- **tex2epub3**: `pandoc in -f latex -t epub3 -o out`
- **tex2htm**: `pandoc in -f latex -t html -s -o out`
- **tex2html**: `pandoc in -f latex -t html -s -o out`
- **tex2md**: `pandoc in -f latex -t gfm -o out`
- **tex2mw**: `pandoc in -f latex -t mediawiki -o out`
- **tex2rst**: `pandoc in -f latex -t rst -o out`
- **tex2rtf**: `pandoc in -f latex -t rtf -s -o out`
- **tex2txt**: `pandoc in -f latex -t plain -o out`
- **tt2htm**: `pandoc in -f t2t -t html -s -o out`
- **tt2html**: `pandoc in -f t2t -t html -s -o out`
- **tt2md**: `pandoc in -f t2t -t gfm -o out`
- **tt2mw**: `pandoc in -f t2t -t mediawiki -o out`
- **tt2rst**: `pandoc in -f t2t -t rst -o out`
- **tt2rtf**: `pandoc in -f t2t -t rtf -s -o out`
- **tt2txt**: `pandoc in -f t2t -t plain -o out`
- **typ2htm**: `pandoc in -f typst -t html -s -o out`
- **typ2md**: `pandoc in -f typst -t gfm -o out`
- **typ2txt**: `pandoc in -f typst -t plain -o out`
- **xlsx2htm**: `pandoc in -f xlsx -t html -s -o out`
- **xlsx2md**: `pandoc in -f xlsx -t gfm -o out`
- **xlsx2txt**: `pandoc in -f xlsx -t plain -o out`

## Other tools

- **brf2txt**: built into EdSharp
- **brl2txt**: built into EdSharp
- **csv2inix**: inixVert in out
- **doc2htm**: EdSharp helper any2htm.cmd
- **doc2html**: EdSharp helper any2htm.cmd
- **doc2md**: EdSharp helper any2htm.cmd
- **doc2txt**: EdSharp helper any2txt.cmd
- **epub32htm**: built into EdSharp
- **epub32html**: built into EdSharp
- **epub32md**: built into EdSharp
- **epub32mw**: built into EdSharp
- **epub32tex**: built into EdSharp
- **epub32txt**: built into EdSharp
- **hlp2txt**: built into EdSharp
- **htm2tidy**: built into EdSharp
- **html2tidy**: built into EdSharp
- **inix2csv**: inixVert in out
- **inix2md**: inixVert in out
- **inix2xlsx**: inixVert in out
- **md2inix**: inixVert in out
- **mdx2docx**: EdSharp helper mdx2docx.cmd
- **mdx2htm**: EdSharp helper mdx2htm.cmd
- **mdx2md**: inixVert in out
- **pdf2htm**: EdSharp helper pdf2md.cmd
- **pdf2html**: EdSharp helper pdf2md.cmd
- **pdf2md**: EdSharp helper pdf2md.cmd
- **pdf2txt**: EdSharp helper pdf2md.cmd
- **ppt2htm**: EdSharp helper any2htm.cmd
- **ppt2md**: EdSharp helper any2htm.cmd
- **ppt2txt**: EdSharp helper any2txt.cmd
- **wpd2txt**: built into EdSharp
- **xls2csv**: %ProgDir%\configs\convert\OfficeConvert\
- **xls2htm**: EdSharp helper any2htm.cmd
- **xls2md**: EdSharp helper sheet2md.cmd
- **xls2txt**: EdSharp helper any2txt.cmd
- **xlsx2csv**: inixVert in out
- **xlsx2inix**: inixVert in out
