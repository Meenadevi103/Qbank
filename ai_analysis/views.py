from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from .analyzer import get_cached_analysis
from papers.models import QuestionPaper
from ai_analysis.models import ExtractionStatus, SubjectAnalysisCache
from subjects.models import Subject

import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def analyze_subject(request, subject_id):
    """
    AJAX endpoint to fetch precomputed semantic analysis for a subject.
    Returns rendered HTML snippet to be injected into the page.
    """
    try:
        force = request.GET.get('force', 'false').lower() == 'true'

        # 1. Get ALL QuestionPapers for this subject
        papers = QuestionPaper.objects.filter(subject_id=subject_id)

        # 2. Create any missing statuses and optionally requeue failures.
        for paper in papers:
            status, created = ExtractionStatus.objects.get_or_create(
                question_paper=paper,
                defaults={'status': 'PENDING'}
            )
            
            # Allow retry of FAILED jobs via force reload
            if force and status.status == 'FAILED':
                status.status = 'PENDING'
                status.save()

        # 3. Ensure every subject has a cache job.  This also repairs older
        # subjects that were uploaded before the automatic queue existed.
        cache, _ = SubjectAnalysisCache.objects.get_or_create(subject_id=subject_id)
        if not cache.results_json and not cache.is_stale:
            cache.is_stale = True
            cache.save(update_fields=['is_stale'])
        # 4. Fetch the currently cached data (if any)
        analysis_data = get_cached_analysis(subject_id)

        # A pending paper must not prevent students from viewing analysis of
        # papers which have already completed.  Deleted-paper signals clear
        # the cache, so stale data cannot be returned for removed papers.
        if not analysis_data:
            return render(request, 'ai_analysis/partials/processing_status.html')

        # Do not show a processing banner to students for a separate queued
        # paper; the cached report remains useful until the worker refreshes it.
        return render(request, 'ai_analysis/partials/analysis_results.html', {
            'data': analysis_data,
            'update_in_progress': False,
            'subject_id': subject_id,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

def download_report(request, subject_id):
    """
    Generates and downloads a PDF report of the semantic analysis.
    """
    subject = get_object_or_404(Subject, pk=subject_id)
    analysis_data = get_cached_analysis(subject_id)
    
    if not analysis_data or not analysis_data.get('groups'):
        return HttpResponse("No valid analysis data available for this subject.", status=404)
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # PDF Elements
    elements = []
    
    # Title
    elements.append(Paragraph(f"Analysis Report: {subject.name}", title_style))
    elements.append(Spacer(1, 12))
    if subject.code:
        elements.append(Paragraph(f"Subject Code: {subject.code}", normal_style))
        elements.append(Spacer(1, 12))
        
    elements.append(Paragraph(f"Total Papers Analyzed: {analysis_data['total_papers']}", normal_style))
    elements.append(Paragraph(f"Total Questions Analyzed: {analysis_data['total_questions']}", normal_style))
    elements.append(Spacer(1, 24))
    
    for group in analysis_data['groups']:
        elements.append(Paragraph(f"Topic: {group['topic']}", heading_style))
        stats_text = (
            f"Total Occurrences: {group['frequency']} | "
            f"Distinct Papers: {group.get('distinct_papers', 0)} | "
            f"Distinct Years: {group.get('distinct_years', len(group['years']))}<br/>"
            f"Observed in Academic Years: {', '.join(group['years'])}"
        )
        elements.append(Paragraph(stats_text, normal_style))
        elements.append(Spacer(1, 12))
        
        # Build table data
        table_data = [['Year', 'Question', 'Section', 'Type', 'Marks']]
        for q in group['related_questions']:
            q_text = Paragraph(q['text'], normal_style)
            year_text = Paragraph(f"{q['academic_year']}<br/><font size=8>Q{q['question_number']}{'('+q['part']+')' if q['part'] else ''}</font>", normal_style)
            section_text = Paragraph(q.get('section') or '-', normal_style)
            rep_type = Paragraph(q.get('repetition_type', 'Unique'), normal_style)
            marks = Paragraph(q.get('marks', 'N/A'), normal_style)
            table_data.append([year_text, q_text, section_text, rep_type, marks])
            
        t = Table(table_data, colWidths=[50, 240, 40, 80, 102], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(t)
        elements.append(Spacer(1, 24))
        
    doc.build(elements)
    buffer.seek(0)
    
    response = FileResponse(buffer, as_attachment=True, filename=f"analysis_{subject.code or subject.id}.pdf")
    return response
