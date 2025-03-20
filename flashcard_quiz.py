import streamlit as st
import pandas as pd
import random

def load_flashcards(uploaded_file):
    """Loads flashcards from a CSV or XLSX file into a list of dictionaries."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV or XLSX file.")
            return None

        if len(df.columns) < 2:
            st.error("File must contain at least two columns (questions and answers).")
            return None

        df = df.rename(columns={df.columns[0]: 'questions', df.columns[1]: 'answer'})
        flashcards = df.to_dict('records')
        return flashcards
    except FileNotFoundError:
        st.error(f"File not found: {uploaded_file.name}")
        return None
    except pd.errors.EmptyDataError:
        st.error(f"The file is empty: {uploaded_file.name}")
        return None
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        return None

def generate_options(correct_answer, all_answers, num_options=5):
    """Generates multiple-choice options, including the correct answer."""
    options = [correct_answer]
    other_answers = [ans for ans in all_answers if ans.strip().lower() != correct_answer.strip().lower()]
    
    # Select incorrect options
    while len(options) < num_options and other_answers:
        incorrect_option = random.choice(other_answers)
        if incorrect_option not in options:
            options.append(incorrect_option)
            other_answers.remove(incorrect_option)
        else:
            other_answers.remove(incorrect_option)

    random.shuffle(options)
    return options

def display_question(question_data, options):
    """Displays the question and multiple-choice options."""
    st.write(f"**Question:** {question_data['questions']}")
    selected_answer = st.radio("Choose your answer:", options, key=f"radio_{question_data['index']}")
    return selected_answer

def check_answer(user_answer, correct_answer):
    """Checks if the user's answer is correct."""
    return user_answer.strip().lower() == correct_answer.strip().lower()

def initialize_quiz_state(flashcards):
    """Initializes the quiz state in st.session_state."""
    st.session_state.quiz_data = {
        'quiz_started': False,
        'correct_count': 0,
        'incorrect_count': 0,
        'correct_questions': [],
        'incorrect_questions': [],
        'current_question_index': 0,
        'questions_order': list(range(len(flashcards))),
        'show_answer': False,
        'user_answers': {},
        'submitted': False,
        'show_answer_clicked': False,
        'incorrect_question_indices': set(),
    }
    random.shuffle(st.session_state.quiz_data['questions_order'])

def start_quiz():
    """Starts or restarts the quiz."""
    st.session_state.quiz_data['quiz_started'] = True
    st.session_state.quiz_data['correct_count'] = 0
    st.session_state.quiz_data['incorrect_count'] = 0
    st.session_state.quiz_data['correct_questions'] = []
    st.session_state.quiz_data['incorrect_questions'] = []
    st.session_state.quiz_data['current_question_index'] = 0
    st.session_state.quiz_data['questions_order'] = list(range(len(st.session_state.flashcards)))
    random.shuffle(st.session_state.quiz_data['questions_order'])
    st.session_state.quiz_data['show_answer'] = False
    st.session_state.quiz_data['user_answers'] = {}
    st.session_state.quiz_data['submitted'] = False
    st.session_state.quiz_data['show_answer_clicked'] = False
    st.session_state.quiz_data['incorrect_question_indices'] = set()

def handle_submit(current_card, current_card_index):
    """Handles the submission of an answer."""
    if check_answer(st.session_state.quiz_data['user_answers'][current_card_index], current_card['answer']):
        st.success("Correct!")
        st.session_state.quiz_data['correct_count'] += 1
        st.session_state.quiz_data['correct_questions'].append(current_card)
    else:
        st.error("Incorrect.")
        st.session_state.quiz_data['incorrect_count'] += 1
        st.session_state.quiz_data['incorrect_questions'].append(current_card)
    st.session_state.quiz_data['submitted'] = True
    st.session_state.quiz_data['show_answer'] = True
    st.session_state.quiz_data['incorrect_question_indices'].add(current_card_index)

def handle_next_question():
    """Moves to the next question."""
    st.session_state.quiz_data['current_question_index'] += 1
    st.session_state.quiz_data['show_answer'] = False
    st.session_state.quiz_data['submitted'] = False
    st.session_state.quiz_data['show_answer_clicked'] = False

def handle_show_answer(current_card, current_card_index):
    """Handles showing the correct answer."""
    st.session_state.quiz_data['show_answer'] = True
    st.session_state.quiz_data['show_answer_clicked'] = True

    if not st.session_state.quiz_data['submitted']:
        st.session_state.quiz_data['incorrect_count'] += 1
        st.session_state.quiz_data['incorrect_questions'].append(current_card)
        st.session_state.quiz_data['incorrect_question_indices'].add(current_card_index)
    st.session_state.quiz_data['submitted'] = True

def display_quiz_results(flashcards):
    """Displays the quiz results."""
    st.write(f"**Quiz Completed!**")
    st.write(f"**Correct Answers:** {st.session_state.quiz_data['correct_count']} out of {len(flashcards)}")
    st.write(f"**Incorrect Answers:** {st.session_state.quiz_data['incorrect_count']} out of {len(flashcards)}")
    if st.session_state.quiz_data['incorrect_questions']:
        st.write("**Review Incorrect Questions:**")
        for incorrect_question in st.session_state.quiz_data['incorrect_questions']:
            st.write(f"- **Question:** {incorrect_question['questions']}")
            st.write(f"- **Correct Answer:** {incorrect_question['answer']}")
    if st.session_state.quiz_data['correct_questions']:
        st.write("**Review Correct Questions:**")
        for correct_question in st.session_state.quiz_data['correct_questions']:
            st.write(f"- **Question:** {correct_question['questions']}")
            st.write(f"- **Correct Answer:** {correct_question['answer']}")
    if st.button("Restart Quiz"):
        start_quiz()
        st.rerun()

def main():
    st.title("Flashcard Quiz App")
    uploaded_file = st.file_uploader("Upload your flashcard file (CSV or XLSX)", type=["csv", "xlsx"])

    if uploaded_file is not None:
        flashcards = load_flashcards(uploaded_file)
        if flashcards:
            if 'flashcards' not in st.session_state:
                st.session_state.flashcards = flashcards
            if 'quiz_data' not in st.session_state:
                initialize_quiz_state(flashcards)

            all_answers = [card['answer'] for card in flashcards]

            if not st.session_state.quiz_data['quiz_started']:
                if st.button("Start Quiz"):
                    start_quiz()
                    st.rerun()

            if st.session_state.quiz_data['quiz_started']:
                if st.session_state.quiz_data['current_question_index'] < len(flashcards):
                    current_card_index = st.session_state.quiz_data['questions_order'][st.session_state.quiz_data['current_question_index']]
                    current_card = flashcards[current_card_index]
                    current_card['index'] = current_card_index

                    if current_card_index not in st.session_state:
                        st.session_state[current_card_index] = {}
                    if 'options' not in st.session_state[current_card_index]:
                        st.session_state[current_card_index]['options'] = generate_options(current_card['answer'], all_answers)
                    options = st.session_state[current_card_index]['options']

                    user_answer = display_question(current_card, options)
                    st.session_state.quiz_data['user_answers'][current_card_index] = user_answer

                    col1, col2 = st.columns(2)
                    with col1:
                        if not st.session_state.quiz_data['submitted'] and not st.session_state.quiz_data['show_answer_clicked']:
                            if st.button("Submit", key=f"submit_{current_card_index}"):
                                handle_submit(current_card, current_card_index)
                                st.rerun()
                        else:
                            if st.button("Next Question", key=f"next_{current_card_index}"):
                                handle_next_question()
                                st.rerun()

                    with col2:
                        if st.button("Show Answer", key=f"show_answer_{current_card_index}"):
                            handle_show_answer(current_card, current_card_index)
                            st.rerun()

                    if st.session_state.quiz_data['show_answer']:
                        st.write(f"**Correct Answer:** {current_card['answer']}")

                else:
                    display_quiz_results(flashcards)
                st.write(f"**Remaining Questions:** {len(flashcards) - st.session_state.quiz_data['current_question_index']}")
                st.write(f"**Correct Answers:** {st.session_state.quiz_data['correct_count']}")
                st.write(f"**Incorrect Answers:** {st.session_state.quiz_data['incorrect_count']}")

if __name__ == "__main__":
    main()
