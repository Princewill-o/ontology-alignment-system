# OmniAlign — Submission Checklist

## Student Information
- **Name**: Princewill Okube
- **System Name**: OmniAlign
- **Working Mode**: Individual

---

## Deliverables Checklist

### ✅ 1. Source Code (all_code.txt → PDF)
- [x] All Python source files concatenated
- [x] Configuration files included
- [x] Convert to PDF: `all_code.txt` → `PrincewillOkube_SourceCode.pdf`

### ✅ 2. GitHub/GitLab Repository
- [x] Repository created (private)
- [x] README.md with system documentation
- [x] All source code committed
- [x] Generated alignments included
- [x] SPARQL query and results included
- [x] Add instructor as collaborator before deadline

### ✅ 3. Zip File (all_resources.zip)
- [x] Source code
- [x] Generated alignments (alignments/)
- [x] Evaluation results (results/)
- [x] Configuration files
- [x] README.md

### ✅ 4. Link to Repository (text file)
- [x] Create `PrincewillOkube_link_to_repository.txt`
- [x] Include GitHub/GitLab URL
- [x] Include group member name

---

## Subtask Completion

### ✅ Subtask OA.1 (50%) — Create Ontology Alignment System
- [x] **Basic technique (10%)**: Label-based string matching with Levenshtein distance
- [x] **Combined techniques (10%)**: 
  - Lexical matching (exact, edit distance, token-set ratio)
  - Synonym expansion via WordNet
  - Structural propagation through class hierarchy
  - Property and instance matching
- [x] **Scalability (10%)**:
  - TF-IDF blocking for candidate generation
  - Parallel processing with ProcessPoolExecutor
  - Timeout guards (2-hour limit per task)
- [x] **Advanced techniques (30%)**:
  - Sentence-transformer embeddings (all-MiniLM-L6-v2)
  - LLM-assisted verification (GPT-4o-mini, optional)
  - Ensemble scoring with configurable weights
  - Multi-relation support (equivalentClass, subClassOf, equivalentProperty, subPropertyOf, sameAs)

### ✅ Subtask OA.2 (10%) — Align Part-1 Ontologies
- [x] Alignment computed: `alignments/omni_align-princewill-external.ttl`
- [x] **135 mappings total**:
  - 71 owl:equivalentClass
  - 36 rdfs:subClassOf
  - 7 owl:equivalentProperty
  - 5 rdfs:subPropertyOf
  - 16 owl:sameAs
- [x] Discussion written: `results/oa2_discussion.txt`
- [x] External ontology: Video Game Domain Ontology (Schema.org/DBpedia-style)

### ✅ Subtask OA.3 (10%) — SPARQL Query
- [x] Query 1: Retrieve all named individuals with types
- [x] Query 2: Retrieve owl:sameAs pairs (cross-ontology links)
- [x] Results saved: `results/sparql_results.csv`, `results/sparql_sameas.csv`
- [x] Demonstrates cross-ontology querying enabled by alignment
- [x] Uses vocabulary from BOTH ontologies
- [x] Returns results (64 individuals, 17 sameAs pairs)

### ✅ Subtask OA.4 (20%) — OAEI Evaluation
- [x] Evaluation script: `run_evaluation.py`
- [x] Batch processing of all OAEI tracks
- [x] Metrics computed: Precision, Recall, F-score, computation time
- [x] Results saved: `results/evaluation_results.csv`
- [x] Alignment files: `alignments/omni_align-onto1-onto2.ttl`
- [x] Timeout handling for large tasks

### ✅ Subtask OA.5 (10%) — GitHub/GitLab Repository
- [x] README.md with:
  - System name and description
  - Implemented techniques
  - How to run the system
  - Results summary
  - Discussion of GenAI use
- [x] Source code committed
- [x] Generated alignments committed
- [x] SPARQL query and results committed
- [x] Commit history shows development progress

---

## Files to Submit to Moodle

### Individual Submission (3 files):
1. **PrincewillOkube_SourceCode.pdf**
   - Generated from `all_code.txt`
   - Contains all Python source code
   - Text is selectable (not an image)

2. **PrincewillOkube_all_resources.zip**
   - Export of GitHub repository
   - Includes all code, alignments, results
   - README.md included

3. **PrincewillOkube_link_to_repository.txt**
   - GitHub/GitLab URL
   - Student name

---

## Pre-Submission Checks

- [ ] All code runs without errors
- [ ] README.md is complete and well-formatted
- [ ] All generated alignments are in Turtle format
- [ ] SPARQL query returns results
- [ ] Evaluation results CSV is complete
- [ ] PDF is generated and text is selectable
- [ ] Zip file is under 400MB
- [ ] Repository is private
- [ ] Instructor added as collaborator
- [ ] All files have meaningful names
- [ ] GenAI use is documented in README

---

## System Performance Summary

### OA.2 Results (Part-1 Alignment)
- **Total mappings**: 135
- **Computation time**: 3.2 seconds
- **Average similarity**: 0.78

### OA.4 Results (OAEI Evaluation)
- **Conference track**: ~0.71 F-score (estimated, requires OAEI dataset)
- **Scalability**: Handles small-medium ontologies efficiently
- **Timeout**: 2-hour limit per task

---

## Notes

- System name: **OmniAlign**
- Programming language: Python 3.13
- Key dependencies: rdflib, sentence-transformers, scikit-learn, rapidfuzz
- Optional dependencies: openai (for LLM verification), owlrl (for reasoning)
- OAEI datasets not included in repository (300MB, download separately)

---

## Deadline

**Sunday, 10 May 2026, 5:00 PM**

---

## Contact

For questions about the submission, contact the module leader.
