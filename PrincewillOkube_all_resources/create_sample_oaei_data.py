#!/usr/bin/env python3
"""
Create sample OAEI datasets for testing and demonstration.
These are realistic miniature versions of actual OAEI tracks with:
- Challenging variations (synonyms, abbreviations, different granularity)
- Incomplete reference alignments (to simulate real-world scenarios)
- Noise and distractors
"""

import os
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL
from rdflib.namespace import SKOS, XSD

def create_conference_track():
    """Create sample Conference track ontologies and reference alignments."""
    os.makedirs("data/conference/ontologies", exist_ok=True)
    
    # CMT ontology (Conference Management Toolkit)
    cmt = Graph()
    CMT = Namespace("http://cmt#")
    cmt.bind("cmt", CMT)
    
    # Classes with variations
    cmt.add((CMT.Conference, RDF.type, OWL.Class))
    cmt.add((CMT.Conference, RDFS.label, Literal("Conference")))
    cmt.add((CMT.Paper, RDF.type, OWL.Class))
    cmt.add((CMT.Paper, RDFS.label, Literal("Paper")))
    cmt.add((CMT.Paper, SKOS.altLabel, Literal("Submission")))
    cmt.add((CMT.Author, RDF.type, OWL.Class))
    cmt.add((CMT.Author, RDFS.label, Literal("Author")))
    cmt.add((CMT.Reviewer, RDF.type, OWL.Class))
    cmt.add((CMT.Reviewer, RDFS.label, Literal("Reviewer")))
    cmt.add((CMT.Review, RDF.type, OWL.Class))
    cmt.add((CMT.Review, RDFS.label, Literal("Review")))
    cmt.add((CMT.ProgramCommitteeMember, RDF.type, OWL.Class))
    cmt.add((CMT.ProgramCommitteeMember, RDFS.label, Literal("Program Committee Member")))
    cmt.add((CMT.ProgramCommitteeMember, SKOS.altLabel, Literal("PC Member")))
    cmt.add((CMT.AcceptedPaper, RDF.type, OWL.Class))
    cmt.add((CMT.AcceptedPaper, RDFS.label, Literal("Accepted Paper")))
    cmt.add((CMT.AcceptedPaper, RDFS.subClassOf, CMT.Paper))
    
    # Properties
    cmt.add((CMT.writtenBy, RDF.type, OWL.ObjectProperty))
    cmt.add((CMT.writtenBy, RDFS.label, Literal("written by")))
    cmt.add((CMT.hasReview, RDF.type, OWL.ObjectProperty))
    cmt.add((CMT.hasReview, RDFS.label, Literal("has review")))
    cmt.add((CMT.assignedTo, RDF.type, OWL.ObjectProperty))
    cmt.add((CMT.assignedTo, RDFS.label, Literal("assigned to")))
    
    cmt.serialize("data/conference/ontologies/cmt.owl", format="xml")
    
    # Conference ontology (different terminology)
    conf = Graph()
    CONF = Namespace("http://conference#")
    conf.bind("conf", CONF)
    
    conf.add((CONF.Conference, RDF.type, OWL.Class))
    conf.add((CONF.Conference, RDFS.label, Literal("Conference")))
    conf.add((CONF.Contribution, RDF.type, OWL.Class))
    conf.add((CONF.Contribution, RDFS.label, Literal("Contribution")))
    conf.add((CONF.Contribution, SKOS.altLabel, Literal("Scientific Contribution")))
    conf.add((CONF.Person, RDF.type, OWL.Class))
    conf.add((CONF.Person, RDFS.label, Literal("Person")))
    conf.add((CONF.Reviewer, RDF.type, OWL.Class))
    conf.add((CONF.Reviewer, RDFS.label, Literal("Reviewer")))
    conf.add((CONF.Review, RDF.type, OWL.Class))
    conf.add((CONF.Review, RDFS.label, Literal("Review")))
    conf.add((CONF.ProgramCommitteeMember, RDF.type, OWL.Class))
    conf.add((CONF.ProgramCommitteeMember, RDFS.label, Literal("Programme Committee Member")))
    conf.add((CONF.AcceptedContribution, RDF.type, OWL.Class))
    conf.add((CONF.AcceptedContribution, RDFS.label, Literal("Accepted Contribution")))
    conf.add((CONF.AcceptedContribution, RDFS.subClassOf, CONF.Contribution))
    # Distractor class
    conf.add((CONF.Workshop, RDF.type, OWL.Class))
    conf.add((CONF.Workshop, RDFS.label, Literal("Workshop")))
    
    conf.add((CONF.writtenBy, RDF.type, OWL.ObjectProperty))
    conf.add((CONF.writtenBy, RDFS.label, Literal("written by")))
    conf.add((CONF.hasReview, RDF.type, OWL.ObjectProperty))
    conf.add((CONF.hasReview, RDFS.label, Literal("has review")))
    conf.add((CONF.reviewedBy, RDF.type, OWL.ObjectProperty))
    conf.add((CONF.reviewedBy, RDFS.label, Literal("reviewed by")))
    
    conf.serialize("data/conference/ontologies/conference.owl", format="xml")
    
    # Reference alignment (not all mappings - realistic scenario)
    ref = Graph()
    ref.add((CMT.Conference, OWL.equivalentClass, CONF.Conference))
    ref.add((CMT.Paper, OWL.equivalentClass, CONF.Contribution))
    ref.add((CMT.Author, RDFS.subClassOf, CONF.Person))
    ref.add((CMT.Reviewer, OWL.equivalentClass, CONF.Reviewer))
    ref.add((CMT.Review, OWL.equivalentClass, CONF.Review))
    ref.add((CMT.ProgramCommitteeMember, OWL.equivalentClass, CONF.ProgramCommitteeMember))
    ref.add((CMT.AcceptedPaper, OWL.equivalentClass, CONF.AcceptedContribution))
    ref.add((CMT.writtenBy, OWL.equivalentProperty, CONF.writtenBy))
    ref.add((CMT.hasReview, OWL.equivalentProperty, CONF.hasReview))
    # Note: assignedTo vs reviewedBy are related but not equivalent (inverse)
    
    ref.serialize("data/conference/cmt-conference.ttl", format="turtle")
    
    # Edas ontology (different structure)
    edas = Graph()
    EDAS = Namespace("http://edas#")
    edas.bind("edas", EDAS)
    
    edas.add((EDAS.Conference, RDF.type, OWL.Class))
    edas.add((EDAS.Conference, RDFS.label, Literal("Conference")))
    edas.add((EDAS.Document, RDF.type, OWL.Class))
    edas.add((EDAS.Document, RDFS.label, Literal("Document")))
    edas.add((EDAS.Person, RDF.type, OWL.Class))
    edas.add((EDAS.Person, RDFS.label, Literal("Person")))
    edas.add((EDAS.Reviewer, RDF.type, OWL.Class))
    edas.add((EDAS.Reviewer, RDFS.label, Literal("Reviewer")))
    edas.add((EDAS.PCMember, RDF.type, OWL.Class))
    edas.add((EDAS.PCMember, RDFS.label, Literal("PC Member")))
    # Distractor
    edas.add((EDAS.Submission, RDF.type, OWL.Class))
    edas.add((EDAS.Submission, RDFS.label, Literal("Submission")))
    
    edas.add((EDAS.writtenBy, RDF.type, OWL.ObjectProperty))
    edas.add((EDAS.writtenBy, RDFS.label, Literal("written by")))
    edas.add((EDAS.authoredBy, RDF.type, OWL.ObjectProperty))
    edas.add((EDAS.authoredBy, RDFS.label, Literal("authored by")))
    
    edas.serialize("data/conference/ontologies/edas.owl", format="xml")
    
    # Reference alignment cmt-edas (partial)
    ref2 = Graph()
    ref2.add((CMT.Conference, OWL.equivalentClass, EDAS.Conference))
    ref2.add((CMT.Paper, RDFS.subClassOf, EDAS.Document))
    ref2.add((CMT.Author, RDFS.subClassOf, EDAS.Person))
    ref2.add((CMT.Reviewer, OWL.equivalentClass, EDAS.Reviewer))
    ref2.add((CMT.ProgramCommitteeMember, OWL.equivalentClass, EDAS.PCMember))
    ref2.add((CMT.writtenBy, OWL.equivalentProperty, EDAS.writtenBy))
    # Note: Paper vs Submission are related but reference doesn't include it
    
    ref2.serialize("data/conference/cmt-edas.ttl", format="turtle")
    
    # Add EKAW ontology for more tasks
    ekaw = Graph()
    EKAW = Namespace("http://ekaw#")
    ekaw.bind("ekaw", EKAW)
    
    ekaw.add((EKAW.Conference, RDF.type, OWL.Class))
    ekaw.add((EKAW.Conference, RDFS.label, Literal("Conference")))
    ekaw.add((EKAW.Article, RDF.type, OWL.Class))
    ekaw.add((EKAW.Article, RDFS.label, Literal("Article")))
    ekaw.add((EKAW.Researcher, RDF.type, OWL.Class))
    ekaw.add((EKAW.Researcher, RDFS.label, Literal("Researcher")))
    ekaw.add((EKAW.Reviewer, RDF.type, OWL.Class))
    ekaw.add((EKAW.Reviewer, RDFS.label, Literal("Reviewer")))
    
    ekaw.add((EKAW.authoredBy, RDF.type, OWL.ObjectProperty))
    ekaw.add((EKAW.authoredBy, RDFS.label, Literal("authored by")))
    
    ekaw.serialize("data/conference/ontologies/ekaw.owl", format="xml")
    
    # Reference alignment cmt-ekaw
    ref3 = Graph()
    ref3.add((CMT.Conference, OWL.equivalentClass, EKAW.Conference))
    ref3.add((CMT.Paper, OWL.equivalentClass, EKAW.Article))
    ref3.add((CMT.Author, RDFS.subClassOf, EKAW.Researcher))
    ref3.add((CMT.Reviewer, OWL.equivalentClass, EKAW.Reviewer))
    ref3.add((CMT.writtenBy, OWL.equivalentProperty, EKAW.authoredBy))
    
    ref3.serialize("data/conference/cmt-ekaw.ttl", format="turtle")
    
    # Conference-EKAW alignment
    ref4 = Graph()
    ref4.add((CONF.Conference, OWL.equivalentClass, EKAW.Conference))
    ref4.add((CONF.Contribution, OWL.equivalentClass, EKAW.Article))
    ref4.add((CONF.Person, RDFS.subClassOf, EKAW.Researcher))
    ref4.add((CONF.Reviewer, OWL.equivalentClass, EKAW.Reviewer))
    ref4.add((CONF.writtenBy, OWL.equivalentProperty, EKAW.authoredBy))
    
    ref4.serialize("data/conference/conference-ekaw.ttl", format="turtle")


def create_anatomy_track():
    """Create sample Anatomy track with challenging variations."""
    os.makedirs("data/anatomy/ontologies", exist_ok=True)
    
    # Mouse anatomy (with abbreviations and variations)
    mouse = Graph()
    MOUSE = Namespace("http://mouse.owl#")
    mouse.bind("mouse", MOUSE)
    
    # Anatomical structures with variations
    structures = [
        ("Brain", "Brain", "Cerebrum"),
        ("Heart", "Heart", "Cardiac Muscle"),
        ("Liver", "Liver", "Hepatic Organ"),
        ("Kidney", "Kidney", "Renal Organ"),
        ("Lung", "Lung", "Pulmonary Organ"),
        ("Stomach", "Stomach", "Gastric Organ"),
        ("Intestine", "Intestine", "Bowel"),
        ("SmallIntestine", "Small Intestine", "SI"),
        ("LargeIntestine", "Large Intestine", "Colon"),
        ("Muscle", "Muscle", "Muscular Tissue"),
        ("Bone", "Bone", "Osseous Tissue"),
        ("Skin", "Skin", "Cutaneous Tissue"),
        ("Nerve", "Nerve", "Neural Tissue"),
        ("BloodVessel", "Blood Vessel", "Vascular Structure"),
        ("Artery", "Artery", "Arterial Vessel"),
    ]
    
    for name, label, alt in structures:
        uri = MOUSE[f"MA_{name}"]
        mouse.add((uri, RDF.type, OWL.Class))
        mouse.add((uri, RDFS.label, Literal(label)))
        if alt:
            mouse.add((uri, SKOS.altLabel, Literal(alt)))
    
    # Add hierarchy
    mouse.add((MOUSE.MA_SmallIntestine, RDFS.subClassOf, MOUSE.MA_Intestine))
    mouse.add((MOUSE.MA_LargeIntestine, RDFS.subClassOf, MOUSE.MA_Intestine))
    mouse.add((MOUSE.MA_Artery, RDFS.subClassOf, MOUSE.MA_BloodVessel))
    
    mouse.serialize("data/anatomy/ontologies/mouse.owl", format="xml")
    
    # Human anatomy (NCI) with different terminology
    human = Graph()
    NCI = Namespace("http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#")
    human.bind("nci", NCI)
    
    human_structures = [
        ("Brain", "Brain", "Encephalon"),
        ("Heart", "Heart", None),
        ("Liver", "Liver", "Hepar"),
        ("Kidney", "Kidney", None),
        ("Lung", "Lung", None),
        ("Stomach", "Stomach", None),
        ("Intestine", "Intestine", "Gut"),
        ("SmallBowel", "Small Bowel", "Small Intestine"),
        ("LargeBowel", "Large Bowel", "Large Intestine"),
        ("MuscleTissue", "Muscle Tissue", "Muscular Tissue"),
        ("BoneTissue", "Bone Tissue", "Osseous Tissue"),
        ("SkinTissue", "Skin Tissue", "Integument"),
        ("NerveTissue", "Nerve Tissue", "Neural Tissue"),
        ("BloodVessel", "Blood Vessel", None),
        ("Artery", "Artery", None),
        # Distractor
        ("Vein", "Vein", "Venous Vessel"),
    ]
    
    for name, label, alt in human_structures:
        uri = NCI[f"NCI_{name}"]
        human.add((uri, RDF.type, OWL.Class))
        human.add((uri, RDFS.label, Literal(label)))
        if alt:
            human.add((uri, SKOS.altLabel, Literal(alt)))
    
    # Add hierarchy
    human.add((NCI.NCI_SmallBowel, RDFS.subClassOf, NCI.NCI_Intestine))
    human.add((NCI.NCI_LargeBowel, RDFS.subClassOf, NCI.NCI_Intestine))
    human.add((NCI.NCI_Artery, RDFS.subClassOf, NCI.NCI_BloodVessel))
    human.add((NCI.NCI_Vein, RDFS.subClassOf, NCI.NCI_BloodVessel))
    
    human.serialize("data/anatomy/ontologies/human.owl", format="xml")
    
    # Reference alignment (partial - realistic)
    ref = Graph()
    ref.add((MOUSE.MA_Brain, OWL.equivalentClass, NCI.NCI_Brain))
    ref.add((MOUSE.MA_Heart, OWL.equivalentClass, NCI.NCI_Heart))
    ref.add((MOUSE.MA_Liver, OWL.equivalentClass, NCI.NCI_Liver))
    ref.add((MOUSE.MA_Kidney, OWL.equivalentClass, NCI.NCI_Kidney))
    ref.add((MOUSE.MA_Lung, OWL.equivalentClass, NCI.NCI_Lung))
    ref.add((MOUSE.MA_Stomach, OWL.equivalentClass, NCI.NCI_Stomach))
    ref.add((MOUSE.MA_Intestine, OWL.equivalentClass, NCI.NCI_Intestine))
    ref.add((MOUSE.MA_SmallIntestine, OWL.equivalentClass, NCI.NCI_SmallBowel))
    ref.add((MOUSE.MA_LargeIntestine, OWL.equivalentClass, NCI.NCI_LargeBowel))
    ref.add((MOUSE.MA_Muscle, OWL.equivalentClass, NCI.NCI_MuscleTissue))
    ref.add((MOUSE.MA_Bone, OWL.equivalentClass, NCI.NCI_BoneTissue))
    ref.add((MOUSE.MA_Skin, OWL.equivalentClass, NCI.NCI_SkinTissue))
    ref.add((MOUSE.MA_Nerve, OWL.equivalentClass, NCI.NCI_NerveTissue))
    ref.add((MOUSE.MA_BloodVessel, OWL.equivalentClass, NCI.NCI_BloodVessel))
    ref.add((MOUSE.MA_Artery, OWL.equivalentClass, NCI.NCI_Artery))
    # Note: Vein is not in mouse ontology - distractor
    
    ref.serialize("data/anatomy/mouse-human.ttl", format="turtle")


def create_bioml_track():
    """Create sample Bio-ML track with challenging medical terminology."""
    os.makedirs("data/bioml/ontologies", exist_ok=True)
    
    # SNOMED CT subset with medical terminology
    snomed = Graph()
    SNOMED = Namespace("http://snomed.info/id/")
    snomed.bind("snomed", SNOMED)
    
    diseases = [
        ("73211009", "Diabetes mellitus", "DM"),
        ("38341003", "Hypertension", "High blood pressure"),
        ("195967001", "Asthma", "Bronchial asthma"),
        ("363346000", "Malignant neoplasm", "Cancer"),
        ("40733004", "Infectious disease", "Infection"),
        ("22298006", "Myocardial infarction", "Heart attack"),
        ("230690007", "Cerebrovascular accident", "Stroke"),
        ("13645005", "Chronic obstructive pulmonary disease", "COPD"),
        ("90708001", "Kidney disease", "Renal disease"),
        ("235856003", "Hepatic disease", "Liver disease"),
    ]
    
    for code, label, alt in diseases:
        uri = SNOMED[code]
        snomed.add((uri, RDF.type, OWL.Class))
        snomed.add((uri, RDFS.label, Literal(label)))
        snomed.add((uri, SKOS.prefLabel, Literal(label)))
        if alt:
            snomed.add((uri, SKOS.altLabel, Literal(alt)))
    
    snomed.serialize("data/bioml/ontologies/snomed.owl", format="xml")
    
    # FMA subset with different terminology
    fma = Graph()
    FMA = Namespace("http://purl.org/sig/fma/")
    fma.bind("fma", FMA)
    
    fma_diseases = [
        ("Diabetes", "Diabetes mellitus disorder"),
        ("Hypertension", "Hypertensive disorder"),
        ("Asthma", "Asthma disorder"),
        ("Cancer", "Malignant tumor"),
        ("Infection", "Infectious disorder"),
        ("MI", "Myocardial infarction"),
        ("CVA", "Stroke"),
        ("COPD", "Chronic obstructive lung disease"),
        ("RenalDisease", "Kidney disorder"),
        ("HepaticDisease", "Liver disorder"),
        # Distractor
        ("Pneumonia", "Pneumonia disorder"),
    ]
    
    for name, label in fma_diseases:
        uri = FMA[name]
        fma.add((uri, RDF.type, OWL.Class))
        fma.add((uri, RDFS.label, Literal(label)))
    
    fma.serialize("data/bioml/ontologies/fma.owl", format="xml")
    
    # Reference alignment (partial - some are challenging)
    ref = Graph()
    ref.add((SNOMED["73211009"], OWL.equivalentClass, FMA.Diabetes))
    ref.add((SNOMED["38341003"], OWL.equivalentClass, FMA.Hypertension))
    ref.add((SNOMED["195967001"], OWL.equivalentClass, FMA.Asthma))
    ref.add((SNOMED["363346000"], OWL.equivalentClass, FMA.Cancer))
    ref.add((SNOMED["40733004"], OWL.equivalentClass, FMA.Infection))
    ref.add((SNOMED["22298006"], OWL.equivalentClass, FMA.MI))
    ref.add((SNOMED["230690007"], OWL.equivalentClass, FMA.CVA))
    ref.add((SNOMED["13645005"], OWL.equivalentClass, FMA.COPD))
    ref.add((SNOMED["90708001"], OWL.equivalentClass, FMA.RenalDisease))
    ref.add((SNOMED["235856003"], OWL.equivalentClass, FMA.HepaticDisease))
    # Note: Pneumonia is not in SNOMED subset - distractor
    
    ref.serialize("data/bioml/snomed-fma.ttl", format="turtle")


def main():
    print("Creating realistic sample OAEI datasets...")
    print("These datasets include:")
    print("  - Challenging variations (synonyms, abbreviations)")
    print("  - Incomplete reference alignments")
    print("  - Noise and distractors")
    print()
    
    print("  Creating Conference track...")
    create_conference_track()
    
    print("  Creating Anatomy track...")
    create_anatomy_track()
    
    print("  Creating Bio-ML track...")
    create_bioml_track()
    
    print("\n✅ Realistic sample OAEI datasets created successfully!")
    print("\nDataset structure:")
    print("  data/conference/  (4 ontologies, 4 reference alignments)")
    print("  data/anatomy/     (2 ontologies, 1 reference alignment)")
    print("  data/bioml/       (2 ontologies, 1 reference alignment)")
    print("\nTotal: 6 alignment tasks across 3 tracks")


if __name__ == "__main__":
    main()
