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

def parse_questions_from_text(text, page_number=1, context=None, is_last_page=True):
    """
    Takes a raw text block (from a page) and parses out questions.
    Returns a list of dicts and the parsing context:
    ([questions], context)
    """
    if context is None:
        context = {
            'current_section': None,
            'section_mark': None,
            'current_q_num': None,
            'current_part': None,
            'current_q_section': None,
            'current_q_section_mark': None,
            'current_text': []
        }

    # Preprocess text to ensure ORs and subquestions on the same line are split
    text = re.sub(r'\s+\[?OR\]?\s+', '\nOR\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+(\(\s*[a-zA-Z]\s*\))\s+', r'\n\1 ', text)
    
    questions = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    current_q_num = context['current_q_num']
    current_part = context['current_part']
    current_text = context['current_text']
    
    current_section = context['current_section']
    section_mark = context['section_mark']
    
    current_q_section = context['current_q_section']
    current_q_section_mark = context['current_q_section_mark']
    
    def save_current_question():
        if current_text and (current_q_num or current_part):
            # Check if the last line is purely a number (likely right-aligned mark parsed as new line)
            last_line_mark = None
            if len(current_text) > 1 and re.match(r'^\(?\s*\d{1,2}\s*\)?$', current_text[-1].strip()):
                last_line_mark = re.sub(r'[^\d]', '', current_text.pop().strip())

            q_text = " ".join(current_text).strip()
            
            # Clean up leading numbers/parts from the text itself to avoid duplication
            clean_q_text = re.sub(r'^(?:Q\.?\s*)?\d+[\.\)\:]?\s*(?:\(\s*[a-zA-Z]\s*\))?\s*', '', q_text, flags=re.IGNORECASE)
            clean_q_text = re.sub(r'^\(\s*[a-zA-Z]\s*\)\s*', '', clean_q_text, flags=re.IGNORECASE)
            clean_q_text = re.sub(r'^[a-zA-Z]\)\s*', '', clean_q_text, flags=re.IGNORECASE)
            
            # Extract marks using a more robust pattern
            # Matches: [10], (10), 10 marks, [10 marks], (10M), etc.
            marks_pattern = r'\[\s*(\d{1,2})\s*(?:marks?|m|M)?\s*\]|\(\s*(\d{1,2})\s*(?:marks?|m|M)?\s*\)|\b(\d{1,2})\s*(?:marks?|M)\b|\[\s*(\d+\s*[xX*]\s*\d+\s*=\s*\d+)\s*\]'
            marks_match = re.search(marks_pattern, clean_q_text, flags=re.IGNORECASE)
            
            extracted_marks = None
            if marks_match:
                extracted_marks = next((m for m in marks_match.groups() if m is not None), None)
            elif last_line_mark:
                extracted_marks = last_line_mark
            elif current_q_section_mark:
                extracted_marks = current_q_section_mark
            
            # Clean up matched marks from the text
            clean_q_text = re.sub(marks_pattern, '', clean_q_text, flags=re.IGNORECASE).strip()
            
            if len(clean_q_text) > 10:  # Minimum length for a valid question
                questions.append({
                    'page_number': page_number,
                    'question_number': current_q_num or "Unknown",
                    'part': current_part,
                    'section': current_q_section,
                    'question_text': clean_q_text,
                    'raw_text_block': q_text,
                    'marks': extracted_marks
                })
    
    for line in lines:
        # 1. Check for section headers (e.g., "SECTION A", "PART - B", "Module 1")
        sec_match = re.match(r'(?i)^(?:section|part|module)[\s\-]*([a-z0-9]+)', line)
        is_sec_header = bool(sec_match)
        if is_sec_header:
            current_section = sec_match.group(1).upper()
            
        # 2. Check if it's an instructional line
        is_instruction = bool(re.match(r'(?i)^(?:answer|attempt|note:?)\s+(?:all|any|the following)', line))
            
        # 3. Check for section marks in this line
        # Only update section_mark if it's a header, instruction, or a short line
        if is_sec_header or is_instruction or len(line) < 60:
            sm_match = re.search(r'(?i)[a-z]{0,2}ach\s+(?:question\s+)?carries\s+(\d+)\s+marks?', line)
            if not sm_match:
                sm_match = re.search(r'(\d+)\s*[xX*]\s*(\d+)\s*=\s*\d+', line)
                if sm_match:
                    section_mark = sm_match.group(2)
            else:
                section_mark = sm_match.group(1)
                
        # 4. Skip further processing if it's a header or instruction
        if is_sec_header or is_instruction:
            continue
            
        is_q, q_num, part = is_question_start(line)
        
        if is_q and q_num:
            # We hit a new main question. Save the previous one.
            save_current_question()
            current_q_num = q_num
            current_part = part
            current_text = [line]
            current_q_section = current_section
            current_q_section_mark = section_mark
        elif is_q and part:
            # It's a subpart.
            save_current_question()
            current_part = part
            current_text = [line]
            current_q_section = current_section
            current_q_section_mark = section_mark
        else:
            # Check if this line is an OR separator
            if re.match(r'^\[?OR\]?$', line, re.IGNORECASE):
                continue
                
            # Accumulate text for the current question
            if current_q_num or current_part:
                current_text.append(line)
                
    # Save the last question only if this is the last page
    if is_last_page:
        save_current_question()
        current_text = []
    
    context.update({
        'current_section': current_section,
        'section_mark': section_mark,
        'current_q_num': current_q_num,
        'current_part': current_part,
        'current_q_section': current_q_section,
        'current_q_section_mark': current_q_section_mark,
        'current_text': current_text
    })
    
    return questions, context
