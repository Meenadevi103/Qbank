import json
import logging
from collections import defaultdict
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ai_analysis.models import ExtractedQuestion, SubjectAnalysisCache
from subjects.models import Subject

import re
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

# Lazy loading of sentence transformer model to avoid memory overhead when not needed
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # BAAI/bge-small-en-v1.5 is excellent, but all-MiniLM-L6-v2 is smaller and faster for basic tasks
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            raise ImportError("sentence-transformers is not installed.")
    return _model

def clean_question_text(text):
    """
    Strips out common section headers and exam instructions.
    """
    text = re.sub(r'(?i)(SECTION\s+[A-Z].*|Answer\s+(ALL|any).*questions?|Each\s+question\s+carries.*|P\.T\.O\.?|PART\s*-\s*[A-Z].*)', '', text)
    return text.strip()

def clean_instructional_phrases(text):
    """
    Removes common instructional prefixes and suffixes to extract core concept.
    """
    patterns = [
        r"(?i)\bwhat( is| are)?\b",
        r"(?i)\bhow( to| can)?\b",
        r"(?i)\bexplain\b",
        r"(?i)\bdiscuss\b",
        r"(?i)\bdescribe\b",
        r"(?i)\bstate\b",
        r"(?i)\bdefine\b",
        r"(?i)\bcompare\b",
        r"(?i)\bdifferentiate\b",
        r"(?i)\bimportance( of)?\b",
        r"(?i)\brelevance( of| in)?\b",
        r"(?i)\brole( of)?\b",
        r"(?i)\buse( of)?\b",
        r"(?i)\bwith( suitable)? example(s)?\b",
        r"(?i)\bin the context of\b",
        r"(?i)\bbriefly\b",
        r"(?i)\b(short )?note( on)?\b",
        r"(?i)\bwrite\b",
        r"(?i)\bdetail\b",
        r"(?i)\bconcept( of)?\b",
        r"(?i)\bmeaning( of)?\b",
        r"(?i)\bdo you mean by\b",
        r"(?i)\billustrate\b",
        r"(?i)\bgive\b",
        r"(?i)\bany\b",
        r"(?i)\bsuitable\b"
    ]
    cleaned = text
    for p in patterns:
        cleaned = re.sub(p, " ", cleaned)
    
    # Strip extra punctuation and spaces
    cleaned = re.sub(r"[^\w\s\-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def extract_topic_name(questions_texts):
    """
    Finds a concise, meaningful label by selecting the shortest cleaned question text.
    """
    cleaned_texts = [clean_instructional_phrases(q).strip() for q in questions_texts]
    # Filter out empty or 1-word texts if possible
    valid_texts = [q for q in cleaned_texts if len(q.split()) >= 1]
    
    if not valid_texts:
        valid_texts = questions_texts
        
    valid_texts.sort(key=len)
    best_candidate = valid_texts[0]
    
    # Capitalize first letter properly
    if len(best_candidate) > 0:
        best_candidate = best_candidate[0].upper() + best_candidate[1:]
        
    # Cap length to ~6 words
    words = best_candidate.split()
    if len(words) > 6:
        best_candidate = " ".join(words[:6]) + "..."
        
    return best_candidate

def perform_semantic_analysis(subject_id):
    """
    Performs semantic analysis on all ExtractedQuestions for a given subject.
    Returns the grouped topics, frequencies, and years.
    """
    subject = Subject.objects.get(id=subject_id)
    
    # 1. Fetch all questions for this subject
    questions = ExtractedQuestion.objects.filter(
        question_paper__subject=subject
    ).select_related('question_paper')
    
    if not questions.exists():
        analysis_data = {"groups": [], "total_papers": 0, "total_questions": 0}
        cache, _ = SubjectAnalysisCache.objects.get_or_create(subject=subject)
        # The old report may refer to a paper that has since been deleted.
        # Replace it with the current empty result rather than showing stale
        # questions from a removed paper.
        cache.results_json = analysis_data
        cache.is_stale = False
        cache.save(update_fields=['results_json', 'is_stale', 'last_computed'])
        return analysis_data
        
    # Gather distinct papers for stats
    papers = set(q.question_paper for q in questions)
    
    # Clean the texts for embedding, filtering out questions that are just generic instructions
    valid_questions = []
    texts = []
    for q in questions:
        cleaned_text = clean_question_text(q.question_text)
        # Check if the question has actual technical content beyond generic instructions
        stripped_concept = clean_instructional_phrases(cleaned_text).strip()
        if len(stripped_concept) >= 3:
            valid_questions.append(q)
            texts.append(cleaned_text)
            
    questions = valid_questions

    # Some PDFs contain only instructions or parser fragments.  In that case
    # there is nothing meaningful to embed; cache an empty valid result rather
    # than passing an empty list to sentence-transformers.
    if not questions:
        analysis_data = {
            "groups": [],
            "total_papers": len(papers),
            "total_questions": 0,
            "all_years": sorted(
                {str(p.academic_year) for p in papers}, reverse=True
            ),
        }
        cache, _ = SubjectAnalysisCache.objects.get_or_create(subject=subject)
        cache.results_json = analysis_data
        cache.is_stale = False
        cache.save(update_fields=['results_json', 'is_stale', 'last_computed'])
        return analysis_data
    
    # 2. Generate Embeddings
    model = get_embedding_model()
    embeddings = model.encode(texts)
    
    # 3. Compute Cosine Similarity
    sim_matrix = cosine_similarity(embeddings)
    
    # 4. Cluster the questions (Agglomerative Clustering)
    distance_matrix = 1 - sim_matrix
    np.fill_diagonal(distance_matrix, 0)
    
    if len(questions) == 1:
        labels = [0]
    else:
        clustering = AgglomerativeClustering(
            n_clusters=None, 
            metric='precomputed', 
            linkage='average',
            distance_threshold=0.15
        )
        labels = clustering.fit_predict(distance_matrix)
        
    # 5. Group by label
    groups = defaultdict(list)
    for idx, label in enumerate(labels):
        groups[label].append((questions[idx], texts[idx]))
        
    # 6. Format results for UI
    merged_groups = {}
    
    for label, group_items in groups.items():
        # group_items is a list of (ExtractedQuestion, cleaned_text)
        group_qs = [item[0] for item in group_items]
        group_texts = [item[1] for item in group_items]
        
        # Calculate distinct years
        years = [str(q.question_paper.academic_year) for q in group_qs]
        frequency = len(group_qs)
        
        # Extract Topic Name
        topic_name = extract_topic_name(group_texts)
        
        # Format related questions as dicts
        related_questions = []
        for q in group_qs:
            q_idx = questions.index(q)
            q_dict = {
                'id': q.id,
                'text': clean_question_text(q.question_text),
                'academic_year': q.question_paper.academic_year,
                'exam_type': q.question_paper.exam_type,
                'question_number': q.question_number,
                'part': q.part,
                'section': q.section,
                'marks': q.marks if q.marks else "Marks not available",
                'embedding_idx': q_idx,
                'question_paper_id': q.question_paper_id
            }
            related_questions.append(q_dict)
            
        if topic_name in merged_groups:
            merged_groups[topic_name]['frequency'] += frequency
            merged_groups[topic_name]['years'].extend(years)
            merged_groups[topic_name]['related_questions'].extend(related_questions)
        else:
            merged_groups[topic_name] = {
                'topic': topic_name,
                'frequency': frequency,
                'years': years,
                'related_questions': related_questions
            }
            
    result_groups = []
    for topic_name, group_data in merged_groups.items():
        group_data['years'] = sorted(list(set(group_data['years'])), reverse=True)
        
        # Calculate repetition type for each question in the merged group
        group_qs = group_data['related_questions']
        
        if len(group_qs) == 1:
            group_qs[0]['repetition_type'] = "Unique"
        else:
            for i, q1 in enumerate(group_qs):
                max_sim = 0
                idx1 = q1['embedding_idx']
                for j, q2 in enumerate(group_qs):
                    if i != j:
                        idx2 = q2['embedding_idx']
                        sim = sim_matrix[idx1][idx2]
                        if sim > max_sim:
                            max_sim = sim
                            
                if max_sim > 0.95:
                    q1['repetition_type'] = "Exact Repeat"
                elif max_sim > 0.85:
                    q1['repetition_type'] = "Near Repeat"
                else:
                    q1['repetition_type'] = "Same Concept"
                    
        # Remove embedding_idx before sending to UI
        for q in group_qs:
            q.pop('embedding_idx', None)
        
        # Calculate distinct papers
        paper_ids = set(q['question_paper_id'] for q in group_qs)
        group_data['distinct_papers'] = len(paper_ids)
        group_data['distinct_years'] = len(group_data['years'])
            
        result_groups.append(group_data)
        
    # Sort groups by frequency (highest first)
    result_groups.sort(key=lambda x: x['frequency'], reverse=True)
    
    analysis_data = {
        'total_papers': len(papers),
        'total_questions': len(questions),
        'groups': result_groups,
        'all_years': sorted(list(set(str(p.academic_year) for p in papers)), reverse=True)
    }
    
    # 7. Cache the results
    cache, created = SubjectAnalysisCache.objects.get_or_create(subject=subject)
    cache.results_json = analysis_data
    cache.is_stale = False
    cache.save()
    
    return analysis_data

def get_cached_analysis(subject_id):
    """
    Retrieves cached analysis. Returns None if no analysis exists.
    """
    subject = Subject.objects.get(id=subject_id)
    cache, created = SubjectAnalysisCache.objects.get_or_create(subject=subject)
    
    return cache.results_json
