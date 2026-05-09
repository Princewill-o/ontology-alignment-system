# 📦 OmniAlign - Submission Package

## 🎯 Ready to Submit

**Student:** Princewill Okube  
**Module:** IN3067/INM713 Semantic Web Technologies  
**Deadline:** Sunday, 10 May 2026, 5:00 PM

---

## 📁 Submission Files (Upload These 3 Files)

### 1️⃣ PrincewillOkube_all_resources.zip
**Size:** 2.1 MB  
**Contains:**
```
PrincewillOkube_all_resources/
├── omni_align/                    # Core package (6 modules)
│   ├── aligner.py                 # Main orchestration
│   ├── ontology_utils.py          # Loading & preprocessing
│   ├── matchers.py                # Matching algorithms
│   ├── scoring.py                 # Ensemble scoring
│   ├── alignment_writer.py        # Output formatting
│   └── evaluator.py               # Evaluation metrics
├── run_alignment.py               # Main CLI script
├── run_evaluation.py              # OAEI evaluation
├── subtask_oa2.py                 # Part 1 alignment
├── subtask_oa3.py                 # SPARQL queries
├── config.yaml                    # Configuration
├── requirements.txt               # Dependencies
├── README.md                      # Documentation
├── data/                          # Input ontologies
├── alignments/                    # Output alignments (36 files)
└── results/                       # Evaluation results
```

### 2️⃣ PrincewillOkube_SourceCode.txt
**Size:** 79 KB (2,484 lines)  
**Contains:** All source code compiled into single text file

### 3️⃣ PrincewillOkube_link_to_repository.txt
**Size:** 411 bytes  
**Contains:** GitHub repository URL and information

---

## 🚀 How to Submit

### Step 1: Locate Files
```bash
cd Work2.0/SUBMISSION_FILES_FINAL/
ls -lh
```

### Step 2: Upload to Moodle
1. Go to Moodle submission page
2. Click "Add submission"
3. Upload these 3 files:
   - ✅ PrincewillOkube_all_resources.zip
   - ✅ PrincewillOkube_SourceCode.txt
   - ✅ PrincewillOkube_link_to_repository.txt
4. Click "Save changes"
5. Click "Submit assignment"

### Step 3: Verify
- Check all 3 files uploaded successfully
- Verify submission confirmation
- Note submission timestamp

---

## ✅ Pre-Submission Checklist

### Files Ready
- [x] All 3 files present in SUBMISSION_FILES_FINAL/
- [x] Zip file created successfully (2.1 MB)
- [x] Source code compiled (2,484 lines)
- [x] Repository link correct

### Code Quality
- [x] All modules working
- [x] No unnecessary files
- [x] Clean structure
- [x] Proper documentation
- [x] System tested

### Content Verified
- [x] 6 core modules included
- [x] All scripts present
- [x] Configuration files included
- [x] Results files included
- [x] README clear and complete

---

## 📊 Project Summary

### Code Statistics
- **Core Modules:** 6 (consolidated from 16)
- **Total Lines:** ~1,130 core code
- **Compiled Source:** 2,484 lines
- **Package Size:** 2.1 MB

### Features Implemented
✅ Lexical matching (string similarity)  
✅ Structural matching (hierarchy propagation)  
✅ Semantic embeddings (sentence-transformers)  
✅ Instance matching  
✅ TF-IDF candidate generation  
✅ Ensemble scoring  
✅ Multiple relation types  
✅ Turtle format output  

### Results Achieved
- **Part 1 (OA.2):** 135 mappings in 3.2 seconds
- **OAEI (OA.4):** 36 tasks completed
- **Average Recall:** 0.636
- **Handles:** 50 to 90,000+ classes

---

## 🧪 How to Test (After Extraction)

```bash
# Extract zip file
unzip PrincewillOkube_all_resources.zip
cd PrincewillOkube_all_resources

# Install dependencies
pip install -r requirements.txt

# Test imports
python3 -c "from omni_align.aligner import OmniAligner; print('✓ OK')"

# Run Part 1 alignment
python3 subtask_oa2.py

# Run OAEI evaluation
python3 run_evaluation.py --dataset /path/to/OAEI --output results/eval.csv
```

---

## 📝 Important Notes

### Expected Warnings
- **WordNet SSL warnings:** Expected and handled gracefully
- System works with or without WordNet
- Fallback stopwords provided

### First Run
- Embedding model download (~200MB)
- Only happens once
- Cached for future use

### Dependencies
All listed in requirements.txt:
- rdflib >= 6.0.0
- sentence-transformers >= 2.0.0
- rapidfuzz >= 2.0.0
- scikit-learn >= 1.0.0
- numpy >= 1.20.0
- nltk >= 3.6
- pyyaml >= 5.4

---

## 🔗 Repository

**GitHub:** https://github.com/Princewill-o/ontology-alignment-system

Repository contains:
- Same code as zip file
- Version history
- Documentation
- Issue tracking

---

## 📞 Support

If you need to verify anything:
1. Check SUBMISSION_INSTRUCTIONS.txt
2. Check FINAL_CHECKLIST.md
3. Review README.md in zip file

---

## ✨ Final Status

**🎉 READY FOR SUBMISSION**

All files prepared, tested, and verified.  
Upload to Moodle before deadline.

**Deadline:** Sunday, 10 May 2026, 5:00 PM

---

*Package prepared: 9 May 2026, 20:00*  
*Status: Complete and tested*
