# Habs Game Thread Comment Generator

This project trains a language model on r/Habs game day thread comments to generate similar comments.

The long-term goal is to:
- input a game event (e.g. “Suzuki scores on the powerplay”)
- generate multiple comments that would not feel out of place in a live r/Habs game thread
- eventually display the output in a Reddit-style web UI

This repository currently contains the data pipeline and an unconditional baseline model.


## Project Overview

### Current capabilities
- Scrapes r/Habs Game Thread comments (excluding post-game threads)
- Cleans and filters raw Reddit comments
- Trains an unconditional DistilGPT-2 model on gameday thread language
- Generates short, realistic comments

### Planned extensions
- Action-conditioned generation (reacting to specific in-game events)
- Retrieval-augmented generation for higher realism
- JavaScript frontend styled like a Reddit game thread
