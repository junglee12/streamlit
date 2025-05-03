# 🧠 Streamlit Flashcard Quiz App

A simple web application built with Streamlit to help you study using flashcards loaded from a CSV or Excel file.

## Features

*   **File Upload:** Load questions and answers from CSV or Excel files.
*   **Multiple Choice Quiz:** Generates random multiple-choice options for each question.
*   **Random Question Order:** Presents flashcards in a random sequence until all are attempted.
*   **Immediate Feedback:** Tells you if your answer was correct or incorrect right after submission.
*   **Show Answer Option:** Allows revealing the correct answer (marks the question as incorrect if used before submitting).
*   **Progress Tracking:** Shows remaining questions, correct count, and incorrect count during the quiz.
*   **Results Summary:** Displays your final score and a table reviewing incorrectly answered questions upon completion.
*   **Results Persistence:** Saves quiz results (timestamp, user name, score, incorrect details) locally to `quiz_results.csv`.
*   **History View:** Allows viewing all past quiz results saved in the CSV file.
*   **User Identification:** Prompts for a username to associate with saved results.
*   **Restart Options:** Restart the quiz mid-way or after completion.

## How to Run

1.  **Prerequisites:**
    *   Ensure you have Python 3 installed.
    *   It's recommended to use a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
        ```

2.  **Install Dependencies:**
    Install the required Python libraries:
    ```bash
    pip install streamlit pandas openpyxl
    ```
    *(Note: `openpyxl` is needed for Excel file support)*

3.  **Navigate to the Directory:**
    Open your terminal or command prompt and change to the directory where the `flashcard_quiz.py` file is located:
    ```bash
    cd /home/j/Downloads/dev/streamlit/
    ```

4.  **Run the App:**
    Execute the Streamlit command:
    ```bash
    streamlit run flashcard_quiz.py
    ```

5.  **Access the App:**
    Streamlit will provide a local URL (usually `http://localhost:8501`) in your terminal. Open this URL in your web browser.

## Input File Format

*   The application accepts **CSV** (`.csv`) and **Excel** (`.xlsx`, `.xls`) files.
*   The file **must** contain at least two columns.
*   The **first row** should contain **headers** (e.g., "Question", "Answer", "Term", "Definition"). These headers are ignored by the app itself.
*   The **first column** (starting from the second row) will be treated as the **Question**.
*   The **second column** (starting from the second row) will be treated as the **Answer**.
*   Any additional columns beyond the first two will be ignored.

**Example CSV (`my_flashcards.csv`):**

```csv
Term,Definition
Streamlit,"An open-source app framework for Machine Learning and Data Science teams"
Pandas,"A fast, powerful, flexible and easy to use open source data analysis and manipulation tool"
Python,"An interpreted, high-level and general-purpose programming language"
```

## Persistence

*   Quiz results are saved locally in the same directory as the script in a file named `quiz_results.csv`.
*   Each row represents a completed quiz attempt, including user name, timestamp, counts, and details of incorrect answers.
*   **Note:** This local CSV storage is suitable for single-user, local operation. If deployed for multiple users, this file could lead to conflicts.

## Dependencies

*   streamlit
*   pandas
*   openpyxl (for Excel support)