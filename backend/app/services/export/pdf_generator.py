"""PDF report generator using ReportLab."""
import io
from datetime import datetime
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart


def generate_analysis_pdf(product, insights: Dict[str, Any]) -> io.BytesIO:
    """
    Generate a PDF report for product analysis.
    
    Args:
        product: Product model instance
        insights: Insights dictionary from generate_product_insights
    
    Returns:
        BytesIO buffer containing PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        spaceAfter=20,
        textColor=colors.HexColor('#1a1a2e')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor('#16213e')
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8
    )
    
    elements = []
    
    # Title
    product_name = product.name or "Product Analysis Report"
    if len(product_name) > 60:
        product_name = product_name[:57] + "..."
    
    elements.append(Paragraph(f"{product_name}", title_style))
    elements.append(Paragraph(f"Analysis Report - {datetime.now().strftime('%B %d, %Y')}", body_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#e94560')))
    elements.append(Spacer(1, 20))
    
    # Overview Section
    elements.append(Paragraph("Overview", heading_style))
    
    overview_data = [
        ["Overall Score", f"{insights['overall_score']:.1f} / 100"],
        ["Total Reviews", str(insights['total_reviews'])],
        ["Average Rating", f"{insights['avg_rating']:.1f} / 5"],
        ["Suspicious Reviews", f"{insights['fake_review_count']} ({insights['fake_review_percent']:.1f}%)"],
    ]
    
    overview_table = Table(overview_data, colWidths=[2.5*inch, 2*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 15))
    
    # Rating Distribution
    elements.append(Paragraph("Rating Distribution", heading_style))
    
    rating_dist = insights['rating_distribution']
    rating_data = [["Rating", "Count", "Percentage"]]
    total = insights['total_reviews']
    for stars in range(5, 0, -1):
        count = rating_dist.get(stars, 0)
        pct = (count / total * 100) if total > 0 else 0
        rating_data.append([f"{stars} Stars", str(count), f"{pct:.1f}%"])
    
    rating_table = Table(rating_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
    rating_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ]))
    elements.append(rating_table)
    elements.append(Spacer(1, 15))
    
    # Sentiment Distribution
    elements.append(Paragraph("Sentiment Analysis", heading_style))
    
    sent_dist = insights['sentiment_distribution']
    sentiment_data = [
        ["Sentiment", "Count", "Percentage"],
        ["Positive", str(sent_dist['positive']), f"{sent_dist['positive_percent']:.1f}%"],
        ["Neutral", str(sent_dist['neutral']), f"{sent_dist['neutral_percent']:.1f}%"],
        ["Negative", str(sent_dist['negative']), f"{sent_dist['negative_percent']:.1f}%"],
    ]
    
    sent_table = Table(sentiment_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
    sent_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#d4edda')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fff3cd')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#f8d7da')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    elements.append(sent_table)
    elements.append(Spacer(1, 15))
    
    # Common Keywords
    elements.append(Paragraph("Key Findings", heading_style))
    
    praises = insights.get('common_praises', [])[:5]
    complaints = insights.get('common_complaints', [])[:5]
    
    if praises:
        elements.append(Paragraph(f"<b>Common Praises:</b> {', '.join(praises)}", body_style))
    if complaints:
        elements.append(Paragraph(f"<b>Common Complaints:</b> {', '.join(complaints)}", body_style))
    
    elements.append(Spacer(1, 15))
    
    # Top Reviews
    if insights.get('top_positive_reviews'):
        elements.append(Paragraph("Top Positive Reviews", heading_style))
        for i, review in enumerate(insights['top_positive_reviews'][:3], 1):
            text = review['text'].replace('\n', ' ')
            if len(text) > 200:
                text = text[:197] + "..."
            elements.append(Paragraph(f"{i}. Rating {review['rating']}/5 - \"{text}\"", body_style))
    
    if insights.get('top_negative_reviews'):
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Top Negative Reviews", heading_style))
        for i, review in enumerate(insights['top_negative_reviews'][:3], 1):
            text = review['text'].replace('\n', ' ')
            if len(text) > 200:
                text = text[:197] + "..."
            elements.append(Paragraph(f"{i}. Rating {review['rating']}/5 - \"{text}\"", body_style))
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph(
        f"<i>Generated by E-commerce Review Analyzer on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer
