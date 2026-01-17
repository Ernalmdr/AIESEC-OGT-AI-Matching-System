# AIESEC OGT AI-Powered Matching Assistant 🚀

An intelligent decision-support tool designed for AIESEC's Outgoing Global Talent (OGT) department. This application automates the matching process between Exchange Participants (EPs) from Podio and available opportunities from the OGT Tracker (Google Sheets) using Artificial Intelligence.

## 🎯 Purpose
The goal is to streamline the matching process, ensuring that the right candidates are suggested for the right projects. By analyzing candidate backgrounds and project requirements through AI, we aim to increase the conversion rate from 'Applied' to 'Accepted'.

## 🛠️ Tech Stack
* **Language:** Python 3.9+
* **Data Sources:** * **Podio API:** To fetch EP profiles and application data.
    * **Google Sheets API:** To pull real-time project lists from the OGT Tracker.
* **AI Engine:** OpenAI GPT-4o (or LangChain) for semantic matching.
* **Data Manipulation:** Pandas

## 🌟 Key Features
- **Automated EP Data Retrieval:** Connects to Podio to extract background, skills, and preferences.
- **Tracker Integration:** Syncs with the Google Sheets OGT Tracker to keep project lists up-to-date.
- **Smart Matching:** AI-driven analysis that scores the compatibility between an EP and a project.
- **Personalized Recommendations:** Generates a brief explanation of *why* a project is a good fit for a specific candidate.

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher.
- API Credentials for Podio and Google Cloud Console.
- OpenAI API Key.

### Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/Ernalmdr/aiesec-ogt-ai-matcher.git](https://github.com/Ernalmdr/aiesec-ogt-ai-matcher.git)
