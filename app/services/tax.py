from config import Config


GST_MODE_EXCLUSIVE = 'exclusive'
GST_MODE_INCLUSIVE = 'inclusive'
GST_MODE_NONE = 'none'
GST_MODE_CHOICES = [
    (GST_MODE_EXCLUSIVE, 'GST Exclusive'),
    (GST_MODE_INCLUSIVE, 'GST Inclusive'),
    (GST_MODE_NONE, 'No GST'),
]


def calculate_gst_breakdown(lines_total, gst_mode, gst_rate=None):
    """Convert entered line totals into subtotal, gst, and total values."""
    total_value = float(lines_total or 0)
    rate = Config.GST_RATE if gst_rate is None else float(gst_rate or 0)

    if gst_mode == GST_MODE_INCLUSIVE:
        total = total_value
        subtotal = total / (1 + rate) if rate > 0 else total
        gst_amount = total - subtotal
    elif gst_mode == GST_MODE_NONE:
        subtotal = total_value
        gst_amount = 0.0
        total = subtotal
    else:
        subtotal = total_value
        gst_amount = subtotal * rate
        total = subtotal + gst_amount

    return {
        'subtotal': round(subtotal, 2),
        'gst_amount': round(gst_amount, 2),
        'total_amount': round(total, 2),
    }


def gross_from_line_total(line_total, gst_mode, gst_rate=None):
    rate = Config.GST_RATE if gst_rate is None else float(gst_rate or 0)
    line_total = float(line_total or 0)
    if gst_mode == GST_MODE_EXCLUSIVE:
        return round(line_total * (1 + rate), 2)
    return round(line_total, 2)


def net_from_line_total(line_total, gst_mode, gst_rate=None):
    rate = Config.GST_RATE if gst_rate is None else float(gst_rate or 0)
    line_total = float(line_total or 0)
    if gst_mode == GST_MODE_INCLUSIVE:
        return round(line_total / (1 + rate), 2) if rate > 0 else round(line_total, 2)
    return round(line_total, 2)


def gst_label(gst_mode):
    if gst_mode == GST_MODE_INCLUSIVE:
        return 'GST Included'
    if gst_mode == GST_MODE_NONE:
        return 'No GST'
    return 'GST Exclusive'
