# US Accidents (2016 - 2023) Raw Dataset Documentation

## 1. Dataset Name
**US Accidents: A Countrywide Traffic Accident Dataset (2016–2023)**

## 2. Original Source & Authors
- **Authors**: Sobhan Moosavi, Mohammad Hossein Samavatian, Srinivasan Parthasarathy, Rajiv Ramnath
- **Institution**: Department of Computer Science and Engineering, The Ohio State University
- **Publication References**:
  - Moosavi, Sobhan, et al. *"A Countrywide Traffic Accident Dataset."* arXiv preprint arXiv:1906.05409 (2019).
  - Moosavi, Sobhan, et al. *"Accident Prediction: A Risk-Driven Approach."* IEEE Transactions on Intelligent Transportation Systems (2021).
- **Kaggle Dataset URL**: [https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents)

## 3. Dataset Version & Release Date
- **Version**: Version 13 (March 2023 Release)
- **Coverage Interval**: January 14, 2016 – March 31, 2023

## 4. Expected Raw Filename
- **Exact Filename**: `US_Accidents_March23.csv`
- **File Size on Disk**: ~3.06 GB uncompressed (2,848 MB)
- **Archive Size**: ~653 MB compressed (.zip / .archive)
- **Record Count**: 7,728,394 rows
- **Feature Count**: 46 columns

## 5. License Information
- **License**: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (**CC BY-NC-SA 4.0**)
- **Usage Restrictions**: Academic and hackathon research prototype use. Commercial redistribution prohibited under this license.

## 6. Download Instructions

### Automated Script (Python / KaggleHub)
```bash
pip install kagglehub
python -c "import kagglehub; path = kagglehub.dataset_download('sobhanmoosavi/us-accidents'); print('Downloaded to:', path)"
```

### Manual Download (Kaggle Web Interface)
1. Navigate to: `https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents`
2. Authenticate with Kaggle credentials.
3. Download `us-accidents.zip` (~653 MB).
4. Extract the archive into the `data/` or `data/raw/` directory.
5. Verify that `US_Accidents_March23.csv` is present.

### Storage & Version Control Policy
> [!IMPORTANT]
> The raw CSV file (`US_Accidents_March23.csv`) exceeds GitHub file size limits (>100 MB per file, repository limits ~2 GB). **NEVER commit the raw CSV file to Git.** It is excluded via `.gitignore`.
