from django.apps import AppConfig
from keybert import KeyBERT

from sentence_transformers import SentenceTransformer
import faiss
import os
import pdfplumber
import numpy as np
import re

class SuggestionConfig(AppConfig):
    name = 'suggestion'