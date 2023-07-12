# TGBot Calculating

This is a Python project that handles XLS files and performs calculations based on the data in the files. It uses the `aiogram` library for interacting with the Telegram Bot API.

## Getting Started

To get started with this project, follow the instructions below.

### Prerequisites

- Python 3.7+
- `aiogram` library
- `calendar` library
- `openpyxl` library
- `pandas` library
- Additional dependencies mentioned in `requirements.txt`

### Installation

1. Clone the repository:

   ```shell
   git clone https://github.com/Va1b0rt/TGBotCalculating.git
   ```

2. Install the required dependencies:

   ```shell
   pip install -r requirements.txt
   ```

3. Configure the Telegram Bot API token:

   Open the `config.py` file and replace `BOT_API_TOKEN` with your own Telegram Bot API token.

### Usage

To use the project, execute the following command:

```shell
python tgBot_Calculating.py
```

The program will start polling for new messages from the Telegram Bot API. It handles XLS files that are sent as documents and performs calculations based on the data in the files. If the attached file is not an XLS file, a warning message will be displayed.

## Contact

If you have any questions or suggestions, feel free to reach out to the project maintainer:

- Name: Volodymir
- Email: valbort.vladimir@gmail.com
