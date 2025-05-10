# Resume Analysis AI

This is a FastAPI application that analyzes resumes against job descriptions using AI. The application uses the `sentence-transformers` library to perform semantic analysis and provide insights on how well a resume matches a job description.

## Features

- Resume analysis against job descriptions
- Support for PDF and DOCX files
- Semantic matching using AI
- Detailed analysis and suggestions
- RESTful API endpoints

## API Endpoints

- `POST /api/enhance-resume`: Analyze a resume against a job description
- `GET /health`: Health check endpoint

## Usage

1. Send a POST request to `/api/enhance-resume` with:
   - `resume`: PDF or DOCX file
   - `job_description`: Text of the job description

2. The response will include:
   - Analysis of the resume
   - Match score
   - Suggestions for improvement

## Technical Details

- Built with FastAPI
- Uses sentence-transformers for semantic analysis
- Supports PDF and DOCX file formats
- Optimized for Hugging Face Spaces deployment

## License

MIT License
