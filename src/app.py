import streamlit as st
import yaml
import random
import time
import streamlit.components.v1 as components

# --- Constants ---
QUESTIONS_FILE = "questions.yaml"
TOTAL_TIME_MINUTES = 90
CS_COUNT = 36
MATH_COUNT = 24
LR_COUNT = 15

# --- Custom CSS ---
def local_css():
    st.markdown("""
    <style>
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
        }
        .question-card {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #ddd;
            margin-bottom: 20px;
        }
        .question-text {
            font-size: 1.2em;
            font-weight: 500;
            margin-bottom: 10px;
        }
        .category-tag {
            background-color: #e0f7fa;
            color: #006064;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            display: inline-block;
            margin-bottom: 10px;
        }
        .timer-box {
            font-size: 24px; 
            font-weight: bold; 
            color: #31333F; 
            text-align: center; 
            padding: 10px; 
            border: 2px solid #4F8BF9; 
            border-radius: 5px;
            background-color: #f0f8ff;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- functions ---
def load_questions():
    """Loads questions from the YAML file."""
    try:
        with open(QUESTIONS_FILE, "r") as f:
            data = yaml.safe_load(f)
        return data
    except FileNotFoundError:
        st.error(f"File not found: {QUESTIONS_FILE}")
        return None
    except yaml.YAMLError as e:
        st.error(f"Error parsing YAML: {e}")
        return None

def select_questions(all_questions):
    """Randomly selects questions based on category counts."""
    selected = []
    
    def sample_safe(questions, count, category_name):
        if not questions:
            return []
        if len(questions) < count:
            return questions 
        return random.sample(questions, count)

    if 'cs' in all_questions:
        cs_qs = sample_safe(all_questions['cs'], CS_COUNT, "Computer Science")
        for q in cs_qs: q['category'] = 'Computer Science'
        selected.extend(cs_qs)
        
    if 'math' in all_questions:
        math_qs = sample_safe(all_questions['math'], MATH_COUNT, "Mathematics")
        for q in math_qs: q['category'] = 'Mathematics'
        selected.extend(math_qs)

    if 'logical_reasoning' in all_questions:
        lr_qs = sample_safe(all_questions['logical_reasoning'], LR_COUNT, "Logical Reasoning")
        for q in lr_qs: q['category'] = 'Logical Reasoning'
        selected.extend(lr_qs)

    random.shuffle(selected)
    return selected

def initialize_session_state():
    """Initializes session state variables."""
    if 'exam_started' not in st.session_state:
        st.session_state.exam_started = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'time_spent' not in st.session_state:
        st.session_state.time_spent = {} # Map question index to total seconds
    if 'current_q_index' not in st.session_state:
        st.session_state.current_q_index = 0
    if 'q_start_time' not in st.session_state:
        st.session_state.q_start_time = None
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

def update_time_spent():
    """Updates the time spent on the current question."""
    if st.session_state.q_start_time is not None:
        elapsed = time.time() - st.session_state.q_start_time
        idx = st.session_state.current_q_index
        st.session_state.time_spent[idx] = st.session_state.time_spent.get(idx, 0) + elapsed

def navigate_to(index):
    """Navigates to the specific question index."""
    update_time_spent() # Save time for current question
    st.session_state.current_q_index = index
    st.session_state.q_start_time = time.time() # Reset start time for new question
    st.rerun()

def start_exam():
    all_qs = load_questions()
    if all_qs:
        st.session_state.questions = select_questions(all_qs)
        st.session_state.exam_started = True
        st.session_state.start_time = time.time()
        st.session_state.submitted = False
        st.session_state.user_answers = {}
        st.session_state.time_spent = {}
        st.session_state.current_q_index = 0
        st.session_state.q_start_time = time.time()
        st.rerun()

def submit_exam():
    update_time_spent() # Final time capture
    st.session_state.submitted = True
    st.session_state.exam_started = False 
    st.rerun()

def get_timer_html(remaining_seconds):
    """Generates HTML/JS for the sidebar timer."""
    timer_id = f"timer_{int(time.time())}"
    
    js_code = f"""
    <div id="{timer_id}" class="timer-box">
        Loading...
    </div>
    <script>
        (function() {{
            var timeLeft = {int(remaining_seconds)};
            var timerElement = document.getElementById("{timer_id}");
            
            var countdown = setInterval(function() {{
                if (timeLeft <= 0) {{
                    clearInterval(countdown);
                    timerElement.innerHTML = "Time's Up!";
                }} else {{
                    var mins = Math.floor(timeLeft / 60);
                    var seconds = timeLeft % 60;
                    timerElement.innerHTML = mins.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0');
                    timeLeft -= 1;
                }}
            }}, 1000);
        }})();
    </script>
    """
    return js_code

# --- Main App ---
st.set_page_config(page_title="Mock Test App", page_icon="📝", layout="wide", initial_sidebar_state="expanded")
local_css()
initialize_session_state()

# --- Header ---
if not st.session_state.exam_started and not st.session_state.submitted:
    st.markdown("<h1 style='text-align: center; color: #4F8BF9;'>Mock Test Application</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>MCA Entrance Preparation</h3>", unsafe_allow_html=True)
else:
    st.title("Mock Test Application")


# --- Exam Phase ---
if st.session_state.exam_started and not st.session_state.submitted:
    
    # --- Sidebar ---
    with st.sidebar:
        st.markdown("### ⏳ Timer")
        # 1. Timer
        elapsed_global = time.time() - st.session_state.start_time
        remaining_seconds = max(0, (TOTAL_TIME_MINUTES * 60) - elapsed_global)
        
        if remaining_seconds <= 0:
            st.warning("Time is up!")
            submit_exam()
        else:
            components.html(get_timer_html(remaining_seconds), height=80)
            
        st.markdown("---")
        
        # 2. Question Palette
        st.markdown("### 🧭 Navigation")
        
        q_count = len(st.session_state.questions)
        
        # Pagination for palette if too many questions? No, single grid is better for overview
        with st.container(height=400):
            cols = st.columns(5) # 5 columns for buttons
            for i in range(q_count):
                with cols[i % 5]:
                    is_current = (i == st.session_state.current_q_index)
                    is_answered = (i in st.session_state.user_answers)
                    
                    label = f"{i+1}"
                    btn_type = "primary" if is_current else ("secondary" if not is_answered else "secondary") 
                    
                    # Style hack: If answered, maybe bold? Streamlit buttons are limited.
                    # We rely on 'primary' for current focus.
                    
                    if st.button(label, key=f"nav_{i}", type=btn_type, use_container_width=True):
                        navigate_to(i)
        
        st.markdown("---")
        if st.button("🚩 Submit Exam", type="primary", use_container_width=True):
            submit_exam()

    # --- Main Content ---
    if 0 <= st.session_state.current_q_index < len(st.session_state.questions):
        idx = st.session_state.current_q_index
        q = st.session_state.questions[idx]
        
        # Progress Bar
        progress = (len(st.session_state.user_answers) / len(st.session_state.questions))
        st.progress(progress, text=f"Progress: {len(st.session_state.user_answers)}/{len(st.session_state.questions)} answered")
        
        # Question Container
        with st.container():
            st.markdown(f"""
            <div class="question-card">
                <span class="category-tag">{q.get('category', 'General')}</span>
                <div class="question-text">Q{idx+1}. {q['question']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Answer Selection
        current_answer = st.session_state.user_answers.get(idx, None)
        
        selected_option = st.radio(
            "Select an answer:",
            q['options'],
            index=q['options'].index(current_answer) if current_answer in q['options'] else None,
            key=f"radio_{idx}",
            label_visibility="collapsed"
        )
        
        if selected_option:
            st.session_state.user_answers[idx] = selected_option
            
        st.markdown("---")
            
        # Navigation Buttons (Bottom)
        col_prev, col_spacer, col_next = st.columns([1, 2, 1])
        with col_prev:
            if idx > 0:
                if st.button("⬅ Previous", use_container_width=True):
                    navigate_to(idx - 1)
        with col_next:
            if idx < len(st.session_state.questions) - 1:
                if st.button("Next ➡", use_container_width=True):
                    navigate_to(idx + 1)
    else:
        st.error("Invalid question index.")

# --- Results Phase ---
elif st.session_state.submitted:
    st.balloons()
    st.success("Exam Submitted Successfully!")
    
    score = 0
    total = len(st.session_state.questions)
    
    # Initialize counters for each section
    sections = ["Computer Science", "Mathematics", "Logical Reasoning"]
    stats = {sec: {"correct": 0, "wrong": 0, "unattempted": 0, "score": 0, "time": 0.0} for sec in sections}
    total_score = 0
    total_correct = 0
    total_wrong = 0
    total_unattempted = 0

    # Calculate stats
    for i, q in enumerate(st.session_state.questions):
        user_ans = st.session_state.user_answers.get(i)
        correct_ans = q['answer']
        category = q.get('category', 'General')
        time_spent = st.session_state.time_spent.get(i, 0)
        
        if category in stats:
            stats[category]["time"] += time_spent
        
        if user_ans is None:
            total_unattempted += 1
            if category in stats: stats[category]["unattempted"] += 1
        elif user_ans == correct_ans:
            total_correct += 1
            if category in stats: stats[category]["correct"] += 1
            mark = 4
            total_score += mark
            if category in stats: stats[category]["score"] += mark
        else:
            total_wrong += 1
            if category in stats: stats[category]["wrong"] += 1
            mark = -1
            total_score += mark
            if category in stats: stats[category]["score"] += mark

    # Display Overall Summary
    st.markdown("## 📊 Performance Analysis")
    
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Score", f"{total_score}", delta=None)
        c2.metric("Total Correct", total_correct, delta_color="normal")
        c3.metric("Total Wrong", total_wrong, delta_color="inverse")
        c4.metric("Total Unattempted", total_unattempted, delta_color="off")
    
    st.markdown("---")
    
    # Display Section-wise Stats
    st.markdown("### 📑 Section-wise Breakdown")
    
    for sec in sections:
        with st.container():
            st.markdown(f"**{sec}**")
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            s_data = stats[sec]
            
            sc1.metric("Score", s_data["score"])
            sc2.metric("Correct", s_data["correct"], delta_color="normal")
            sc3.metric("Wrong", s_data["wrong"], delta_color="inverse")
            sc4.metric("Unattempted", s_data["unattempted"], delta_color="off")
            sc5.metric("Avg Time", f"{(s_data['time'] / max(1, (s_data['correct'] + s_data['wrong'] + s_data['unattempted']))):.1f}s")
            st.divider()

    # Detailed Analysis
    with st.expander("Show Detailed Question Analysis"):
        for i, q in enumerate(st.session_state.questions):
            user_ans = st.session_state.user_answers.get(i)
            correct_ans = q['answer']
            time_spent = st.session_state.time_spent.get(i, 0)
            
            is_correct = (user_ans == correct_ans)
            icon = "✅" if is_correct else "❌"
            
            st.markdown(f"**Q{i+1}: {q['question']}** {icon}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"- **Your Answer:** {user_ans if user_ans else 'No Answer'}")
                st.markdown(f"- **Correct Answer:** {correct_ans}")
            with c2:
                st.markdown(f"- **Time Spent:** {time_spent:.1f}s")
                st.caption(f"Category: {q.get('category')}")
            st.divider()

    if st.button("🔄 Retake Exam", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- Start Screen ---
else:
    with st.container():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100) # Placeholder logo
            st.markdown("## Instructions")
            st.info(f"""
            - **Duration:** {TOTAL_TIME_MINUTES} Minutes
            - **Total Questions:** {CS_COUNT + MATH_COUNT + LR_COUNT}
            - **Marking Scheme:** +4 for Correct, -1 for Incorrect
            """)
            
            st.markdown("### Subject Distribution")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Computer Science", CS_COUNT)
            col_b.metric("Mathematics", MATH_COUNT)
            col_c.metric("Logical Reasoning", LR_COUNT)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Start Exam", type="primary", use_container_width=True):
                start_exam()
