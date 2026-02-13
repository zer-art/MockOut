import yaml
import re

def fix_math_format(text):
    if not isinstance(text, str):
        return text
    # Generic n power
    text = re.sub(r'\b([a-zA-Z0-9]+)\s+2\b', r'$\1^2$', text)
    text = re.sub(r'\b([a-zA-Z0-9]+)\s+n\b', r'$\1^n$', text)

    text = text.replace("2 n", "$2^n$")
    text = text.replace("n 2", "$n^2$")
    
    # Fix sets
    text = text.replace("A '", "$A'$")
    text = text.replace("B '", "$B'$")
    text = text.replace("U ", "$\cup$ ")
    
    return text

def process_file(filename):
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)
        
    if 'math' in data:
        for q in data['math']:
            q['question'] = fix_math_format(q['question'])
            q['options'] = [fix_math_format(opt) for opt in q['options']]
            q['answer'] = fix_math_format(q['answer'])
            
    with open(filename, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

def parse_markdown_questions(content):
    questions = []
    # Split by "Question X"
    # Note: Qtemp.md has "Question 1", "Question 2" etc.
    raw_blocks = re.split(r'Question \d+', content)
    
    # Skips the first split if it's empty (before Question 1)
    if raw_blocks and not raw_blocks[0].strip():
        raw_blocks = raw_blocks[1:]
        
    for i, block in enumerate(raw_blocks):
        block = block.strip()
        if not block:
            continue
            
        # Specific cleanup for Qtemp.md text
        # Remove "Options:" if present
        block = block.replace("Options:", "")
        
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        # Identify answer index if marked with +1 or +4
        answer_idx = -1
        valid_lines = []
        
        # Filter out score lines but keep track of where they were to find answer
        for idx, line in enumerate(lines):
            if re.match(r'^\+\d+$', line):
                # This marker likely applies to the PREVIOUS line being the answer
                # identifying which option that was
                # We need to count how many options we have seen so far?
                # Actually, simpler: just tag the previous valid line as answer
                if valid_lines:
                    # The last added valid line is the answer
                    # We will mark it later
                    # Store the content of the answer
                    answer_content = valid_lines[-1]
            else:
                valid_lines.append(line)
        
        # Heuristic: Last 4 lines are options
        if len(valid_lines) >= 5:
            options = valid_lines[-4:]
            question_lines = valid_lines[:-4]
        else:
            # Fallback
            options = []
            question_lines = valid_lines

        # Format question lines
        formatted_q_lines = []
        for line in question_lines:
            # Check for match patterns like "(A) ..." or "(a) ..." or "(i) ..."
            # We want to ensure they start on a new line and are treated as list items
            # Typical patterns in Qtemp: "(A)", "(B)", etc.
            if re.match(r'^\s*\(?[A-Za-z0-9]+\)[\s\.]', line):
                 # It's a list item. Prepend explicit newline and bullet if not already
                 formatted_q_lines.append(f"\n- {line}")
            else:
                 formatted_q_lines.append(line)
        
        question_text = "\n".join(formatted_q_lines)
            
        # Clean question text
        question_text = re.sub(r'^\s*[\r\n]+', '', question_text)
        
        # Determine answer string
        final_answer = ""
        # scan original block for the answer marker again to match with options
        # or use logic above?
        # Let's try to match options with lines followed by +1
        
        for opt in options:
            # specific check if this option was followed by +1 in the original non-filtered lines
            # This is tricky because duplicates.
            # Let's search in the original block context
            # regex: option_text \s+ \+\d
            escaped_opt = re.escape(opt)
            if re.search(f"{escaped_opt}\s*\n\s*\+\d", block):
                final_answer = opt
                break
        
        questions.append({
            "question": question_text,
            "options": options,
            "answer": final_answer
        })
        
    return questions

if __name__ == "__main__":
    process_file("questions.yaml")
