from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict
import os
from dotenv import load_dotenv
import PyPDF2
from docx import Document
import io
from sentence_transformers import SentenceTransformer, util
import numpy as np
import torch
import logging
import traceback
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Configure CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://brandonscanlon.github.io",  # GitHub Pages
        "https://brandonscanlon.github.io/Resume-Analysis-AI",  # GitHub Pages with repo name
        os.getenv("FRONTEND_URL", "")  # Additional frontend URL from env
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Mount static files
app.mount("/static", StaticFiles(directory="../Frontend/images"), name="static")

# Serve favicon
@app.get("/images/favicon.ico")
async def get_favicon():
    return FileResponse("../Frontend/images/favicon.ico")

# Load the pre-trained model
try:
    logger.info("Loading the pre-trained model...")
    # Using a model better suited for resume analysis
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    logger.error(traceback.format_exc())
    raise


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            # logger.info(f"PDF Page Content: {page_text[:200]}...")  # Log first 200 chars of each page
            # Clean up the text by removing excessive whitespace and newlines
            page_text = ' '.join(page_text.split())
            text += page_text + "\n\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        docx_file = io.BytesIO(file_bytes)
        doc = Document(docx_file)
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                logger.info(f"DOCX Paragraph: {paragraph.text[:200]}...")  # Log first 200 chars of each paragraph
                text.append(paragraph.text)
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def analyze_resume(resume_text: str, job_description: str) -> Dict:
    try:
        logger.info("=== Starting Resume Analysis ===")
        
        # Clean up text
        cleaned_text = re.sub(r'[^\w\s.,;:!?()\'\"-]', ' ', resume_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # Prepare prompt for the model
        prompt = f"""Analyze this resume against the job description and provide a detailed analysis.
        
Resume:
{cleaned_text}

Job Description:
{job_description}

Please analyze the match between the resume and job requirements, considering:
1. Overall alignment and match score (0-100)
2. Key strengths and relevant experience
3. Areas that need improvement
4. Specific suggestions for better alignment
5. Overall assessment

Format the response with clear sections and specific examples."""

        # Get embeddings for the full texts
        resume_embedding = model.encode(cleaned_text, convert_to_tensor=True)
        job_embedding = model.encode(job_description, convert_to_tensor=True)
        
        # Calculate overall similarity score
        similarity = util.pytorch_cos_sim(resume_embedding, job_embedding)[0][0].item()
        match_score = int((similarity + 1) * 50)  # Convert to 0-100 scale
        
        # Generate analysis using the model's understanding
        analysis = f"""
        1. Overall Match Score: {match_score}/100
        
        2. Key Strengths:
        {generate_strengths(cleaned_text, job_description)}
        
        3. Suggested Improvements:
        {generate_improvements(cleaned_text, job_description)}
        
        4. Areas that need attention:
        {generate_gaps(cleaned_text, job_description)}
        
        5. Overall Assessment:
        {generate_assessment(match_score, cleaned_text, job_description)}
        """
        
        return {
            "analysis": analysis,
            "match_score": match_score
        }
    except Exception as e:
        logger.error(f"Error in analyze_resume: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def generate_strengths(resume: str, job_desc: str) -> str:
    """Generate strengths based on semantic understanding."""
    # Get embeddings for key sections
    resume_sections = [s.strip() for s in resume.split('.') if s.strip()]
    job_requirements = [s.strip() for s in job_desc.split('.') if s.strip()]
    
    resume_embeddings = model.encode(resume_sections, convert_to_tensor=True)
    job_embeddings = model.encode(job_requirements, convert_to_tensor=True)
    
    # Find strong matches
    similarity_matrix = util.pytorch_cos_sim(resume_embeddings, job_embeddings)
    strong_matches = []
    
    for i, job_req in enumerate(job_requirements):
        similarities = similarity_matrix[:, i]
        top_idx = torch.argmax(similarities).item()
        if similarities[top_idx] > 0.6:
            strong_matches.append({
                'resume': resume_sections[top_idx],
                'requirement': job_req,
                'similarity': similarities[top_idx].item()
            })
    
    if not strong_matches:
        return "- No strong matches found"
    
    return '\n'.join([
        f"- Your experience in '{match['resume']}' strongly aligns with the requirement: '{match['requirement']}'."
        for match in sorted(strong_matches, key=lambda x: x['similarity'], reverse=True)[:5]
    ])

def generate_improvements(resume: str, job_desc: str) -> str:
    """Generate improvement suggestions based on semantic understanding."""
    resume_sections = [s.strip() for s in resume.split('.') if s.strip()]
    job_requirements = [s.strip() for s in job_desc.split('.') if s.strip()]
    
    resume_embeddings = model.encode(resume_sections, convert_to_tensor=True)
    job_embeddings = model.encode(job_requirements, convert_to_tensor=True)
    
    similarity_matrix = util.pytorch_cos_sim(resume_embeddings, job_embeddings)
    moderate_matches = []
    
    for i, job_req in enumerate(job_requirements):
        similarities = similarity_matrix[:, i]
        top_idx = torch.argmax(similarities).item()
        if 0.4 <= similarities[top_idx] <= 0.6:
            moderate_matches.append({
                'resume': resume_sections[top_idx],
                'requirement': job_req,
                'similarity': similarities[top_idx].item()
            })
    
    if not moderate_matches:
        return "- No moderate matches found"
    
    return '\n'.join([
        f"- Your experience with '{match['resume']}' partially matches the requirement: '{match['requirement']}'."
        for match in sorted(moderate_matches, key=lambda x: x['similarity'], reverse=True)[:3]
    ])

def generate_gaps(resume: str, job_desc: str) -> str:
    """Generate gap analysis based on semantic understanding."""
    resume_sections = [s.strip() for s in resume.split('.') if s.strip()]
    job_requirements = [s.strip() for s in job_desc.split('.') if s.strip()]
    
    resume_embeddings = model.encode(resume_sections, convert_to_tensor=True)
    job_embeddings = model.encode(job_requirements, convert_to_tensor=True)
    
    similarity_matrix = util.pytorch_cos_sim(resume_embeddings, job_embeddings)
    gaps = []
    
    for i, job_req in enumerate(job_requirements):
        similarities = similarity_matrix[:, i]
        max_similarity = torch.max(similarities).item()
        if max_similarity < 0.4:
            gaps.append({
                'requirement': job_req,
                'similarity': max_similarity
            })
    
    if not gaps:
        return "- No significant gaps found"
    
    return '\n'.join([
        f"- The requirement '{gap['requirement']}' is not well represented in your resume."
        for gap in sorted(gaps, key=lambda x: x['similarity'])[:3]
    ])

def generate_assessment(match_score: int, resume: str, job_desc: str) -> str:
    """Generate overall assessment based on match score and content analysis."""
    if match_score >= 80:
        return "Your resume shows strong alignment with the job requirements."
    elif match_score >= 50:
        return "Your resume shows moderate alignment with the job requirements."
    else:
        return "Your resume needs significant enhancement to better match the job requirements."

@app.post("/api/enhance-resume")
async def analyze_resume_endpoint(
    resume: UploadFile,
    job_description: str = Form(...)
) -> Dict:
    try:
        if not resume.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="File must be PDF or DOCX")
        
        # logger.info(f"Processing file: {resume.filename}")
        file_content = await resume.read()
        
        if resume.filename.lower().endswith('.pdf'):
            resume_text = extract_text_from_pdf(file_content)
        else:
            resume_text = extract_text_from_docx(file_content)
            
        # logger.info("Extracted text from resume, starting analysis...")
        analysis = analyze_resume(resume_text, job_description)
        return analysis
    except Exception as e:
        logger.error(f"Error in analyze_resume_endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 