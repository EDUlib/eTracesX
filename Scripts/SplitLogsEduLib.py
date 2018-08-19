#!/usr/bin/python

import sys
import getopt
import re
import gzip
#import random

NameDict = dict()
CoursList = [
    # Pattern, Filename
#    ('ITES\.1','ITES-A2015.txt'),

# La chimie, en route vers le génie I					Polytechnique Montréal	27 aout 2018	31 juil 2019	CHE101.5	course-v1:PolyMtl+CHE101.5+E2018
#    ('','.txt'),
# La chimie, en route vers le génie II					Polytechnique Montréal	27 aout 2018	31 juil 2019	CHE102.3	course-v1:PolyMtl+CHE102.3+E2018
#    ('','.txt'),

# -------------------------

# La glande mammaire et sa réponse à l’infection				Université de Montréal	12 juil 2018	05 juil 2019	MAMBOV1.2	course-v1:UMontreal+MAMBOV1.2+E2018
#    ('','.txt'),

# The udder and its response to infection					Université de Montréal	12 juil 2018	05 juil 2019	MASTBOV1.2	course-v1:UMontreal+MASTBOV1.2+E2018
#    ('','.txt'),
	# Réfugiés et demandeurs d'asile: réalités et pistes			Université de Montréal	20 juin 2018	20 juin 2019	EREFUG.1	course-v1:UMontreal+EREFUG.1+E2018
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))EREFUG\.1([\+ ]|(%2[B0])|(%252B))E2018','EREFUG.1-E2018.txt'),
	# Électricité et magnétisme, un duo de génie I				Polytechnique Montréal	06 juin 2018	01 aout 2018	EMI101.1	course-v1:PolyMtl+EMI101.1+P2018
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))EMI101\.1([\+ ]|(%2[B0])|(%252B))P2018','EMI101.1-P2018.txt'),
	# Introduction à l'expérience utilisateur					HEC Montréal		15 mai 2018	15 mai 2019	UX-101.1	course-v1:HEC+UX-101.1+P2018
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))UX-101\.1([\+ ]|(%2[B0])|(%252B))P2018','UX-101.1-P2018.txt'),
	# Réussir son démarrage d'entreprise - L'approche SynOpp			HEC Montréal		05 fev 2018	15 dec 2018	ENT-102.4	course-v1:HEC+ENT-102.4+HEC
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-102\.4([\+ ]|(%2[B0])|(%252B))HEC','ENT-102.4-HEC.txt'),

	# La chimie, en route vers le génie II					Polytechnique Montréal	13 dec 2017	31 juil 2018	CHE102.2	course-v1:PolyMtl+CHE102.2+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))CHE102\.2([\+ ]|(%2[B0])|(%252B))A2017','CHE102.2-A2017.txt'),
	# TEKPHY — Analyse du mouvement						Université de Montréal	02 oct 2017	30 juin 2019	TEKPHY3.2	course-v1:UMontreal+TEKPHY3.2+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))TEKPHY3\.2([\+ ]|(%2[B0])|(%252B))A2017','TEKPHY3.2-A2017.txt'),
	# TEKPHY — Activité physique et dépense énergétique			Université de Montréal	02 oct 2017	30 juin 2019	TEKPHY2.2	course-v1:UMontreal+TEKPHY2.2+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))TEKPHY2\.2([\+ ]|(%2[B0])|(%252B))A2017','TEKPHY2.2-A2017.txt'),
	# TEKPHY — Équilibre postural						Université de Montréal	02 oct 2017	30 juin 2019	TEKPHY1.2	course-v1:UMontreal+TEKPHY1.2+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))TEKPHY1\.2([\+ ]|(%2[B0])|(%252B))A2017','TEKPHY1.2-A2017.txt'),
	# Introduction à l'apprentissage profond					IVADO			19 juin 2018			IA-101		course-v1:IVADO+IA-101+P2018
    ('(course|block)-v1(:|(%3A)|(%253A))IVADO([\+ ]|(%2[B0])|(%252B))IA-101([\+ ]|(%2[B0])|(%252B))P2018','IA-101-P2018.txt'),

# -------------------------

	# La chimie, en route vers le génie I					Polytechnique Montréal	24 juil 2017	31 juil 2018	CHE101.4	course-v1:PolyMtl+CHE101.4+E2017
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))CHE101\.4([\+ ]|(%2[B0])|(%252B))E2017','CHE101.4-E2017.txt'),
	# Entrepreneuriat familial						HEC Montréal		12 mars 2018	01 juil 2018	ENT-103.2	course-v1:HEC+ENT-103.2+H2018
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-103\.2([\+ ]|(%2[B0])|(%252B))H2018','ENT-103.2-H2018.txt'),
	# La glande mammaire et sa réponse à l’infection				Université de Montréal	01 nov 2017	29 juin 2018	MAMBOV1.1	course-v1:UMontreal+MAMBOV1.1+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))MAMBOV1\.1([\+ ]|(%2[B0])|(%252B))A2017','MAMBOV1.1-A2017.txt'),
	# The udder and its response to infection					Université de Montréal	01 nov 2017	29 juin 2018	MASTBOV1.1	course-v1:UMontreal+MASTBOV1.1+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))MASTBOV1\.1([\+ ]|(%2[B0])|(%252B))A2017','MASTBOV1.1-A2017.txt'),

	# Introduction au marketing						HEC Montréal		29 Avril 2015	30 mai 2018	MKT-101		HEC/MKT-101/H2015			HEC/MKT-101/H2015
    ('HEC([/\.]|(%2F)|(%252F))MKT-101([/\.]|(%2F)|(%252F))H2015','MKT-101-H2015.txt'), 
    ('HEC([/\.]|(%2F)|(%252F))MKT-101\.2([/\.]|(%2F)|(%252F))P2014','MKT-101.2-P2014.txt'), # MKT-101.2???
    ('HEC([/\.]|(%2F)|(%252F))MKT-101\.1([/\.]|(%2F)|(%252F))H2012','MKT-101.1-H2012.txt'), # MKT-101.1???
	# Processus de raisonnement clinique					Université de Montréal	15 fev 2018	30 avril 2018	PRC.4		course-v1:UMontreal+PRC.4+H2018
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))PRC\.4([\+ ]|(%2[B0])|(%252B))H2018','PRC.4-H2018.txt'),
	# Le management								HEC Montréal		03 oct 2017	30 mars 2018	MAN-101.2	course-v1:HEC+MAN-101.2+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))MAN-101\.2([\+ ]|(%2[B0])|(%252B))A2017','MAN-101.2-A2017.txt'),
	# L'ingénieur, source de solutions durables				Polytechnique Montréal	24 janv 2018	21 mars 2018	DDI101.5	course-v1:PolyMtl+DDI101.5+H2018
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))DDI101\.5([\+ ]|(%2[B0])|(%252B))H2018','DDI101.5-H2018.txt'),
	# Outil d'aide à la scénarisation						Université de Montréal	15 oct 2017	18 mars 2018	OAS.3		course-v1:UMontreal+OAS.3+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))OAS\.3([\+ ]|(%2[B0])|(%252B))A2017','OAS.3-A2017.txt'),

	# Réussir son démarrage d'entreprise - L'approche SynOpp			HEC Montréal		14 nov 2016	04 fev 2018	ENT-102.3	course-v1:HEC+ENT-102.3+A2016		course-v1:HEC+ENT-102.3+A2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-102\.3([\+ ]|(%2[B0])|(%252B))A2016','ENT-102.3-A2016.txt'), 
	# Vers les limites ultimes de l'informatique				Université de Montréal	12 sept 2017	31 janv 2018	IFT-Limites	course-v1:UMontreal+IFT-Limites.2+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))IFT-Limites\.2([\+ ]|(%2[B0])|(%252B))A2017','IFT-Limites.2-A2017.txt'),
	# Décisions financières et gestion budgétaire				HEC Montréal		30 oct 2017	28 janv 2018	SC-102.2	course-v1:HEC+SC-102.2+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))SC-102.2([\+ ]|(%2[B0])|(%252B))A2017','SC-102.2-A2017.txt'),
	# L'esprit entrepreneurial						HEC Montréal		30 oct 2017	28 janv 2018	ENT-101.3	course-v1:HEC+ENT-101.3+E2017
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-101\.3([\+ ]|(%2[B0])|(%252B))E2017','ENT-101.3-E2017.txt'),
	# L'évaluation participative: mesurer les projets collectifs		Dynamo + HEC Montréal	30 oct 2017	15 dec 2017	COL-101.2	course-v1:HEC+COL-101.2+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))COL-101\.2([\+ ]|(%2[B0])|(%252B))A2017','COL-101.2-A2017.txt'),

	# L'ingénieur, source de solutions durables				Polytechnique Montréal	18 oct 2017	13 dec 2017	DDI101.4	course-v1:PolyMtl+DDI101.4+A2017
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))DDI101\.4([\+ ]|(%2[B0])|(%252B))A2017','DDI101.4-A2017.txt'),
	# Gestion des conflits							HEC Montréal		16 Nov 2015	31 oct 2017	GRH-101		HEC/GRH-101/A2015			HEC/GRH-101/A2015
    ('HEC([/\.]|(%2F)|(%252F))GRH-101([/\.]|(%2F)|(%252F))A2015','GRH-101-A2015.txt'), 
    ('HEC([/\.]|(%2F)|(%252F))GRH-101\.1([/\.]|(%2F)|(%252F))H2013','GRH-101.1-H2013.txt'), # GRH-101.1???
	# TEKPHY — Analyse du mouvement						Université de Montréal	24 Mai 2017	30 Juil 2017	TEKPHY3		course-v1:UMontreal+TEKPHY3+P2017	course-v1:UMontreal+TEKPHY3+P2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))TEKPHY3([\+ ]|(%2[B0])|(%252B))P2017','TEKPHY3-P2017.txt'),
	# L'ingénieur, source de solutions durables				Polytechnique Montréal	31 mai 2017	26 juil 2017	DDI101.3	course-v1:PolyMtl+DDI101.3+P2017
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))DDI101\.3([\+ ]|(%2[B0])|(%252B))P2017','DDI101.3-P2017.txt'),
	# Outil d'aide à la scénarisation						Université de Montréal	28 févr 2017	15 juil 2017	OAS.2		course-v1:UMontreal+OAS.2+P2017		course-v1:UMontreal+OAS.2+P2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))OAS\.2([\+ ]|(%2[B0])|(%252B))P2017','OAS.2-P2017.txt'), 

	# Décisions financières et gestion budgétaire				HEC Montréal		30 avr 2017	02 juil 2017	SC-102.1	HEC/SC-102.1/A2015			HEC/SC-102.1/A2015
    ('HEC([/\.]|(%2F)|(%252F))SC-102\.1([/\.]|(%2F)|(%252F))A2015','SC-102.1-A2015.txt'), 
	# Entrepreneuriat familial						HEC Montréal		13 mars 2017	30 juin 2017	ENT-103.1	course-v1:HEC+ENT-103.1+H2017		course-v1:HEC+ENT-103.1+H2017
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-103\.1([\+ ]|(%2[B0])|(%252B))H2017','ENT-103.1-H2017.txt'), 
	# Neurosciences : parole, musique						UdeM, ULB, G3		18 avr 2017	30 juin 2017	BRAMS.2		course-v1:UMontreal+BRAMS.2+P2017	course-v1:UMontreal+BRAMS.2+P2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))BRAMS\.2([\+ ]|(%2[B0])|(%252B))P2017','BRAMS.2-P2017.txt'), 
	# TEKPHY — Activité physique et dépense énergétique			Université de Montréal	05 Avril 2017	18 juin 2017	TEKPHY2		course-v1:UMontreal+TEKPHY2+P2017	course-v1:UMontreal+TEKPHY2+P2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))TEKPHY2([\+ ]|(%2[B0])|(%252B))P2017','TEKPHY2-P2017.txt'), 
	# Vers les limites ultimes de l'informatique				Université de Montréal	26 févr 2017	16 juin 2017	IFT-Limites	course-v1:UMontreal+IFT-Info-Theo+H2016	course-v1:UMontreal+IFT-Info-Theo+H2016    
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))IFT-Info-Theo([\+ ]|(%2[B0])|(%252B))H2016','IFT-Limites-H2016.txt'), 

	# La chimie, en route vers le génie II					Polytechnique Montréal	19 Avril 2017	14 juin 2017	CHE102		course-v1:PolyMtl+CHE102+P2017		course-v1:PolyMtl+CHE102+P2017
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))CHE102([\+ ]|(%2[B0])|(%252B))P2017','CHE102-P2017.txt'), 
	# Clinical Reasoning Process						Université de Montréal	01 mai 2017	12 juin 2017	CRP.1		course-v1:UMontreal+CRP.1+A2016		course-v1:UMontreal+CRP.1+A2016
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))CRP\.1([\+ ]|(%2[B0])|(%252B))A2016','CRP.1-A2016.txt'), 
	# Processus de raisonnement clinique					Université de Montréal	01 avr 2017	31 mai 2017	PRC.3		course-v1:UMontreal+PRC.3+P2017		course-v1:UMontreal+PRC.3+P2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))PRC\.3([\+ ]|(%2[B0])|(%252B))P2017','PRC.3-P2017.txt'), 
	# TEKPHY — Équilibre postural						Université de Montréal	15 févr 2017	30 avr 2017	TEKPHY1		course-v1:UMontreal+TEKPHY1+H2017	course-v1:UMontreal+TEKPHY1+H2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))TEKPHY1([\+ ]|(%2[B0])|(%252B))H2017','TEKPHY1-H2017.txt'), 
	# L'ingénieur, source de solutions durables				Polytechnique Montréal	01 Février 2017	01 avr 2017	DDI101.2	course-v1:PolyMtl+DDI101.2+H2017	course-v1:PolyMtl+DDI101.2+H2017
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))DDI101\.2([\+ ]|(%2[B0])|(%252B))H2017','DDI101.2-H2017.txt'), 
    
	# Promouvoir la santé et l'efficacité au travail				HEC Montréal		14 nov 2016	20 févr 2017	MAN-102.1	course-v1:HEC+MAN-102.1+A2016		course-v1:HEC+MAN-102.1+A2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))MAN-102\.1([\+ ]|(%2[B0])|(%252B))A2016','MAN-102.1-A2016.txt'), 
	# Le Management								HEC Montréal		14 nov 2016	20 févr 2017	MAN-101.1	course-v1:HEC+MAN-101.1+A2016		course-v1:HEC+MAN-101.1+A2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))MAN-101\.1([\+ ]|(%2[B0])|(%252B))A2016','MAN-101.1-A2016.txt'), 
	# La chimie, en route vers le génie I					Polytechnique Montréal	02 nov 2016	15 janv 2017	CHE101.3	course-v1:PolyMtl+CHE101.3+A2016	course-v1:PolyMtl+CHE101.3+A2016
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))CHE101\.3([\+ ]|(%2[B0])|(%252B))A2016','CHE101.3-A2016.txt'), 
	# L'ingénieur, source de solutions durables				Polytechnique Montréal	14 Sept 2016	14 nov 2016	DDI101		course-v1:PolyMtl+DDI101+A2015		course-v1:PolyMtl+DDI101+A2015
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))DDI101([\+ ]|(%2[B0])|(%252B))A2015','DDI101-A2015.txt'), 
	# Outil d’Aide à la Scénarisation pédagogique				Université de Montréal	08 Août 2016	25 oct 2016	ITES-OAS	course-v1:UMontreal+OAS.1+P2016		course-v1:UMontreal+OAS.1+P2016
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))OAS\.1([\+ ]|(%2[B0])|(%252B))P2016','OAS.1-P2016.txt'), 

	# Réussir son démarrage d'entreprise - L'approche SynOpp			HEC Montréal		16 mai 2016	30 juin 2016	ENT-102.2	course-v1:HEC+ENT-102.2+P2016		course-v1:HEC+ENT-102.2+P2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-102\.2([\+ ]|(%2[B0])|(%252B))P2016','ENT-102.2-P2016.txt'), 
	# L'évaluation participative de projets concertés				Dynamo + HEC Montréal	12 Avril 2016	27 juin 2016	COL-101.1	course-v1:HEC+d101+H2016		course-v1:HEC+d101+H2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))d101([\+ ]|(%2[B0])|(%252B))H2016','COL-101.1-H2016.txt'), 
	# Processus de raisonnement clinique					Université de Montréal	04 Avril 2016	11 juin 2016	PRC.2		course-v1:UMontreal+PRC.2+P2016		course-v1:UMontreal+PRC.2+P2016
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))PRC\.2([\+ ]|(%2[B0])|(%252B))P2016','PRC.2-P2016.txt'), 
	# La chimie, en route vers le génie					Polytechnique Montréal	05 Avril 2016	07 juin 2016	CHE101.2	course-v1:PolyMtl+CHE101.2+P2016	course-v1:PolyMtl+CHE101.2+P2016
	('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))CHE101\.2([\+ ]|(%2[B0])|(%252B))P2016','CHE101.2-P2016.txt'), 
	# L'esprit entrepreneurial						HEC Montréal		21 Mars 2016	26 mai 2016	ENT-101.2	course-v1:HEC+ENT-101.2+H2016		course-v1:HEC+ENT-101.2+H2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-101\.2([\+ ]|(%2[B0])|(%252B))H2016','ENT-101.2-H2016.txt'), 
    
	# Comprendre les états financiers						HEC Montréal		14 Déc 2015	21 mars 2016	SC-101.2	HEC/SC101.2/H2015			HEC/SC101.2/H2015
    ('HEC([/\.]|(%2F)|(%252F))SC101\.2([/\.]|(%2F)|(%252F))H2015','SC101.2-H2015.txt'), 
	# La chimie, en route vers le génie					Polytechnique Montréal	01 Nov 2015	12 janv 2016	CHE101		course-v1:PolyMtl+CHE101.1+E2015	course-v1:PolyMtl+CHE101.1+E2015
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))CHE101\.1([\+ ]|(%2[B0])|(%252B))E2015','CHE101.1-E2015.txt'), 
    ('PolyMtl([/\.]|(%2F)|(%252F))CHE101\.1([/\.]|(%2F)|(%252F))P2015','CHE101.1-P2015.txt'), # CHE101???
	# Innovations technopédagogiques en enseignement supérieur		Université de Montréal	13 Sept 2015	15 déc 2015	ITES		UMontreal/ITES.1/P2015			UMontreal/ITES.1/P2015
    ('UMontreal([/\.]|(%2F)|(%252F))ITES\.1([/\.]|(%2F)|(%252F))P2015','ITES.1-P2015.txt'), 
	# Processus de raisonnement clinique					Université de Montréal	05 Oct 2015	15 déc 2015	PRC		UMontreal/PRC.1/P2015			UMontreal/PRC.1/P2015
    ('UMontreal([/\.]|(%2F)|(%252F))PRC\.1([/\.]|(%2F)|(%252F))P2015','PRC.1-P2015.txt'), 
	# Réussir son démarrage d'entreprise - L'approche SynOpp			HEC Montréal		18 Mai 2015	28 juil 2015	ENT-102.1	HEC/ENT-102.1/P2015			HEC/ENT-102.1/P2015
    ('HEC([/\.]|(%2F)|(%252F))ENT-102\.1([/\.]|(%2F)|(%252F))P2015','ENT-102.1-P2015.txt'), 
	
# 	------------------------- NOT IN LOGS -------------------------
# L'esprit entrepreneurial						HEC Montréal		27 oct 2014	27 déc 2014	ENT-101.1	HEC/ENT-101.1/A2014			HEC/ENT-101.1/A2014
# Introduction au marketing						HEC Montréal		01 avr 2014	15 juin 2014	MKT-101.2	HEC/MKT-101.2/P2014			HEC/MKT-101.2/P2014
# Gestion des conflits							HEC Montréal		28 oct 2013	31 déc 2013	GRH-101.1	HEC/GRH-101.1/H2013			HEC/GRH-101.1/H2013
# Problèmes et politiques économiques: outils essentiels d'analyse	HEC Montréal		13 mai 2013	01 juil 2013	EA-101.1	HEC/EA-101.1/P2013			HEC/EA-101.1/P2013
# Comprendre les états financiers						HEC Montréal		11 mars 2013	11 juin 2013	SC-101.1	HEC/SC-101/P2013			HEC/SC-101/P2013
# Introduction au marketing						HEC Montréal		22 oct 2012	30 déc 2012	MKT-101.1	HEC/MKT-101.1/H2012			HEC/MKT-101.1/H2012

    ]
    
def main(argv):
    workingDir = ''    
    inputFile = ''
    zipped = False

    try:
        opts, args = getopt.getopt(argv,"hi:w:z",["ifile=","wdir=","zip"])
    except getopt.GetoptError:
        print 'test.py -i <inputFileName> -w <workingDir> -z'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -i <inputFileName> -w <workingDir> -z'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputFile = arg
        elif opt in ("-w", "--wdir"):
            workingDir = arg
        elif opt in ("-z", "--zip"):
            zipped = True

#    inputFile = 'test.txt'
#    workingDir = 'test'
     
    if inputFile == '' or workingDir == '':
        sys.exit()
    
    if workingDir[-1] != '/':
        workingDir += '/'
    inputFilePath = workingDir + inputFile
    print 'Input file is :', inputFilePath
    print 'Output directory is :', workingDir
    print "Zipped file :", zipped
    
    infile = ''
    restfile = ''
    if zipped:
        infile = gzip.open(inputFilePath + '.gz', 'rb')
        restfile = gzip.open(inputFilePath + '.leftover.txt.gz', 'wb')
        for i in xrange(0,len(CoursList)):
            CoursList[i] = (re.compile(CoursList[i][0]), gzip.open(workingDir + CoursList[i][1]+ '.gz', 'wb'))
    else:
        infile = open(inputFilePath, "r")
        restfile = open(inputFilePath + '.leftover.txt', 'w')
        for i in xrange(0,len(CoursList)):
            CoursList[i] = (re.compile(CoursList[i][0]), open(workingDir + CoursList[i][1], "w"))

    for oneline in infile:
        added = False
#		line = oneline
		line = anonymize(oneline)
        for pattern, outfile in CoursList:
            if pattern.search(line):
                outfile.write(line)
                if added == True:
                    print 'Line already added in another course :' + line
                added = True
        if added == False:
            restfile.write(line)
            
    infile.close()
    restfile.close()
    for pattern, outfile in CoursList:
        outfile.close()
        
def anonymize(aLine)
    pUser = re.compile('"username": "([\w.@&\-]*)"')
    mUser = pUser.findall(aLine)
    newLine = ''
    if len(mUser) == 1:
        if mUser[0] != '':
            if not NameDict.has_key(mUser[0]):
                newName = ''.join(random.SystemRandom().choice('0123456789ABCDEF') for _ in range(16))
                i = 0;
                while (newName in NameDict.values()) and i < 1000:
                    newName = ''.join(random.SystemRandom().choice('0123456789ABCDEF') for _ in range(16))
                    i = i+1;
                if i == 1000:
                    print "Can't find a name :", mUser[0]
                    sys.exit()
                NameDict[mUser[0]] = newName;
                print 'Username is :', mUser[0], ' ---  newName :', NameDict[mUser[0]]
            newLine = re.sub('"username": "'+ mUser[0] + '"', '"username": "' + NameDict[mUser[0]] + '"', aLine)
#            newLine = re.sub('"username": "'+ mUser[0] + '"', '"username": "' + mUser[0] + '"', aLine)
#            newLine = aLine
        else:
            newLine = aLine
    else:
        print "More than one username :", aLine
        sys.exit()
    return newLine

if __name__ == "__main__":
    main(sys.argv[1:])


