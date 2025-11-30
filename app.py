import streamlit as st
import pandas as pd
import random
import os

# -----------------------------------------------------------------------------
# CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="React Master | 550 Questions",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner, "Notion-like" aesthetic
st.markdown("""
<style>
    /* Main Background adjustments */
    .stApp {
        background-color: #0e1117; 
    }
    
    /* Card Styling for Flashcards */
    .flashcard {
        background-color: #1f2937;
        padding: 40px;
        border-radius: 15px;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .question-text {
        font-size: 24px;
        font-weight: 600;
        color: #f3f4f6;
    }
    
    .category-tag {
        background-color: #3b82f6;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 15px;
    }

    /* Success/Info Message Styling */
    .stSuccess {
        background-color: #064e3b;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATA LOADING & SESSION STATE
# -----------------------------------------------------------------------------

FILE_PATH = './500_React_Interview_Questions.csv'

def create_demo_data():
    """Creates a dummy CSV if the real one isn't found, prevents crash."""
    data = {
        'ID': [1, 2, 3, 501, 502],
        'Category': ['Basics', 'Hooks', 'Components', 'System Design', 'System Design'],
        'Question': [
            'What is React?', 
            'What is useEffect?', 
            'Difference between Class and Functional components?',
            'Design an Infinite Scroll feed.',
            'Architect a Real-Time Chat App.'
        ],
        'Answer': [
            'A JS library for building UIs.', 
            'A hook for side effects.', 
            'Class uses this.state, Func uses hooks.',
            'Use Virtualization (Windowing) and DOM recycling.',
            'Use WebSockets, Optimistic UI, and IndexedDB.'
        ]
    }
    df = pd.DataFrame(data)
    df.to_csv(FILE_PATH, index=False)
    return df

@st.cache_data
def load_data():
    if not os.path.exists(FILE_PATH):
        return create_demo_data()
    try:
        df = pd.read_csv(FILE_PATH)
        # Ensure columns exist even if CSV is slightly malformed
        required_cols = ['ID', 'Category', 'Question', 'Answer']
        if not all(col in df.columns for col in required_cols):
            st.error("CSV is missing required columns: ID, Category, Question, Answer")
            return pd.DataFrame(columns=required_cols)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Initialize Session State
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = set()
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'reveal' not in st.session_state:
    st.session_state.reveal = False
if 'random_mode' not in st.session_state:
    st.session_state.random_mode = False

df = load_data()

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚛️ React Master")
    st.markdown("Your ultimate interview prep companion.")
    
    st.write("---")
    
    mode = st.radio(
        "Study Mode",
        ["📚 Browse & Search", "🃏 Flashcards", "🔖 My Bookmarks"]
    )
    
    st.write("---")
    
    # Global Filters (Apply to all views mostly)
    all_categories = sorted(df['Category'].astype(str).unique().tolist())
    selected_categories = st.multiselect(
        "Filter by Category", 
        all_categories,
        default=None,
        placeholder="All Categories"
    )
    
    # Progress
    st.write("---")
    st.subheader("Progress")
    total_q = len(df)
    bookmarked_q = len(st.session_state.bookmarks)
    st.metric("Total Questions", total_q)
    st.metric("Bookmarked for Review", bookmarked_q)
    
    if st.button("Clear Bookmarks", type="secondary"):
        st.session_state.bookmarks = set()
        st.rerun()

# Filter Data based on Sidebar
if selected_categories:
    filtered_df = df[df['Category'].isin(selected_categories)].reset_index(drop=True)
else:
    filtered_df = df

# -----------------------------------------------------------------------------
# PAGE: BROWSE & SEARCH
# -----------------------------------------------------------------------------
if mode == "📚 Browse & Search":
    st.header("Explore the Questions")
    st.caption(f"Displaying {len(filtered_df)} of {len(df)} total questions.")
    
    # Search Bar
    search_query = st.text_input("", placeholder="Search within the selected category...", label_visibility="collapsed")
    
    if search_query:
        display_df = filtered_df[
            filtered_df['Question'].str.contains(search_query, case=False) | 
            filtered_df['Answer'].str.contains(search_query, case=False)
        ]
    else:
        display_df = filtered_df
    
    st.write("---")

    # Display list in "Clean Read" mode
    for index, row in display_df.iterrows():
        # Using a container for better grouping
        with st.container():
            # Question Header
            st.subheader(f"{row['ID']}. {row['Question']}")
            
            # Answer Body
            st.markdown(f"**Answer:** {row['Answer']}")
            
            # Metadata & Actions row
            col_info, col_btn = st.columns([6, 1])
            
            with col_info:
                st.caption(f"Category: {row['Category']}")
                
            with col_btn:
                is_bookmarked = row['ID'] in st.session_state.bookmarks
                # Minimal button with icon
                icon = "★" if is_bookmarked else "☆"
                help_text = "Remove from bookmarks" if is_bookmarked else "Add to bookmarks"
                
                if st.button(icon, key=f"browse_bm_{row['ID']}", help=help_text):
                    if is_bookmarked:
                        st.session_state.bookmarks.remove(row['ID'])
                    else:
                        st.session_state.bookmarks.add(row['ID'])
                    st.rerun()
            
            st.divider()

# -----------------------------------------------------------------------------
# PAGE: FLASHCARDS
# -----------------------------------------------------------------------------
elif mode == "🃏 Flashcards":
    st.header("Active Recall Mode")
    
    if filtered_df.empty:
        st.warning("No questions found with current filters.")
    else:
        # Navigation Logic
        if st.session_state.current_index >= len(filtered_df):
            st.session_state.current_index = 0
            
        current_q = filtered_df.iloc[st.session_state.current_index]
        q_id = current_q['ID']
        
        # Top Controls
        col_prev, col_rand, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("⬅️ Previous"):
                st.session_state.current_index = (st.session_state.current_index - 1) % len(filtered_df)
                st.session_state.reveal = False
                st.rerun()
                
        with col_rand:
            if st.button("🎲 Random Question", use_container_width=True):
                st.session_state.current_index = random.randint(0, len(filtered_df) - 1)
                st.session_state.reveal = False
                st.rerun()
        
        with col_next:
            if st.button("Next ➡️"):
                st.session_state.current_index = (st.session_state.current_index + 1) % len(filtered_df)
                st.session_state.reveal = False
                st.rerun()

        st.write("") # Spacer

        # THE FLASHCARD UI
        
        # Bookmark status for current card
        is_bm = q_id in st.session_state.bookmarks
        bm_text = "★ Bookmarked" if is_bm else "☆ Add to Bookmarks"
        
        # Render Card
        st.markdown(f"""
        <div class="flashcard">
            <span class="category-tag">{current_q['Category']}</span>
            <div class="question-text">#{q_id}: {current_q['Question']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Actions Row
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button(bm_text, use_container_width=True):
                if is_bm:
                    st.session_state.bookmarks.remove(q_id)
                else:
                    st.session_state.bookmarks.add(q_id)
                st.rerun()

            reveal_btn = st.button("👁️ Reveal Answer", type="primary", use_container_width=True)
            
            if reveal_btn:
                st.session_state.reveal = not st.session_state.reveal
                
        # Answer Section
        if st.session_state.reveal:
            st.divider()
            st.markdown("### Answer")
            st.info(current_q['Answer'])
            
            # Simple Feedback Mechanism (Optional logic)
            st.caption("How did you do?")
            f1, f2, f3 = st.columns(3)
            with f1: st.button("🔴 Hard", key="hard")
            with f2: st.button("🟡 Okay", key="okay")
            with f3: st.button("🟢 Easy", key="easy")

# -----------------------------------------------------------------------------
# PAGE: BOOKMARKS
# -----------------------------------------------------------------------------
elif mode == "🔖 My Bookmarks":
    st.header("My Bookmarks")
    
    if not st.session_state.bookmarks:
        st.info("You haven't bookmarked any questions yet. Go to 'Browse' or 'Flashcards' to add some!")
    else:
        # Filter main DF by bookmarks
        bookmark_df = df[df['ID'].isin(st.session_state.bookmarks)]
        
        st.markdown(f"You have **{len(bookmark_df)}** questions marked for review.")
        
        for index, row in bookmark_df.iterrows():
            st.subheader(f"{row['ID']}. {row['Question']}")
            st.markdown(f"**Answer:** {row['Answer']}")
            
            if st.button("Remove Bookmark", key=f"rm_{row['ID']}"):
                st.session_state.bookmarks.remove(row['ID'])
                st.rerun()
            st.divider()

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.write("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Built for React Interview Prep 
    </div>
    """, 
    unsafe_allow_html=True
)
