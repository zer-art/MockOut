 # Streamlit Mock Test Application

An interactive mock test application built with Streamlit and Pixi.

## Features

-   **Subject Coverage**: Questions from Computer Science, Mathematics, and Logical Reasoning.
-   **Randomized Questions**:
    -   36 Computer Science questions
    -   24 Mathematics questions
    -   15 Logical Reasoning questions
-   **Timer**: 90-minute countdown timer.
-   **Instant Feedback**: Detailed results page with score and correct/incorrect answer breakdown.

## Folder Structure

```
mock test/
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── src/
│   ├── app.py               # Main application file
│   ├── utils.py             # Utility functions
│   └── __pycache__/         # Python cache files
├── __pycache__/             # Python cache files
├── .pixi/                   # Pixi environment files
├── QuestionBank.yaml        # Question database
├── Qtemp.md                 # Temporary questions
├── README.md                # This file
├── pixi.toml                # Pixi configuration
├── pixi.lock                # Pixi lock file
├── .gitignore               # Git ignore rules
└── .gitattributes           # Git attributes
```

## Prerequisites

-   [Pixi](https://prefix.dev/) package manager.

## Installation

1.  Clone the repository or navigate to the project directory.
2.  Initialize the environment and install dependencies:
    ```bash
    pixi install
    ```

## Usage

To run the application:

```bash
pixi run streamlit run src/app.py
```

The application will open in your default web browser (usually at `http://localhost:8501`).

## Configuration

Questions are stored in `QuestionBank.yaml`. You can modify this file to add, remove, or edit questions in the following format:

```yaml
category_name:
  - question: "Question text here?"
    options: ["Option A", "Option B", "Option C", "Option D"]
    answer: "Correct Option Text"
```
