import streamlit as st
import pandas as pd
import random
import os
import datetime
from typing import List, Dict, Any, Optional, Set # For type hinting

# --- Constants ---
RESULTS_FILE = "quiz_results.csv"
NUM_OPTIONS = 5
COL_QUESTION = 'questions'
COL_ANSWER = 'answer'

# Session State Keys
SS_FLASHCARDS = 'flashcards'
SS_QUIZ_DATA = 'quiz_data'
SS_USER = 'user'
SS_CURRENT_INDEX = 'current_card_index' # Store the index being displayed

# Quiz Data Keys (within session_state[SS_QUIZ_DATA])
QK_STARTED = 'quiz_started'
QK_CORRECT_COUNT = 'correct_count'
QK_INCORRECT_COUNT = 'incorrect_count'
QK_CORRECT_QUESTIONS = 'correct_questions' # List of {question, answer} dicts
QK_INCORRECT_QUESTIONS = 'incorrect_questions' # List of {q, correct_a, user_a} dicts
QK_SHOW_ANSWER = 'show_answer' # Boolean flag for current question display
QK_USER_ANSWERS = 'user_answers' # Dict {original_index: user_answer}
QK_SUBMITTED = 'submitted' # Boolean flag for current question submission
QK_SHOW_ANSWER_CLICKED = 'show_answer_clicked' # Boolean flag for current q
QK_USED_QUESTIONS = 'used_questions' # Set of original indices attempted
QK_CURRENT_OPTIONS = 'current_options' # Stores options for the currently displayed question

# --- Helper Functions ---

def _get_default_quiz_state(num_questions: int) -> Dict[str, Any]:
    """Returns the default structure for the quiz state dictionary."""
    return {
        QK_STARTED: True,           # Flag indicating the quiz is active
        QK_CORRECT_COUNT: 0,        # Count of correctly answered questions
        QK_INCORRECT_COUNT: 0,      # Count of incorrectly answered questions
        QK_CORRECT_QUESTIONS: [],   # Stores details of correctly answered questions
        QK_INCORRECT_QUESTIONS: [], # Stores details of incorrectly answered questions
        QK_SHOW_ANSWER: False,      # Flag to display the answer for the current question
        QK_USER_ANSWERS: {},        # Stores the user's selected answer for each question {index: answer}
        QK_SUBMITTED: False,        # Flag indicating if the current question's answer was submitted
        QK_SHOW_ANSWER_CLICKED: False, # Flag indicating if 'Show Answer' was clicked for the current question
        QK_USED_QUESTIONS: set(),   # Set of original flashcard indices already presented
        QK_CURRENT_OPTIONS: None,   # Options generated for the current question
    }

# --- Core Logic Functions ---

def load_flashcards(uploaded_file) -> Optional[List[Dict[str, Any]]]:
    """
    Loads flashcards from an uploaded CSV or XLSX file.

    Args:
        uploaded_file: The file object uploaded via st.file_uploader.

    Returns:
        A list of dictionaries (flashcards) or None if loading fails.
    """
    try:
        fname = uploaded_file.name
        if fname.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif fname.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV or XLSX file.")
            return None

        if df.empty:
            st.error(f"The file '{fname}' is empty.")
            return None

        if len(df.columns) < 2:
            st.error(
                "File must contain at least two columns. "
                f"Expected '{COL_QUESTION}' (or first column) and '{COL_ANSWER}' (or second column)."
            )
            return None

        # Use standardized column names
        df = df.rename(columns={df.columns[0]: COL_QUESTION, df.columns[1]: COL_ANSWER})
        # Ensure columns exist after renaming
        if COL_QUESTION not in df.columns or COL_ANSWER not in df.columns:
             st.error(f"Could not find required columns '{COL_QUESTION}' and '{COL_ANSWER}' after renaming.")
             return None

        flashcards = df[[COL_QUESTION, COL_ANSWER]].to_dict('records')
        return flashcards

    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        return None

def start_quiz(flashcards: List[Dict[str, Any]]):
    """Initializes or restarts the quiz state in session_state."""
    st.session_state[SS_FLASHCARDS] = flashcards # Store the loaded flashcards
    st.session_state[SS_QUIZ_DATA] = _get_default_quiz_state(len(flashcards))
    # Clear any lingering current index from a previous run
    if SS_CURRENT_INDEX in st.session_state:
        del st.session_state[SS_CURRENT_INDEX]
    st.rerun() # Rerun to reflect the start of the quiz immediately

def generate_options(correct_answer: str, all_answers: List[str], num_options: int = NUM_OPTIONS) -> List[str]:
    """
    Generates multiple-choice options, including the correct answer.

    Args:
        correct_answer: The correct answer string.
        all_answers: A list of all possible answer strings from the dataset.
        num_options: The total number of options desired (including correct).

    Returns:
        A list of shuffled answer options.
    """
    options = {correct_answer.strip()} # Use a set for uniqueness initially
    correct_lower = correct_answer.strip().lower()

    # Filter out the correct answer (case-insensitive)
    other_answers = [ans for ans in all_answers if ans.strip().lower() != correct_lower]

    # Ensure enough unique incorrect options are available
    num_incorrect_needed = num_options - 1
    num_available_incorrect = len(set(ans.strip() for ans in other_answers)) # Count unique incorrect

    if num_available_incorrect >= num_incorrect_needed:
        # Sample unique incorrect answers
        incorrect_options_pool = list(set(ans.strip() for ans in other_answers))
        incorrect_options = random.sample(incorrect_options_pool, num_incorrect_needed)
        options.update(incorrect_options)
    else:
        # Not enough unique incorrect answers, add all available unique ones
        options.update(ans.strip() for ans in other_answers)

    # Convert back to list and shuffle
    final_options = list(options)
    random.shuffle(final_options)
    return final_options

def display_question(question_data: Dict[str, Any], options: List[str], question_key_suffix: str):
    """
    Displays the question and multiple-choice options using st.radio.

    Args:
        question_data: Dictionary containing the 'questions' text.
        options: List of answer strings for the radio button.
        question_key_suffix: A unique suffix for the st.radio key.

    Returns:
        The answer selected by the user.
    """
    st.write(f"**Question:** {question_data[COL_QUESTION]}")
    # Use a unique key based on the question index/suffix to maintain state correctly
    selected_answer = st.radio(
        "Choose your answer:",
        options,
        key=f"radio_{question_key_suffix}",
        index=None # Default to no selection
    )
    return selected_answer

def check_answer(user_answer: Optional[str], correct_answer: str) -> bool:
    """Checks if the user's answer is correct (case-insensitive comparison)."""
    if user_answer is None:
        return False # No answer selected is incorrect
    return user_answer.strip().lower() == correct_answer.strip().lower()

def handle_incorrect_answer(current_card: Dict[str, Any], user_answer: Optional[str]):
    """Handles the logic when an answer is marked incorrect."""
    quiz_data = st.session_state[SS_QUIZ_DATA]
    quiz_data[QK_INCORRECT_COUNT] += 1
    quiz_data[QK_INCORRECT_QUESTIONS].append({
        'Question': current_card[COL_QUESTION],
        'Correct Answer': current_card[COL_ANSWER],
        'Your Answer': user_answer if user_answer is not None else "No answer"
    })

def handle_submit(current_card_index: int):
    """Handles the answer submission logic."""
    quiz_data = st.session_state[SS_QUIZ_DATA]
    flashcards = st.session_state[SS_FLASHCARDS]
    current_card = flashcards[current_card_index]

    user_answer = quiz_data[QK_USER_ANSWERS].get(current_card_index)

    if check_answer(user_answer, current_card[COL_ANSWER]):
        st.success("Correct!")
        # Avoid double counting if somehow submitted again
        if current_card_index not in quiz_data[QK_USED_QUESTIONS]:
             quiz_data[QK_CORRECT_COUNT] += 1
             quiz_data[QK_CORRECT_QUESTIONS].append({
                 COL_QUESTION: current_card[COL_QUESTION],
                 COL_ANSWER: current_card[COL_ANSWER]
             })
    else:
        st.error(f"Incorrect. The correct answer is: {current_card[COL_ANSWER]}")
        # Record incorrect only if not already recorded via "Show Answer"
        if current_card_index not in quiz_data[QK_USED_QUESTIONS]:
             handle_incorrect_answer(current_card, user_answer)

    quiz_data[QK_SUBMITTED] = True
    quiz_data[QK_SHOW_ANSWER] = True # Show answer after submitting
    quiz_data[QK_USED_QUESTIONS].add(current_card_index) # Mark as used
    st.rerun() # Update UI to show feedback and potentially Next button

def handle_show_answer(current_card_index: int):
    """Handles the logic when 'Show Answer' is clicked."""
    quiz_data = st.session_state[SS_QUIZ_DATA]
    flashcards = st.session_state[SS_FLASHCARDS]
    current_card = flashcards[current_card_index]

    st.info(f"**Correct Answer:** {current_card[COL_ANSWER]}")
    quiz_data[QK_SHOW_ANSWER] = True
    quiz_data[QK_SHOW_ANSWER_CLICKED] = True

    # If the answer wasn't already submitted/used, mark it as incorrect
    if current_card_index not in quiz_data[QK_USED_QUESTIONS]:
        user_answer = quiz_data[QK_USER_ANSWERS].get(current_card_index)
        handle_incorrect_answer(current_card, user_answer)
        quiz_data[QK_USED_QUESTIONS].add(current_card_index) # Mark as used

    quiz_data[QK_SUBMITTED] = True # Treat showing answer as a form of submission
    st.rerun() # Update UI

def handle_next_question():
    """Resets flags to prepare for the next question draw."""
    quiz_data = st.session_state[SS_QUIZ_DATA]
    quiz_data[QK_SHOW_ANSWER] = False
    quiz_data[QK_SUBMITTED] = False
    quiz_data[QK_SHOW_ANSWER_CLICKED] = False
    quiz_data[QK_CURRENT_OPTIONS] = None # <<< Clear options for next question
    # Remove the stored current index so a new one is picked
    if SS_CURRENT_INDEX in st.session_state:
        del st.session_state[SS_CURRENT_INDEX]
    st.rerun() # Rerun to draw and display the next question

def display_quiz_results():
    """Displays the final quiz results and review sections."""
    quiz_data = st.session_state[SS_QUIZ_DATA]
    total_questions = len(st.session_state[SS_FLASHCARDS])

    st.subheader("Quiz Completed!")
    st.metric("Total Questions", total_questions)
    st.metric("Correct Answers", f"{quiz_data[QK_CORRECT_COUNT]} / {total_questions}")
    st.metric("Incorrect Answers", f"{quiz_data[QK_INCORRECT_COUNT]} / {total_questions}")

    # Calculate score
    score = (quiz_data[QK_CORRECT_COUNT] / total_questions) * 100 if total_questions > 0 else 0
    st.progress(int(score))
    st.write(f"**Score: {score:.2f}%**")


    if quiz_data[QK_INCORRECT_QUESTIONS]:
        st.subheader("Review Incorrect Questions:")
        incorrect_df = pd.DataFrame(quiz_data[QK_INCORRECT_QUESTIONS])
        st.dataframe(incorrect_df, use_container_width=True)

    # Optionally show correct answers for review
    # if quiz_data[QK_CORRECT_QUESTIONS]:
    #     with st.expander("Review Correct Questions"):
    #         correct_df = pd.DataFrame(quiz_data[QK_CORRECT_QUESTIONS])
    #         st.dataframe(correct_df, use_container_width=True)

    if st.button("Restart Quiz"):
        # Pass flashcards from session state to start_quiz
        start_quiz(st.session_state[SS_FLASHCARDS])
        # No need for rerun here, start_quiz handles it

# --- Results Persistence ---

def load_quiz_results() -> List[Dict[str, Any]]:
    """Loads all past quiz results from the CSV file."""
    if os.path.exists(RESULTS_FILE):
        try:
            return pd.read_csv(RESULTS_FILE).to_dict('records')
        except pd.errors.EmptyDataError:
            return [] # File exists but is empty
        except Exception as e:
            st.error(f"Error loading results file: {e}")
            return []
    return []

def save_quiz_results(results: List[Dict[str, Any]]):
    """Saves quiz results to the CSV file."""
    try:
        df = pd.DataFrame(results)
        df.to_csv(RESULTS_FILE, index=False)
    except Exception as e:
        st.error(f"Error saving results file: {e}")

def record_quiz_attempt():
    """Records the just-completed quiz attempt to the results file."""
    quiz_data = st.session_state[SS_QUIZ_DATA]
    flashcards = st.session_state[SS_FLASHCARDS]
    user = st.session_state.get(SS_USER, "Unknown") # Get user, default if not set

    if not user or user == "Unknown":
        st.warning("User name not set. Results cannot be saved.")
        return

    results = load_quiz_results()
    timestamp = datetime.datetime.now().isoformat()

    # Format incorrect questions slightly more compactly for the CSV
    incorrect_details = []
    for item in quiz_data[QK_INCORRECT_QUESTIONS]:
        incorrect_details.append(
            f"Q: {item['Question']} | A: {item['Correct Answer']} | Your: {item['Your Answer']}"
        )
    incorrect_questions_str = "; ".join(incorrect_details)

    results.append({
        "Timestamp": timestamp,
        "User": user,
        "Correct Count": quiz_data[QK_CORRECT_COUNT],
        "Incorrect Count": quiz_data[QK_INCORRECT_COUNT],
        "Total Questions": len(flashcards),
        "Incorrect Details": incorrect_questions_str,
    })
    save_quiz_results(results)
    st.success("Quiz results recorded.")

def display_all_quiz_results():
    """Displays all recorded quiz results in a table."""
    results = load_quiz_results()
    if results:
        st.subheader("All Past Quiz Results")
        df = pd.DataFrame(results)
        if "Timestamp" in df.columns:
             try:
                 df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.strftime('%Y-%m-%d %H:%M:%S')
             except Exception:
                 pass # Ignore formatting errors
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No past quiz results found.")

# --- Main Application ---

# --- Main Application ---

def main():
    st.set_page_config(layout="wide")
    st.title("🧠 Flashcard Quiz App")

    # --- User Identification ---
    st.sidebar.header("User")
    if SS_USER not in st.session_state:
        st.session_state[SS_USER] = "" # Initialize user state

    user_name = st.sidebar.text_input("Enter your name to save results:", value=st.session_state[SS_USER])
    if user_name:
        st.session_state[SS_USER] = user_name
        st.sidebar.success(f"Current User: {st.session_state[SS_USER]}")
    else:
        st.sidebar.warning("Enter your name to track results.")

    # --- File Upload ---
    st.sidebar.header("Load Flashcards")
    uploaded_file = st.sidebar.file_uploader("Upload CSV or XLSX file", type=["csv", "xlsx", "xls"])

    # --- Handle File Upload/Removal ---
    if uploaded_file is not None:
        # Load only if flashcards aren't already loaded from this specific file
        # Simple check: If no flashcards, load. If file name changes, reload.
        # (More robust check could use file ID if needed)
        current_file_name = uploaded_file.name
        previous_file_name = st.session_state.get('_loaded_file_name', None)

        if SS_FLASHCARDS not in st.session_state or current_file_name != previous_file_name:
            flashcards = load_flashcards(uploaded_file)
            if flashcards:
                st.session_state[SS_FLASHCARDS] = flashcards
                st.session_state['_loaded_file_name'] = current_file_name # Track loaded file name
                st.sidebar.success(f"Loaded {len(flashcards)} flashcards.")
                # Clear old quiz state if new file loaded or reloaded
                if SS_QUIZ_DATA in st.session_state:
                    del st.session_state[SS_QUIZ_DATA]
                if SS_CURRENT_INDEX in st.session_state:
                    del st.session_state[SS_CURRENT_INDEX]
                # Clear cached answers if file changes
                if 'all_answers' in st.session_state:
                    del st.session_state['all_answers']

                st.rerun() # Rerun to update UI after loading/clearing state
            else:
                # Loading failed, clear any potentially loaded cards/state
                if SS_FLASHCARDS in st.session_state: del st.session_state[SS_FLASHCARDS]
                if '_loaded_file_name' in st.session_state: del st.session_state['_loaded_file_name']
                if SS_QUIZ_DATA in st.session_state: del st.session_state[SS_QUIZ_DATA]
                if SS_CURRENT_INDEX in st.session_state: del st.session_state[SS_CURRENT_INDEX]
                if 'all_answers' in st.session_state: del st.session_state['all_answers']

    elif SS_FLASHCARDS in st.session_state:
         # File removed in uploader UI, clear related state
         del st.session_state[SS_FLASHCARDS]
         if '_loaded_file_name' in st.session_state: del st.session_state['_loaded_file_name']
         if SS_QUIZ_DATA in st.session_state: del st.session_state[SS_QUIZ_DATA]
         if SS_CURRENT_INDEX in st.session_state: del st.session_state[SS_CURRENT_INDEX]
         if 'all_answers' in st.session_state: del st.session_state['all_answers']
         st.rerun()


    # --- Process Flashcards and Quiz State ---
    if SS_FLASHCARDS in st.session_state:
        flashcards = st.session_state[SS_FLASHCARDS]

        # Cache all unique answers once per flashcard set
        if 'all_answers' not in st.session_state:
             st.session_state['all_answers'] = list(set(card[COL_ANSWER] for card in flashcards))
        all_answers = st.session_state['all_answers']

        # Initialize quiz state if it doesn't exist for the loaded flashcards
        if SS_QUIZ_DATA not in st.session_state:
            st.session_state[SS_QUIZ_DATA] = _get_default_quiz_state(len(flashcards))
            st.session_state[SS_QUIZ_DATA][QK_STARTED] = False # Explicitly set not started

        quiz_data = st.session_state[SS_QUIZ_DATA]

        # --- Sidebar Controls (Restart Button) ---
        st.sidebar.header("Quiz Controls")
        # Show restart button in sidebar ONLY if quiz has started AND is not finished
        if quiz_data.get(QK_STARTED, False):
             # Need to check if finished - calculate available indices here too
             all_indices_set = set(range(len(flashcards)))
             used_indices_set: Set[int] = quiz_data.get(QK_USED_QUESTIONS, set())
             is_finished = not (all_indices_set - used_indices_set) # True if no available indices left

             if not is_finished: # Only show if quiz is running AND not finished
                 if st.sidebar.button("🔁 Restart Quiz Now", key="restart_quiz_sidebar", help="Stop the current quiz and start over."):
                     start_quiz(st.session_state[SS_FLASHCARDS])
                     # start_quiz calls rerun, execution effectively stops here for this run
             else:
                # Optionally show a message or different control when finished
                st.sidebar.info("Quiz finished. See results.")

        # --- Main Area: Start Button or Quiz Display ---
        if not quiz_data.get(QK_STARTED, False):
             st.info("Flashcards loaded. Press 'Start Quiz' to begin.")
             if st.button("🚀 Start Quiz", type="primary"):
                 start_quiz(st.session_state[SS_FLASHCARDS])
                 # start_quiz calls rerun

        elif quiz_data.get(QK_STARTED, False):
            # --- Active Quiz Logic ---
            # Determine available questions (recalculate here for main logic)
            all_indices = set(range(len(flashcards)))
            used_indices: Set[int] = quiz_data[QK_USED_QUESTIONS]
            available_indices = list(all_indices - used_indices)

            # --- Quiz Completion Check ---
            if not available_indices:
                # Quiz is finished, display results
                display_quiz_results()
                # Attempt to record only once after completion
                if 'results_recorded' not in quiz_data:
                     record_quiz_attempt()
                     quiz_data['results_recorded'] = True # Mark as recorded
            else:
                # --- Display Current Question ---
                # Choose the next question index randomly if not already set for this turn
                if SS_CURRENT_INDEX not in st.session_state:
                    st.session_state[SS_CURRENT_INDEX] = random.choice(available_indices)
                    # Ensure options are cleared when a new index is chosen
                    quiz_data[QK_CURRENT_OPTIONS] = None

                current_card_index = st.session_state[SS_CURRENT_INDEX]
                current_card = flashcards[current_card_index]

                # --- Generate or Retrieve Options ---
                options = quiz_data.get(QK_CURRENT_OPTIONS)
                if not options:
                    # Generate options only if they aren't already stored for this question turn
                    options = generate_options(current_card[COL_ANSWER], all_answers)
                    quiz_data[QK_CURRENT_OPTIONS] = options # Store the generated options

                # --- Display Question UI ---
                if options:
                    user_answer = display_question(current_card, options, f"q_{current_card_index}")
                else:
                    st.error("Error: Could not generate/retrieve options.") # Fallback
                    user_answer = None

                # Store the user's current selection immediately
                quiz_data[QK_USER_ANSWERS][current_card_index] = user_answer

                st.write("---") # Separator

                # --- Action Buttons (Toggle Logic) ---
                submitted = quiz_data[QK_SUBMITTED]
                show_answer_clicked = quiz_data[QK_SHOW_ANSWER_CLICKED]

                # Use a consistent key for the main action button across states
                action_button_key = f"action_button_{current_card_index}"

                if submitted or show_answer_clicked:
                    # --- State: Show "Next Question" ---
                    if st.button("➡️ Next Question", key=action_button_key):
                         handle_next_question()
                         # handle_next_question calls rerun, so script execution stops here
                else:
                    # --- State: Show "Submit Answer" and "Show Answer" ---
                    col_submit, col_show = st.columns(2) # Place Submit and Show side-by-side

                    with col_submit:
                        submit_disabled = user_answer is None
                        if st.button("✅ Submit Answer", key=action_button_key, disabled=submit_disabled, type="primary"):
                            handle_submit(current_card_index)
                            # handle_submit calls rerun, so script execution stops here

                    with col_show:
                        show_answer_key = f"show_answer_{current_card_index}"
                        if st.button("💡 Show Answer", key=show_answer_key):
                             handle_show_answer(current_card_index)
                             # handle_show_answer calls rerun, so script execution stops here

                st.write("---")
                # --- Progress Indicators ---
                remaining_count = len(available_indices)
                st.write(f"**Remaining Questions:** {remaining_count}")
                st.write(f"**Correct:** {quiz_data[QK_CORRECT_COUNT]} | **Incorrect:** {quiz_data[QK_INCORRECT_COUNT]}")

    else:
        # No flashcards loaded state
        st.info("Please upload a flashcard file (CSV or XLSX) using the sidebar.")

    # --- Display All Results Area ---
    st.sidebar.header("History")
    if st.sidebar.button("Show All Past Results"):
        display_all_quiz_results()

# Make sure the rest of your functions (load_flashcards, start_quiz, etc.) exist outside main()

if __name__ == "__main__":
    main()