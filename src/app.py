import streamlit as st
import yaml
import random
import time
import re
import copy
import json
import streamlit.components.v1 as components

# --- Constants ---
QUESTIONS_FILE = "QuestionBank.yaml"
LOCAL_STORAGE_KEY = "mock_test_question_usage"
TOTAL_TIME_MINUTES = 90
CS_COUNT = 36
MATH_COUNT = 24
LR_COUNT = 15
MAX_USAGE_HISTORY = 50  # Keep track of last 50 question usages


# --- Custom CSS ---
def local_css():
    st.markdown(
        """
    <style>
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
        }
        .question-card {
            background-color: #f9f9f9;
            padding: 10px 20px;
            border-radius: 10px;
            border: 1px solid #ddd;
            margin-bottom: 10px;
        }
        .category-tag {
            background-color: #e0f7fa;
            color: #006064;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            display: inline-block;
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
    """,
        unsafe_allow_html=True,
    )


# --- functions ---
def init_usage_from_browser():
    """Initializes usage history from browser's localStorage on app start."""
    # Only run once per session
    if "usage_init_attempted" in st.session_state:
        return

    st.session_state.usage_init_attempted = True

    # JavaScript to read localStorage and store count for display
    js_code = f"""
    <script>
        (function() {{
            const storedData = localStorage.getItem('{LOCAL_STORAGE_KEY}');
            let count = 0;
            
            if (storedData) {{
                try {{
                    const parsed = JSON.parse(storedData);
                    const usageHistory = parsed.usage_history || [];
                    count = usageHistory.length;
                    
                    // Log for debugging
                    console.log('Loaded', count, 'question IDs from localStorage');
                }} catch (e) {{
                    console.error('Failed to parse usage history:', e);
                }}
            }}
        }})();
    </script>
    """

    components.html(js_code, height=0)


def load_question_usage():
    """Loads question usage history from browser localStorage."""
    # JavaScript that both loads from localStorage AND returns the data
    js_code = f"""
    <script>
        const storedData = localStorage.getItem('{LOCAL_STORAGE_KEY}');
        let usageHistory = [];
        
        if (storedData) {{
            try {{
                const parsed = JSON.parse(storedData);
                usageHistory = parsed.usage_history || [];
                console.log('Loaded', usageHistory.length, 'question IDs from localStorage for selection');
            }} catch (e) {{
                console.error('Failed to parse usage history:', e);
            }}
        }}
        
        // Make available globally for debugging
        window.currentUsageHistory = usageHistory;
    </script>
    <div id="usage-data" style="display:none">{{}}</div>
    """

    # Execute JS
    components.html(js_code, height=0)

    # Return from session cache (which gets populated by save_question_usage)
    # On first run, this will be empty, which is fine
    return st.session_state.get("usage_history_cache", [])


def save_question_usage(usage_history):
    """Saves question usage history to browser's localStorage using JavaScript."""
    # Update cache
    st.session_state.usage_history_cache = usage_history[:MAX_USAGE_HISTORY]

    # JavaScript to write to localStorage
    usage_json = json.dumps(usage_history[:MAX_USAGE_HISTORY])
    js_code = f"""
    <script>
        (function() {{
            const usageHistory = {usage_json};
            const data = {{
                usage_history: usageHistory,
                last_updated: new Date().toISOString()
            }};
            
            try {{
                localStorage.setItem('{LOCAL_STORAGE_KEY}', JSON.stringify(data));
                console.log('Saved', usageHistory.length, 'question IDs to localStorage');
            }} catch (e) {{
                console.error('Failed to save usage history:', e);
            }}
        }})();
    </script>
    """

    components.html(js_code, height=0)


def clear_usage_history():
    """Clears the question usage history from browser localStorage."""
    st.session_state.usage_history_cache = []
    st.session_state.usage_history_loaded = True

    js_code = f"""
    <script>
        (function() {{
            try {{
                localStorage.removeItem('{LOCAL_STORAGE_KEY}');
                console.log('Question usage history cleared from localStorage');
            }} catch (e) {{
                console.error('Failed to clear usage history:', e);
            }}
        }})();
    </script>
    """

    components.html(js_code, height=0)


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


def get_question_id(question):
    """Generate a unique ID for a question based on its content."""
    # Use first 50 chars of question as ID
    q_text = question.get("question", "")[:50]
    return hash(q_text)


def weighted_sample(questions, count, usage_history, max_history=5):
    """Sample questions WITHOUT replacement, with lower probability for recently used ones."""
    if not questions or count <= 0:
        return []

    if len(questions) <= count:
        return questions[:]

    # Calculate weights based on persistent usage history
    weights = []
    for q in questions:
        q_id = get_question_id(q)
        # Find how recently this question was used in the persistent history
        try:
            recent_index = usage_history.index(q_id)
            # More recent = lower weight (0.2 for most recent, gradually increases)
            weight = 0.2 + (recent_index / max_history) * 0.8
        except ValueError:
            # Not in history = full weight
            weight = 1.0
        weights.append(weight)

    # Weighted sampling WITHOUT replacement
    selected = []
    available_indices = list(range(len(questions)))
    available_weights = weights[:]

    for _ in range(count):
        if not available_indices:
            break
        # Normalize weights for remaining items
        total_weight = sum(available_weights)
        if total_weight == 0:
            # Fallback: pick randomly from remaining
            pick = random.choice(range(len(available_indices)))
        else:
            normalized = [w / total_weight for w in available_weights]
            pick = random.choices(
                range(len(available_indices)), weights=normalized, k=1
            )[0]

        selected.append(questions[available_indices[pick]])
        available_indices.pop(pick)
        available_weights.pop(pick)

    return selected


def select_questions(all_questions):
    """Randomly selects questions based on category counts with weighted selection."""
    selected = []

    # Load persistent usage history from file (not session state)
    usage_history = load_question_usage()

    if "cs" in all_questions:
        cs_qs = weighted_sample(all_questions["cs"], CS_COUNT, usage_history)
        for q in cs_qs:
            q["category"] = "Computer Science"
        selected.extend(cs_qs)

    if "math" in all_questions:
        math_qs = weighted_sample(all_questions["math"], MATH_COUNT, usage_history)
        for q in math_qs:
            q["category"] = "Mathematics"
        selected.extend(math_qs)

    if "logical_reasoning" in all_questions:
        lr_qs = weighted_sample(
            all_questions["logical_reasoning"], LR_COUNT, usage_history
        )
        for q in lr_qs:
            q["category"] = "Logical Reasoning"
        selected.extend(lr_qs)

    # Update persistent usage history with newly selected questions
    new_ids = [get_question_id(q) for q in selected]
    updated_history = new_ids + usage_history
    # Save to file (persists across page reloads)
    save_question_usage(updated_history[:MAX_USAGE_HISTORY])

    random.shuffle(selected)
    return selected


def initialize_session_state():
    """Initializes session state variables."""
    if "exam_started" not in st.session_state:
        st.session_state.exam_started = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "time_spent" not in st.session_state:
        st.session_state.time_spent = {}  # Map question index to total seconds
    if "current_q_index" not in st.session_state:
        st.session_state.current_q_index = 0
    if "q_start_time" not in st.session_state:
        st.session_state.q_start_time = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False


def update_time_spent():
    """Updates the time spent on the current question."""
    if st.session_state.q_start_time is not None:
        elapsed = time.time() - st.session_state.q_start_time
        idx = st.session_state.current_q_index
        st.session_state.time_spent[idx] = (
            st.session_state.time_spent.get(idx, 0) + elapsed
        )


def navigate_to(index):
    """Navigates to the specific question index."""
    update_time_spent()  # Save time for current question
    st.session_state.current_q_index = index
    st.session_state.q_start_time = time.time()  # Reset start time for new question
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
    update_time_spent()  # Final time capture
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
st.set_page_config(
    page_title="Mock Test App",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)
local_css()
initialize_session_state()

# --- Header ---
if not st.session_state.exam_started and not st.session_state.submitted:
    st.markdown(
        "<h1 style='text-align: center; color: #4F8BF9;'>Mock Test Application</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h3 style='text-align: center;'>MCA Entrance Preparation</h3>",
        unsafe_allow_html=True,
    )
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
            cols = st.columns(5)  # 5 columns for buttons
            for i in range(q_count):
                with cols[i % 5]:
                    is_current = i == st.session_state.current_q_index
                    is_answered = i in st.session_state.user_answers

                    label = f"{i+1}"
                    btn_type = (
                        "primary"
                        if is_current
                        else ("secondary" if not is_answered else "secondary")
                    )

                    # Style hack: If answered, maybe bold? Streamlit buttons are limited.
                    # We rely on 'primary' for current focus.

                    if st.button(
                        label, key=f"nav_{i}", type=btn_type, use_container_width=True
                    ):
                        navigate_to(i)

        st.markdown("---")
        if st.button("🚩 Submit Exam", type="primary", use_container_width=True):
            submit_exam()

    # --- Main Content ---
    if 0 <= st.session_state.current_q_index < len(st.session_state.questions):
        idx = st.session_state.current_q_index
        q = st.session_state.questions[idx]

        # Progress Bar
        progress = len(st.session_state.user_answers) / len(st.session_state.questions)
        st.progress(
            progress,
            text=f"Progress: {len(st.session_state.user_answers)}/{len(st.session_state.questions)} answered",
        )

        # Question Container
        with st.container():
            st.markdown(
                f"""
            <div class="question-card">
                <span class="category-tag">{q.get('category', 'General')}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Render question with LaTeX support
            st.markdown(f"### Q{idx+1}. {q['question']}")

        # Answer Selection
        current_answer = st.session_state.user_answers.get(idx, None)

        selected_option = st.radio(
            "Select an answer:",
            q["options"],
            index=(
                q["options"].index(current_answer)
                if current_answer in q["options"]
                else None
            ),
            key=f"radio_{idx}",
            label_visibility="collapsed",
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
    stats = {
        sec: {"correct": 0, "wrong": 0, "unattempted": 0, "score": 0, "time": 0.0}
        for sec in sections
    }
    total_score = 0
    total_correct = 0
    total_wrong = 0
    total_unattempted = 0

    # Calculate stats
    for i, q in enumerate(st.session_state.questions):
        user_ans = st.session_state.user_answers.get(i)
        correct_ans = q["answer"]
        category = q.get("category", "General")
        time_spent = st.session_state.time_spent.get(i, 0)

        if category in stats:
            stats[category]["time"] += time_spent

        if user_ans is None:
            total_unattempted += 1
            if category in stats:
                stats[category]["unattempted"] += 1
        elif user_ans == correct_ans:
            total_correct += 1
            if category in stats:
                stats[category]["correct"] += 1
            mark = 4
            total_score += mark
            if category in stats:
                stats[category]["score"] += mark
        else:
            total_wrong += 1
            if category in stats:
                stats[category]["wrong"] += 1
            mark = -1
            total_score += mark
            if category in stats:
                stats[category]["score"] += mark

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
            sc5.metric(
                "Avg Time",
                f"{(s_data['time'] / max(1, (s_data['correct'] + s_data['wrong'] + s_data['unattempted']))):.1f}s",
            )
            st.divider()

    # Detailed Analysis
    with st.expander("Show Detailed Question Analysis"):
        for i, q in enumerate(st.session_state.questions):
            user_ans = st.session_state.user_answers.get(i)
            correct_ans = q["answer"]
            time_spent = st.session_state.time_spent.get(i, 0)

            is_correct = user_ans == correct_ans
            icon = "✅" if is_correct else "❌"

            st.markdown(f"**Q{i+1}: {q['question']}** {icon}")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    f"- **Your Answer:** {user_ans if user_ans else 'No Answer'}"
                )
                st.markdown(f"- **Correct Answer:** {correct_ans}")
            with c2:
                st.markdown(f"- **Time Spent:** {time_spent:.1f}s")
                st.caption(f"Category: {q.get('category')}")
            st.divider()

    if st.button("🔄 Retake Exam", type="primary"):
        # Clear session state (usage history persists in browser localStorage)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- Start Screen ---
else:
    # Initialize usage history from browser on app start
    init_usage_from_browser()

    with st.container():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(
                "https://streamlit.io/images/brand/streamlit-mark-color.png", width=100
            )  # Placeholder logo
            st.markdown("## Instructions")
            st.info(
                f"""
            - **Duration:** {TOTAL_TIME_MINUTES} Minutes
            - **Total Questions:** {CS_COUNT + MATH_COUNT + LR_COUNT}
            - **Marking Scheme:** +4 for Correct, -1 for Incorrect
            """
            )

            # Show question usage tracking status
            usage_history = st.session_state.get("usage_history_cache", [])
            if len(usage_history) > 0:
                st.success(
                    f"""
                🎯 **Smart Randomization Active**  
                Tracking {len(usage_history)} recently used questions.  
                Recent questions will have lower probability (saved in browser).
                """
                )

            # Add button to clear history
            if st.button(
                "🗑️ Clear Question History",
                help="Reset question tracking to get a completely fresh randomization",
            ):
                clear_usage_history()
                st.success("Question history cleared!")
                st.rerun()

            st.markdown("### Subject Distribution")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Computer Science", CS_COUNT)
            col_b.metric("Mathematics", MATH_COUNT)
            col_c.metric("Logical Reasoning", LR_COUNT)

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🚀 Start Exam", type="primary", use_container_width=True):
                start_exam()
