from io import BytesIO


class SimplePDFBuilder:
    """Generate small text-based PDFs without external dependencies."""

    def __init__(self, title='Document'):
        self.title = title
        self.page_width = 595
        self.page_height = 842
        self.margin_x = 40
        self.top_y = 800
        self.line_height = 14
        self.lines = []

    def add_line(self, text='', indent=0):
        self.lines.append((indent, str(text or '')))

    def add_blank_line(self):
        self.lines.append((0, ''))

    def build(self):
        buffer = BytesIO()
        objects = []

        font_object = b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'
        objects.append(font_object)

        content_stream = self._build_content_stream()
        content_object = b'<< /Length %d >>\nstream\n%s\nendstream' % (len(content_stream), content_stream)
        objects.append(content_object)

        page_object = (
            b'<< /Type /Page /Parent 4 0 R /MediaBox [0 0 %d %d] '
            b'/Resources << /Font << /F1 1 0 R >> >> /Contents 2 0 R >>'
        ) % (self.page_width, self.page_height)
        objects.append(page_object)

        pages_object = b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>'
        objects.append(pages_object)

        catalog_object = b'<< /Type /Catalog /Pages 4 0 R >>'
        objects.append(catalog_object)

        info_object = b'<< /Title (%s) >>' % self._escape(self.title)
        objects.append(info_object)

        buffer.write(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')

        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(buffer.tell())
            buffer.write(b'%d 0 obj\n%s\nendobj\n' % (index, obj))

        xref_position = buffer.tell()
        buffer.write(b'xref\n0 %d\n' % (len(objects) + 1))
        buffer.write(b'0000000000 65535 f \n')
        for offset in offsets[1:]:
            buffer.write(b'%010d 00000 n \n' % offset)

        buffer.write(
            b'trailer\n<< /Size %d /Root 5 0 R /Info 6 0 R >>\nstartxref\n%d\n%%%%EOF' %
            (len(objects) + 1, xref_position)
        )
        buffer.seek(0)
        return buffer

    def _build_content_stream(self):
        commands = [b'BT', b'/F1 11 Tf']
        y = self.top_y
        for indent, text in self.lines:
            if y < 50:
                break
            safe = self._escape(text)
            x = self.margin_x + (indent * 14)
            commands.append(b'1 0 0 1 %d %d Tm (%s) Tj' % (x, y, safe))
            y -= self.line_height
        commands.append(b'ET')
        return b'\n'.join(commands)

    def _escape(self, value):
        return (
            value
            .replace('\\', '\\\\')
            .replace('(', '\\(')
            .replace(')', '\\)')
            .encode('latin-1', 'replace')
        )
