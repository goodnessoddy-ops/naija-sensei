# NaijaSensei

An offline-capable AI tutor for Nigerian secondary school students, powered by Gemma 4.
Built for the Gemma 4 Good Hackathon — Future of Education track.

## What it does

NaijaSensei is a conversational AI tutor that:
- Answers questions in English, Nigerian Pidgin, Yoruba, Igbo, and Hausa
- Grounds answers in 1,797 curriculum chunks across 13 WAEC subjects
- Works fully offline using local Gemma 3n E2B (true airplane-mode operation)
- Gracefully switches to cloud Gemma 4 26B when internet is available
- Accepts voice input and reads replies aloud

## Architecture

Hybrid edge/cloud:
- **Local always:** FastAPI server, ChromaDB retrieval, embedding model, conversation memory
- **Adaptive inference:** auto-switches between cloud Gemma 4 26B and local Gemma 3n E2B based on connectivity
- **Voice:** browser-native speech recognition and synthesis

## Subjects covered

Compulsory: English Language, Mathematics
Sciences: Physics, Chemistry, Biology, Further Mathematics, Agricultural Science  
Arts: Government, Christian Religious Studies, Islamic Religious Studies
Commercial: Economics, Commerce, Financial Accounting

All curriculum sourced from official WAEC syllabi.

## Status

Work in progress. Submission for the Gemma 4 Good Hackathon, May 2026.
