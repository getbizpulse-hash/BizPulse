from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import io
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# --- VISUAL CONSTANTS ---
BRAND_PRIMARY = colors.HexColor("#0D5e37")  # Deep Green
TEXT_HEADING = colors.HexColor("#202124")
TEXT_BODY = colors.HexColor("#3C4043")
TEXT_SUBTLE = colors.HexColor("#5F6368")
BG_LIGHT = colors.HexColor("#F8F9FA")
BORDER_COLOR = colors.HexColor("#E8EAED")

# --- PLOTTING HELPERS ---
def get_plot_style():
    # Use seaborn-v0_8-whitegrid for matplotlib 3.6+ compatibility
    # Falls back to default if style not available
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except:
        plt.style.use('default')
    
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 10,
        'axes.titleweight': 'bold',
        'axes.titlesize': 12,
        'axes.labelsize': 9,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.spines.left': False,
        'axes.edgecolor': '#E0E0E0',
        'axes.facecolor': 'white',
        'axes.grid': True,
        'grid.color': '#F0F0F0',
        'grid.linestyle': '-',
        'grid.linewidth': 0.5,
        'text.color': '#333333',
    })

def create_health_donut(score, status_label):
    get_plot_style()
    fig, ax = plt.subplots(figsize=(4, 4))
    sizes = [score, 100 - score]
    colors_list = ['#0D5e37', '#E0E0E0']
    
    wedges, texts = ax.pie(sizes, colors=colors_list, startangle=90, counterclock=False, 
                           wedgeprops=dict(width=0.3, edgecolor='white'))
    ax.axis('equal')
    ax.text(0, 0.1, f"{int(score)}", ha='center', va='center', fontsize=40, fontweight='bold', color='#0D5e37')
    ax.text(0, -0.25, status_label, ha='center', va='center', fontsize=11, color='#666666')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf

def create_segment_chart(customer_df, context):
    """Conditional chart generation based on data quality."""
    get_plot_style()
    if 'segment' not in customer_df.columns: return None
    
    use_count = not context['has_revenue']
    
    if use_count:
        data = customer_df['segment'].value_counts().sort_values(ascending=True)
        title = 'Customer Distribution'
        color = '#5F6368'
    else:
        data = customer_df.groupby('segment')['total_spend'].sum().sort_values(ascending=True)
        title = 'Revenue Contribution'
        color = '#0D5e37'

    if len(data) < 2: return None

    fig, ax = plt.subplots(figsize=(6, 3))
    bars = ax.barh(data.index, data.values, color=color, alpha=0.9, height=0.6)
    
    for bar in bars:
        width = bar.get_width()
        if width > 0:
            label = f' {int(width)}' if use_count else f' ${width:,.0f}'
            ax.text(width * 1.02, bar.get_y() + bar.get_height()/2, 
                    label, ha='left', va='center', fontsize=9, color='#666666')
                
    ax.set_title(title, fontsize=12, loc='left', pad=15)
    ax.grid(axis='y', alpha=0) 
    ax.grid(axis='x', alpha=0.3)
    ax.set_xlabel("")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf

def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(TEXT_SUBTLE)
    page_num = canvas.getPageNumber()
    canvas.setStrokeColor(BORDER_COLOR)
    canvas.line(60, 50, LETTER[0]-60, 50)
    canvas.drawRightString(LETTER[0]-60, 35, f"Page {page_num}")
    
    # Credibility Footer (No "AI" or "Engine")
    canvas.drawString(60, 35, "Prepared by BizPulse")
    canvas.restoreState()

# --- DIAGNOSTIC LOGIC (The Brain) ---

def diagnose_business_state(health_score, customer_df, top_actions):
    """
    PASS 1: Diagnose the business context with calibrated tone.
    """
    ctx = {
        'theme': 'Neutral',
        'headline': '',
        'situation_narrative': '',
        'top_priority_label': 'Optimization',
        'has_revenue': False,
        'dominant_segment': None,
        'segment_insight': '',
        'show_segmentation': False
    }

    # Data Hygiene
    total_rev = customer_df['total_spend'].sum() if 'total_spend' in customer_df.columns else 0
    ctx['has_revenue'] = total_rev > 100 
    
    score = health_score.get('score', 0)
    retention_status = health_score.get('retention', {}).get('status', 'Neutral')
    
    # 3. Determine Dominant Theme (Corrected Tone)
    if score < 50:
        ctx['theme'] = 'Turnaround'
        ctx['headline'] = "Priority: Stabilize retention in the near term to protect revenue."
        ctx['situation_narrative'] = "The overall health score reflects fragile stability. Customer return rates are below the viable baseline."
        ctx['top_priority_label'] = "Retention"
    elif retention_status == 'Fair' or retention_status == 'Needs Attention':
        ctx['theme'] = 'Retention Risk'
        ctx['headline'] = "Priority: Correct retention trends to safeguard the base."
        ctx['situation_narrative'] = "While the business is operational, underlying churn is eroding value. Growth is effectively capped until this is resolved."
        ctx['top_priority_label'] = "Retention"
    elif score > 75:
        ctx['theme'] = 'Growth'
        ctx['headline'] = "Focus: Capitalize on strong loyalty to drive expansion."
        ctx['situation_narrative'] = "The business has a rock-solid foundation. The primary opportunity is now aggressive expansion or share-of-wallet increase."
        ctx['top_priority_label'] = "Growth"
    else:
        ctx['theme'] = 'Stable/Stagnant'
        ctx['headline'] = "Focus: Unlock growth from a stable but static base."
        ctx['situation_narrative'] = "The business is stable but may be drifting. Performance is consistent, but lacks upward momentum."
        ctx['top_priority_label'] = "Optimization"

    # 4. Segment Diagnosis
    if 'segment' in customer_df.columns:
        seg_counts = customer_df['segment'].value_counts()
        if len(seg_counts) > 1:
            ctx['show_segmentation'] = True
            biggest_seg = seg_counts.idxmax()
            ctx['dominant_segment'] = biggest_seg
            
            # Insight Logic
            if biggest_seg in ['Explorer', 'Casual']:
                ctx['segment_insight'] = f"Volume is driven by {biggest_seg}s, who are low-frequency. Revenue is vulnerable to their churn."
            elif biggest_seg == 'Loyal':
                ctx['segment_insight'] = "Revenue is highly concentrated in Loyalists. Use them as a blueprint for acquisition."
            else:
                ctx['segment_insight'] = f"Customer base is heavily weighted toward {biggest_seg}s."
    
    return ctx

def create_bizpulse_report(buffer, business_name, health_score, top_actions, customer_df):
    
    # --- PASS 1: DIAGNOSE ---
    context = diagnose_business_state(health_score, customer_df, top_actions)
    
    # --- PASS 2: COMMUNICATE ---
    doc = SimpleDocTemplate(buffer, pagesize=LETTER,
                            rightMargin=60, leftMargin=60,
                            topMargin=60, bottomMargin=60,
                            title=f"BizPulse Executive Report - {business_name}",
                            author="BizPulse",
                            subject="Strategic Business Analysis",
                            creator="BizPulse Strategy")
    
    styles = getSampleStyleSheet()
    story = []

    # Styles
    style_headline = ParagraphStyle('Headline', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=TEXT_HEADING, spaceAfter=20)
    style_section_header = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=BRAND_PRIMARY, spaceBefore=24, spaceAfter=12)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10.5, leading=15, textColor=TEXT_BODY, spaceAfter=8)
    style_takeaway = ParagraphStyle('Takeaway', parent=style_body, fontSize=12, leading=18, leftIndent=12, spaceAfter=12)
    style_subtle = ParagraphStyle('Subtle', parent=style_body, fontSize=9, textColor=TEXT_SUBTLE)

    # --- PAGE 1: EXECUTIVE BRIEF ---
    story.append(Paragraph("Executive Business Brief", style_section_header))
    story.append(Paragraph(f"{business_name} • {datetime.now().strftime('%B %d, %Y')}", style_subtle))
    story.append(Spacer(1, 20))
    
    # Dynamic Headline
    story.append(Paragraph(f"{business_name} {context['headline']}", style_headline))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Key Takeaways", style_section_header))
    takeaways = []
    
    # T1: Health Summary
    score_val = health_score.get('score', 0)
    status_display = "Below Target" if health_score.get('status_label') == "Needs Attention" else health_score.get('status_label', 'Neutral')
    takeaways.append(f"• Overall health is <b>{status_display}</b> ({int(score_val)}/100). {context['theme']} context.")
    
    # T2: Segment Insight (Conditional)
    if context['show_segmentation']:
        takeaways.append(f"• <b>Segmentation:</b> {context['segment_insight']}")
    
    # T3: Top Action
    if top_actions:
        takeaways.append(f"• <b>Priority:</b> {top_actions[0]['title']} offers the highest impact.")
        
    for t in takeaways:
        story.append(Paragraph(t, style_takeaway))
    story.append(Spacer(1, 20))
    
    # Strategic Priorities
    story.append(Paragraph("Strategic Priorities", style_section_header))
    action_data = [] 
    for i, action in enumerate(top_actions):
        clean_impact = action['impact_value']
        # Hygiene
        if "$" in str(clean_impact) and "0" in str(clean_impact) and len(str(clean_impact)) < 5:
            clean_impact = "Protects Future Revenue"
        
        action_data.append([
            f"{i+1}", 
            Paragraph(f"<b>{action['title']}</b>", style_body),
            Paragraph(f"{clean_impact}<br/><font color='#666666' size=8>{action['effort']} Effort</font>", style_body)
        ])
    t_actions = Table(action_data, colWidths=[0.3*inch, 4*inch, 2*inch])
    t_actions.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_COLOR),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), BRAND_PRIMARY),
    ]))
    story.append(t_actions)
    story.append(PageBreak())

    # --- PAGE 2: SITUATION ANALYSIS ---
    story.append(Paragraph("Situation Analysis", style_headline))
    story.append(Paragraph("Why is this the priority?", style_section_header))
    
    story.append(Paragraph(f"Score: <b>{int(score_val)}</b>. {context['situation_narrative']}", style_body))
    story.append(Spacer(1, 12))
    
    donut_buf = create_health_donut(score_val, status_display)
    story.append(Image(donut_buf, width=3*inch, height=3*inch))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Driver Analysis", style_section_header))
    driver_text = "The score is a composite of signals."
    if context['theme'] == 'Turnaround' or context['theme'] == 'Retention Risk':
        driver_text = "<b>Churn is the primary drag.</b> Recent patterns suggest customer frequency is decaying faster than acquisition can replenish it."
    elif context['theme'] == 'Growth':
        driver_text = "<b>Retention is an asset.</b> Unlike many peers, you are not losing customers. This capital efficiency means every marketing dollar works harder."
    
    story.append(Paragraph(driver_text, style_body))
    story.append(PageBreak())

    # --- PAGE 3: SEGMENTATION (CONDITIONAL) ---
    if context['show_segmentation']:
        story.append(Paragraph("Customer Dynamics", style_headline))
        
        story.append(Paragraph(context['segment_insight'], style_takeaway))
        story.append(Spacer(1, 12))
        
        seg_chart_buf = create_segment_chart(customer_df, context)
        if seg_chart_buf:
            story.append(Image(seg_chart_buf, width=6*inch, height=3*inch))
        story.append(Spacer(1, 12))
        
        # Table
        seg_counts = customer_df['segment'].value_counts()
        seg_rev = customer_df.groupby('segment')['total_spend'].sum() if context['has_revenue'] else None
        
        header_row = ['Segment', 'Role', 'Active Count']
        if context['has_revenue']: header_row.append('Rev Share')
        else: header_row.append('Avg Visits')
        data_rows = [header_row]
        
        for seg in seg_counts.index:
            count = seg_counts.get(seg, 0)
            
            # Contextual Role descriptions (Generalized)
            role = "Core Base"
            if seg == 'Loyal': role = "Key Asset / High Value"
            elif seg == 'At-Risk': role = "Churn Risk / Protection Needed"
            elif seg == 'Explorer': role = "Low Frequency / Growth Target" # Generalized from Upsell
            
            row = [
                seg,
                Paragraph(role, style_subtle),
                f"{count}"
            ]
            if context['has_revenue']:
                rev = seg_rev.get(seg, 0)
                total = seg_rev.sum()
                pct = (rev / total) if total > 0 else 0
                row.append(f"{pct:.0%}")
            else:
                 visits = customer_df[customer_df['segment']==seg]['frequency'].mean()
                 row.append(f"{visits:.1f}")
            data_rows.append(row)
            
        t_seg = Table(data_rows, colWidths=[1.2*inch, 2.5*inch, 1.3*inch, 1.2*inch])
        t_seg.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (0, -1), TEXT_HEADING),
        ]))
        story.append(t_seg)
        story.append(PageBreak())

    # --- PAGE 4: PLAYBOOK ---
    story.append(Paragraph("Action Playbook", style_headline))
    story.append(Paragraph("Execution plan for the next quarter.", style_body))
    story.append(Spacer(1, 24))
    
    # Standardized Horizons
    horizons = ["in the next 30 days", "over the upcoming quarter", "as an ongoing priority"]
    
    for i, action in enumerate(top_actions):
        clean_impact = action['impact_value']
        if "$" in str(clean_impact) and "0" in str(clean_impact) and len(str(clean_impact)) < 5:
             clean_impact = "Protects Future Revenue"
        
        target = "All customers"
        approach = "General marketing"
        time_frame = horizons[i % len(horizons)] 
        
        priority_label = "Priority"
        
        # Adaptive Language
        title = action['title']
        if "At-Risk" in title:
            target = "Customers inactive for 45+ days"
            approach = f"Targeted outreach via email/SMS {time_frame}."
            priority_label = "Defensive Move"
        elif "loss" in title:
            target = "High-value customers showing usage decay"
            approach = f"Personalized appreciation offer {time_frame}."
            priority_label = "Retention Move"
        elif "Upgrade" in title:
            target = "Frequent visitors with average spend"
            approach = f"Exclusive membership invitation {time_frame}."
            priority_label = "Growth Move"
        
        story.append(Paragraph(f"{priority_label} #{i+1}: {title}", style_section_header))
        playbook_data = [
            [Paragraph("<b>Who to target</b>", style_body), Paragraph(target, style_body)],
            [Paragraph("<b>Why it matters</b>", style_body), Paragraph(f"Estimated Impact: {clean_impact}", style_body)],
            [Paragraph("<b>What to do</b>", style_body), Paragraph(approach, style_body)]
        ]
        t_play = Table(playbook_data, colWidths=[1.5*inch, 4.5*inch])
        t_play.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (0, 0), (0, -1), BG_LIGHT),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(t_play)
        story.append(Spacer(1, 20))

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
