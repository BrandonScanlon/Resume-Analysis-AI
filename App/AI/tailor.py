import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="transformers.utils.generic")

from sentence_transformers import SentenceTransformer, util
import numpy as np
import torch
import logging
import traceback
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import textwrap
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize model as None
model = None

def load_model():
    global model
    if model is None:
        try:
            logger.info("Loading the pre-trained model...")
            # Force CPU usage and limit memory
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
            
            # Clear any existing CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Use the smaller model
            model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            
            # Force garbage collection
            gc.collect()
            
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            logger.error(traceback.format_exc())
            raise

def cleanup_memory():
    """Helper function to clean up memory"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)

class ResumeSection:
    def __init__(self, name: str, content: List[str], order: int):
        self.name = name
        self.content = content
        self.order = order

def extract_sections(text: str) -> Dict[str, ResumeSection]:
    sections = {}
    current_section = "other"
    current_content = []
    order = 0
    
    # Common section headers with their canonical names
    section_headers = {
        r'professional summary|summary|profile': 'Professional Summary',
        r'experience|work history|employment': 'Professional Experience',
        r'education|academic': 'Education',
        r'skills|technical skills|core competencies': 'Skills',
        r'projects|key projects': 'Projects',
        r'achievements|accomplishments': 'Achievements',
        r'contact|personal information': 'Contact Information'
    }
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line is a section header
        is_header = False
        for pattern, section_name in section_headers.items():
            if re.search(pattern, line.lower()):
                # Save previous section if it exists
                if current_section != "other" and current_content:
                    sections[current_section] = ResumeSection(current_section, current_content, order)
                    order += 1
                current_section = section_name
                current_content = []
                is_header = True
                break
                
        if not is_header:
            current_content.append(line)
    
    # Save the last section
    if current_content:
        sections[current_section] = ResumeSection(current_section, current_content, order)
    
    return sections

def extract_skills(text: str) -> Set[str]:
    """Extract skills from text."""
    skills = set()
    
    # Enhanced skill patterns with better context
    patterns = [
        r'(?:proficient|expert|skilled|experienced|knowledge|strong background|familiar|competent|working knowledge|hands-on experience) (?:in|with) ([^.,]+)',
        r'([A-Z][A-Z0-9\s&]+) (?:development|programming|engineering|design|analysis|management)',
        r'([A-Z][A-Z0-9\s&]+) (?:framework|library|tool|platform|system|service)',
        r'([A-Z][A-Z0-9\s&]+) (?:certification|certified)'
    ]
    
    # Extract skills from patterns
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            skills.update([s.strip() for s in match.group(1).split(',')])
    
    # Extract standalone skills (words in all caps or with specific formatting)
    standalone_skills = re.findall(r'\b[A-Z][A-Z0-9\s&]+\b', text)
    skills.update(s.strip() for s in standalone_skills if len(s.split()) <= 3)
    
    return skills

def extract_experience(text: str) -> List[str]:
    """Extract experience requirements from job description."""
    experience = []
    
    # Common experience patterns
    patterns = [
        r'(?:required|must have|looking for|seeking).*?(?:years|experience).*?(?:\.|$)',
        r'(?:minimum|at least).*?(?:years|experience).*?(?:\.|$)',
        r'(?:experience with|experience in).*?(?:\.|$)',
        r'(?:proven track record|demonstrated experience).*?(?:\.|$)'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            exp = match.group(0).strip()
            if exp and len(exp.split()) >= 4:  # Ensure meaningful content
                experience.append(exp)
    
    return experience

def enhance_resume(resume_text: str, job_description: str) -> Dict:
    """Analyze resume against job description and provide dynamic suggestions."""
    try:
        # Ensure model is loaded
        load_model()
        
        logger.info("Starting resume analysis...")
        
        # Split text into sentences
        resume_sentences = [s.strip() for s in re.split(r'[.!?]', resume_text) if s.strip()]
        job_sentences = [s.strip() for s in re.split(r'[.!?]', job_description) if s.strip()]
        
        # Get embeddings for all sentences
        resume_embeddings = model.encode(resume_sentences, convert_to_tensor=True)
        job_embeddings = model.encode(job_sentences, convert_to_tensor=True)
        
        # Calculate similarity matrix
        similarity_matrix = util.pytorch_cos_sim(resume_embeddings, job_embeddings)
        
        # Find most relevant resume sentences for each job requirement
        relevant_sentences = []
        for i, job_sent in enumerate(job_sentences):
            similarities = similarity_matrix[:, i]
            top_indices = torch.topk(similarities, min(3, len(resume_sentences))).indices
            for idx in top_indices:
                if similarities[idx] > 0.3:  # Only include if similarity is meaningful
                    relevant_sentences.append({
                        'resume_sentence': resume_sentences[idx],
                        'job_requirement': job_sent,
                        'similarity': similarities[idx].item()
                    })
        
        # Calculate overall match score
        max_similarities = torch.max(similarity_matrix, dim=0)[0]
        match_score = int((torch.mean(max_similarities).item() + 1) * 50)
        
        # Generate dynamic analysis
        output = []
        output.append("Resume Analysis Results")
        output.append("=" * 20)
        output.append(f"Overall Match Score: {match_score}/100")
        
        # Clean up memory after processing
        cleanup_memory()
        
        return {
            "analysis": "\n".join(output),
            "match_score": match_score
        }
    except Exception as e:
        logger.error(f"Error in enhance_resume: {str(e)}")
        logger.error(traceback.format_exc())
        cleanup_memory()
        raise

def format_resume_section(section: ResumeSection, max_width: int = 80) -> List[str]:
    formatted_lines = []
    formatted_lines.append(section.name.upper())
    formatted_lines.append("=" * len(section.name))
    
    for line in section.content:
        if len(line) > max_width:
            wrapped_lines = textwrap.wrap(line, width=max_width)
            formatted_lines.extend(wrapped_lines)
        else:
            formatted_lines.append(line)
    
    return formatted_lines

def rewrite_experience(exp: Dict, job_description: str) -> str:
    """Rewrite experience to better match job requirements."""
    try:
        # Extract key requirements from job description
        requirements = re.findall(r'(?:required|must have|looking for|seeking).*?(?:\.|$)', job_description, re.IGNORECASE)
        requirements_text = ' '.join(requirements)
        
        # Get embeddings for comparison
        exp_embedding = model.encode(exp['text'], convert_to_tensor=True)
        req_embedding = model.encode(requirements_text, convert_to_tensor=True)
        
        # Calculate similarity
        similarity = util.pytorch_cos_sim(exp_embedding, req_embedding)[0][0].item()
        
        # If experience is highly relevant, enhance it
        if similarity > 0.5:
            # Extract action verbs and outcomes
            verbs = re.findall(r'\b(?:developed|designed|implemented|created|built|managed|led|optimized|improved|enhanced)\b', exp['text'], re.IGNORECASE)
            outcomes = re.findall(r'(?:increased|reduced|improved|enhanced|achieved|delivered).*?(?:\.|$)', exp['text'], re.IGNORECASE)
            
            # Create enhanced version
            enhanced_text = exp['text']
            if verbs and outcomes:
                enhanced_text = f"{verbs[0].capitalize()} {outcomes[0]}"
            
            return enhanced_text
        return exp['text']
    except Exception as e:
        logger.error(f"Error rewriting experience: {str(e)}")
        return exp['text']