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
    Uses a KeyBERT-like approach to find the most representative phrase.
    """
    from sklearn.feature_extraction.text import CountVectorizer
    
    combined_text = " ".join(questions_texts)
    cleaned_text = clean_instructional_phrases(combined_text)
    
    if len(cleaned_text.split()) < 2:
        cleaned_text = combined_text
        
    try:
        vectorizer = CountVectorizer(ngram_range=(1, 3), stop_words='english')
        vectorizer.fit([cleaned_text])
        candidates = vectorizer.get_feature_names_out()
    except ValueError:
        return "General Concept"
        
    if len(candidates) == 0:
        return "General Concept"
        
    model = get_embedding_model()
    doc_embedding = model.encode([cleaned_text])
    candidate_embeddings = model.encode(candidates)
    
    distances = cosine_similarity(doc_embedding, candidate_embeddings)[0]
    
    # Penalize longer phrases significantly to prefer concise concepts
    best_score = -1
    best_topic = candidates[0]
    
    for i, candidate in enumerate(candidates):
        num_words = len(candidate.split())
        # Heavy penalty: 0.1 for bigrams, 0.2 for trigrams
        penalty = (num_words - 1) * 0.1
        score = distances[i] - penalty
        if score > best_score:
            best_score = score
            best_topic = candidate
            
    return best_topic.title().strip()

def perform_semantic_analysis(subject_id):
    """
    Performs semantic analysis on all ExtractedQuestions for a given subject.
    Returns the grouped topics, frequencies, and years.
    """
    subject = Subject.objects.get(id=subject_id)
    
    # 1. Fetch all questions for this subject
    questions = ExtractedQuestion.objects.filter(question_paper__subject=subject)
    
    if not questions.exists():
        return {"groups": [], "total_papers": 0, "total_questions": 0}
        
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
            distance_threshold=0.25
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
        
        # Format related questions
        related_questions = []
        for q in group_qs:
            q_str = f"{clean_question_text(q.question_text)}"
            if q.question_number:
                prefix = f"Q{q.question_number}"
                if q.part:
                    prefix += f" ({q.part})"
                q_str = f"[{q.question_paper.academic_year} - {prefix}] {q_str}"
            related_questions.append(q_str)
            
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
        
        # Priority
        if group_data['frequency'] >= 3:
            group_data['priority'] = "High Priority"
        elif group_data['frequency'] == 2:
            group_data['priority'] = "Important"
        else:
            group_data['priority'] = "Optional"
            
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

def get_or_compute_analysis(subject_id, force=False):
    """
    Retrieves cached analysis or computes it if missing/stale.
    """
    subject = Subject.objects.get(id=subject_id)
    cache, created = SubjectAnalysisCache.objects.get_or_create(subject=subject)
    
    if created or cache.is_stale or force or not cache.results_json:
        return perform_semantic_analysis(subject_id)
        
    return cache.results_json
