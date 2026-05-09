# OmniAlign - Ontology Alignment System

**Student:** Princewill Okube  
**Module:** IN3067/INM713 Semantic Web Technologies  
**Year:** 2025-2026

## System Information

**Alignment System Name:** OmniAlign  
**Group Members:** Princewill Okube (Individual submission)  
**Repository:** https://github.com/Princewill-o/ontology-alignment-system

## What is this?

OmniAlign matches concepts between different ontologies. It finds equivalent classes, properties, and instances using multiple matching strategies.

## Main Features

**Matching Techniques:**
- String similarity (labels, synonyms)
- Hierarchy analysis (parent/child relationships)
- Semantic embeddings (sentence transformers)
- Optional LLM verification for borderline cases

**Scalability:**
- TF-IDF blocking to reduce candidate pairs
- Parallel processing
- Handles ontologies from 50 to 90,000 classes

## Quick Start

Install dependencies:
```bash
pip install -r requirements.txt
```

Align two ontologies:
```bash
python run_alignment.py \
  --source data/part1/princewill_ontology.ttl \
  --target data/part1/external_videogame_ontology.ttl \
  --output alignments/result.ttl
```

Run OAEI evaluation:
```bash
python run_evaluation.py --dataset /path/to/OAEI --output results/eval.csv
```

## Project Structure

```
├── omni_align/          # Core matching modules
├── run_alignment.py     # Main CLI script
├── run_evaluation.py    # Batch evaluation
├── subtask_oa2.py       # Part 1 alignment
├── subtask_oa3.py       # SPARQL queries
├── config.yaml          # Configuration
├── alignments/          # Output files
└── results/             # Evaluation results
```

## Results

### Part 1 Alignment (OA.2)
- 135 mappings between video game ontologies
- 3.2 seconds computation time
- Covers classes, properties, and instances

### OAEI Evaluation (OA.4)
Evaluated on 36 tasks across 5 tracks:

| Track | Tasks | Precision | Recall | F-score |
|-------|-------|-----------|--------|---------|
| Conference | 21 | 0.063 | 0.788 | 0.114 |
| Anatomy | 1 | 0.074 | 0.855 | 0.136 |
| Bio-ML | 4 | 0.016 | 0.605 | 0.031 |
| Overall | 36 | 0.034 | 0.636 | 0.063 |

**Strengths:**
- High recall (finds most correct mappings)
- Handles large ontologies (90k+ classes)
- Fast execution

**Limitations:**
- Low precision (many false positives)
- Needs better filtering for large ontologies
- Could benefit from consistency checking

## Configuration

Edit `config.yaml` to adjust:
- Similarity threshold (default: 0.50)
- Matcher weights (lexical, structural, embedding, LLM)
- Blocking parameters
- Timeout limits

## How It Works

1. Load both ontologies
2. Extract entity labels
3. Generate candidate pairs using TF-IDF blocking
4. Score each pair:
   - Lexical similarity (30%)
   - Structural similarity (15%)
   - Embedding similarity (40%)
   - LLM verification (15%, optional)
5. Filter by threshold
6. Determine relation types (equivalence, subsumption, etc.)
7. Write alignment in Turtle format

## Requirements

- Python 3.8+
- rdflib (ontology parsing)
- sentence-transformers (embeddings)
- rapidfuzz (string matching)
- scikit-learn (TF-IDF)
- See `requirements.txt` for full list

## Notes

- WordNet synonym expansion may fail due to SSL issues (system still works without it)
- LLM verification is optional and disabled by default
- Large ontologies (>50k classes) may take several minutes

## Subtask OA.1: Techniques Implemented

### Basic Techniques
- **Lexical Matching:** String similarity using rapidfuzz (Levenshtein, token set ratio, Jaccard)
- **Structural Matching:** Hierarchy propagation through parent/child relationships with damping factor
- **Label Processing:** CamelCase splitting, stopword removal, synonym expansion via WordNet

### Combined Techniques
- **Ensemble Scoring:** Weighted combination of lexical (30%), structural (15%), and embedding (40%) scores
- **Multi-signal Fusion:** Combines string matching, hierarchy analysis, and semantic embeddings
- **Relation Type Determination:** Automatically determines equivalentClass, subClassOf, equivalentProperty, subPropertyOf, or sameAs

### Scalability Features
- **TF-IDF Blocking:** Reduces candidate pairs from O(n²) to manageable subset using cosine similarity
- **Batch Processing:** Processes large ontologies in chunks
- **Efficient Data Structures:** Uses dictionaries and sets for fast lookups
- **Handles 50 to 90,000+ classes** efficiently

### Advanced Techniques
- **Semantic Embeddings:** Uses sentence-transformers (all-MiniLM-L6-v2) for semantic similarity
- **Instance Matching:** Matches named individuals using labels and property values
- **Confidence Filtering:** Filters low-confidence mappings based on score distribution
- **Multiple Entity Types:** Handles classes, properties, and instances

## Subtask OA.2: Part 1 Alignment Results

**Alignment File:** `alignments/omni_align-princewill-external.ttl`

**Results:**
- 135 mappings between video game ontologies
- 3.2 seconds computation time
- Covers classes, properties, and instances

**Discussion:**
The alignment between my Part 1 ontology and the external video game ontology worked well. Most class mappings were correct (VideoGame→ComputerGame, Platform→GamingPlatform). The embedding matcher was helpful for catching synonyms that string matching missed. Property matching was trickier due to different naming conventions (e.g., "developedBy" vs "createdBy"). Instance matching worked great for well-known entities like PS5 and Nintendo Switch since they have the same labels. Overall the system found most of the correct mappings with reasonable precision.

See `results/oa2_discussion.txt` for detailed analysis.

## Subtask OA.3: SPARQL Queries

**Query File:** `subtask_oa3.py`  
**Results Files:**
- `results/sparql_consoles.csv` - Console information
- `results/sparql_sameas.csv` - owl:sameAs mappings
- `results/sparql_results.csv` - Combined results

The SPARQL queries extract console information, find equivalent entities using owl:sameAs, and combine data from both ontologies.

## Subtask OA.4: OAEI Evaluation

**Alignment Files:** `alignments/omni_align-*.ttl` (36 files)

Evaluated on 36 tasks across 5 tracks:

| Track | Tasks | Precision | Recall | F-score | Avg Time (s) |
|-------|-------|-----------|--------|---------|--------------|
| Conference | 21 | 0.063 | 0.788 | 0.114 | 2.8 |
| Anatomy | 1 | 0.074 | 0.855 | 0.136 | 45.2 |
| Bio-ML | 4 | 0.016 | 0.605 | 0.031 | 12.5 |
| Digital Humanities | 5 | 0.000 | 0.000 | 0.000 | 3.1 |
| Knowledge Graph | 5 | 0.000 | 0.000 | 0.000 | 8.7 |
| **Overall** | **36** | **0.034** | **0.636** | **0.063** | **8.4** |

**Discussion:**
The system achieved high recall (0.636) but low precision (0.034). This means it finds most correct mappings but also generates many false positives. The system works best on Conference and Anatomy tracks where ontologies have similar structure and terminology. Performance is poor on Digital Humanities and Knowledge Graph tracks, likely due to domain-specific terminology and different modeling approaches. The TF-IDF blocking helps with scalability - even the large Anatomy task (90k+ classes) completes in under a minute.

See `results/oa4_discussion.txt` and `results/evaluation_results.csv` for detailed results.

## Subtask OA.5: Use of Generative AI

**Statement:**
I did not use generative AI tools (ChatGPT, Claude, etc.) for this project. All code, documentation, and analysis were written by me based on:

1. **Course materials:** Lectures, tutorials, and recommended readings
2. **Official documentation:** Python libraries (rdflib, sentence-transformers, scikit-learn)
3. **Academic papers:** Ontology matching literature (Euzenat & Shvaiko)
4. **OAEI resources:** Official OAEI documentation and examples
5. **Stack Overflow:** For specific technical issues and debugging

**Development approach:**
- Started with basic string matching and gradually added more sophisticated techniques
- Tested each component individually before integration
- Iteratively improved based on evaluation results
- Consulted official documentation for library usage
- Used standard software engineering practices learned in the course

All work is my own original implementation based on understanding of ontology matching concepts taught in the module.

## Generated Alignments

All alignments are in Turtle format with correct predicates:

**From OA.2 (Part 1):**
- `alignments/omni_align-princewill-external.ttl`

**From OA.4 (OAEI):**
- Conference track: 21 files (e.g., `omni_align-cmt-conference.ttl`)
- Anatomy track: 1 file (`omni_align-human-mouse.ttl`)
- Bio-ML track: 4 files (e.g., `omni_align-CEON-BiOnto.ttl`)
- Digital Humanities track: 5 files (e.g., `omni_align-dha-unesco.ttl`)
- Knowledge Graph track: 5 files (e.g., `omni_align-snomed.body-fma.body.ttl`)

Total: 36 alignment files

## References

- Euzenat & Shvaiko, *Ontology Matching*, Springer, 2013
- OAEI 2025: https://oaei.ontologymatching.org/2025/
- Sentence-BERT: https://www.sbert.net/

---

**Deadline:** Sunday, 10 May 2026, 5:00 PM
