import re
import logging

logger = logging.getLogger(__name__)

def is_question_start(line):
    """
    Detects if a line looks like the start of a question.
    Matches: '1.', '1)', 'Q1.', '13 (a)', '13(a)', '1 ', '1:', '(a)'
    """
    # Exclude common non-question headers
    lower_line = line.lower().strip()
    ignore_starts = ['time', 'max', 'marks', 'register', 'section', 'part', 'college', 'university', 'b.tech', 'm.tech', 'bca', 'mca', 'bba', 'mba', 'b.com', 'm.com', 'page']
    if any(lower_line.startswith(ig) for ig in ignore_starts):
        return False, None, None

    # Regex to match Q1., 1., 1), 13 (a), 1
    # Groups:
    # 1. Question Number (e.g., '1', '13')
    # 2. Part (e.g., '(a)', 'a')
    
    # 1. Main questions with optional parts: "1.", "13 (a)", "Q1", "1 )"
    main_q_pattern = re.compile(r'^(?:Q\.?\s*)?(\d+)[\.\)\:]?\s*(?:\(\s*([a-zA-Z])\s*\))?', re.IGNORECASE)
    
    # 2. Sub-parts on their own line: "(a)", "a)"
    sub_q_pattern = re.compile(r'^\(\s*([a-zA-Z])\s*\)|^[a-zA-Z]\)', re.IGNORECASE)

    match = main_q_pattern.match(line)
    if match:
        q_num = match.group(1)
        part = match.group(2) if match.group(2) else None
        return True, q_num, part
        
    sub_match = sub_q_pattern.match(line)
    if sub_match:
        # A subpart without a main number (relies on previous main number context)
        part = sub_match.group(1)
        return True, None, part

    return False, None, None

def parse_questions_from_text(text, page_number=1):
    """
    Takes a raw text block (from a page) and parses out questions.
    Returns a list of dicts:
    [{
        'page_number': int,
        'question_number': str,
        'part': str or None,
        'question_text': str,
        'raw_text_block': str
    }]
    """
    questions = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    current_q_num = None
    current_part = None
    current_text = []
    
    def save_current_question():
        if current_text and (current_q_num or current_part):
            q_text = " ".join(current_text).strip()
            
            # Clean up leading numbers/parts from the text itself to avoid duplication
            # E.g., if text is "1. Explain...", remove "1. "
            # This is optional, but helps keep the text clean.
            clean_q_text = re.sub(r'^(?:Q\.?\s*)?\d+[\.\)\:]?\s*(?:\(\s*[a-zA-Z]\s*\))?\s*', '', q_text, flags=re.IGNORECASE)
            clean_q_text = re.sub(r'^\(\s*[a-zA-Z]\s*\)\s*', '', clean_q_text, flags=re.IGNORECASE)
            clean_q_text = re.sub(r'^[a-zA-Z]\)\s*', '', clean_q_text, flags=re.IGNORECASE)
            
            # Also clean up trailing marks like [10 marks]
            clean_q_text = re.sub(r'\[\d+\s*marks?\]|\(\d+\)|\[\d+\s*[xX*]\s*\d+\s*=\s*\d+\]', '', clean_q_text, flags=re.IGNORECASE).strip()
            
            if len(clean_q_text) > 10:  # Minimum length for a valid question
                questions.append({
                    'page_number': page_number,
                    'question_number': current_q_num or "Unknown",
                    'part': current_part,
                    'question_text': clean_q_text,
                    'raw_text_block': q_text
                })
    
    for line in lines:
        is_q, q_num, part = is_question_start(line)
        
        if is_q and q_num:
            # We hit a new main question. Save the previous one.
            save_current_question()
            current_q_num = q_num
            current_part = part
            current_text = [line]
        elif is_q and part and not current_q_num:
            # It's a subpart, but we have no main question context yet.
            # Treat it as a new question (e.g. paper only has a, b, c)
            save_current_question()
            current_part = part
            current_text = [line]
        else:
            # Check if this line is an OR separator
            if re.match(r'^\[?OR\]?$', line, re.IGNORECASE):
                continue
                
            # Accumulate text for the current question
            if current_q_num or current_part:
                current_text.append(line)
                
    # Save the last question
    save_current_question()
    
    return questions
