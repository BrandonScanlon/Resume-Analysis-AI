document.addEventListener('DOMContentLoaded', () => {
    // console.log('DOM Content Loaded');
    const form = document.getElementById('resumeForm');
    const fileInput = document.getElementById('resumeUpload');
    const selectedFileText = document.getElementById('selectedFile');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const analysisContent = document.getElementById('analysisContent');
    const errorMessage = document.getElementById('errorMessage');

    // console.log('Form elements:', {
    //     form: form,
    //     fileInput: fileInput,
    //     selectedFileText: selectedFileText,
    //     loadingDiv: loadingDiv,
    //     resultsDiv: resultsDiv,
    //     analysisContent: analysisContent,
    //     errorMessage: errorMessage
    // });

    // Update selected file name
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            if (!file.name.toLowerCase().endsWith('.pdf') && !file.name.toLowerCase().endsWith('.docx')) {
                errorMessage.textContent = 'Please upload a PDF or DOCX file';
                errorMessage.classList.remove('hidden');
                fileInput.value = '';
                selectedFileText.textContent = '';
            } else {
                selectedFileText.textContent = `Selected file: ${file.name}`;
                errorMessage.classList.add('hidden');
            }
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        // console.log('Form submitted');

        const file = fileInput.files[0];
        const jobDescription = document.getElementById('jobDescription').value;

        if (!file) {
            errorMessage.textContent = 'Please select a file to upload';
            errorMessage.classList.remove('hidden');
            return;
        }

        if (!jobDescription.trim()) {
            errorMessage.textContent = 'Please enter a job description';
            errorMessage.classList.remove('hidden');
            return;
        }

        errorMessage.classList.add('hidden');
        loadingDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
        
        const formData = new FormData();
        formData.append('resume', file);
        formData.append('job_description', jobDescription);

        try {
            // console.log('Sending request to server...');
            const response = await fetch('https://hangryboi-resume-analysis-ai.hf.space/api/analyze-resume', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                try {
                    const errorData = JSON.parse(errorText);
                    throw new Error(errorData.detail || 'Error processing resume');
                } catch (e) {
                    throw new Error('Server error: ' + errorText);
                }
            }

            const data = await response.json();
            // console.log("Received data:", data);
            
            // Check if analysis-results exists
            const analysisContainer = document.getElementById('analysis-results');
            // console.log('Analysis container:', analysisContainer);
            
            if (!analysisContainer) {
                // console.error('Analysis container not found. Creating it...');
                const resultsDiv = document.getElementById('results');
                const newContainer = document.createElement('div');
                newContainer.id = 'analysis-results';
                newContainer.className = 'space-y-8';
                resultsDiv.appendChild(newContainer);
            }
            
            // Display analysis results
            displayAnalysis(data.analysis);

            loadingDiv.classList.add('hidden');
            resultsDiv.classList.remove('hidden');
        } catch (error) {
            console.error('Error:', error);
            loadingDiv.classList.add('hidden');
            errorMessage.textContent = error.message;
            errorMessage.classList.remove('hidden');
        }
    });
});

function displayAnalysis(analysis) {
    // console.log('Starting displayAnalysis function');
    const analysisContainer = document.getElementById('analysis-results');
    // console.log('Analysis container:', analysisContainer);
    
    if (!analysisContainer) {
        console.error('Analysis container not found');
        return;
    }
    
    analysisContainer.innerHTML = '';

    // Clean up the analysis text and split into sections
    const cleanAnalysis = analysis.trim();
    // console.log('Clean analysis:', cleanAnalysis);
    
    // Split by numbered sections (1., 2., etc.)
    const sections = cleanAnalysis.split(/\d+\./).filter(section => section.trim());
    // console.log('Number of sections found:', sections.length);
    
    sections.forEach((section, index) => {
        // console.log(`Processing section ${index + 1}:`, section);
        
        if (section.trim()) {
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'analysis-section';
            
            // Handle the match score section differently
            if (section.includes('Overall Match Score')) {
                // console.log('Found match score section');
                const scoreMatch = section.match(/Overall Match Score: (\d+)/);
                const score = scoreMatch ? scoreMatch[1] : '0';
                // console.log('Extracted score:', score);
                sectionDiv.innerHTML = `
                    <h3>Overall Match Score</h3>
                    <div class="match-score">
                        <div class="score-circle" style="--score: ${score}">
                            <span>${score}</span>
                        </div>
                        <p>Match Score</p>
                    </div>
                `;
            } else {
                // For other sections, split into header and content
                const [header, ...content] = section.split('\n');
                const cleanHeader = header.replace(/\*/g, '').trim();
                // console.log('Processing section with header:', cleanHeader);
                // console.log('Section content:', content);
                // Add color class based on content for Overall Assessment
                let contentClass = '';
                if (cleanHeader === 'Overall Assessment:') {
                    // console.log('Found Overall Assessment section');
                    const text = content.join(' ').toLowerCase();
                    // console.log('Assessment text:', text);
                    
                    if (text.includes('strong alignment')) {
                        contentClass = 'assessment-strong';
                        // console.log('Setting strong alignment class');
                    } else if (text.includes('moderate alignment')) {
                        contentClass = 'assessment-moderate';
                        // console.log('Setting moderate alignment class');
                    } else if (text.includes('needs significant enhancement')) {
                        contentClass = 'assessment-weak';
                        // console.log('Setting weak alignment class');
                    }
                }
                // console.log('Final content class:', contentClass);
                
                sectionDiv.innerHTML = `
                    <h3>${cleanHeader}</h3>
                    <div class="section-content">
                        ${content.map(line => {
                            const trimmedLine = line.trim();
                            if (trimmedLine.startsWith('-')) {
                                const cleanLine = trimmedLine.substring(1).trim();
                                return `<p class="bullet-point">${cleanLine}</p>`;
                            }
                            return `<p class="${contentClass}">${trimmedLine}</p>`;
                        }).join('')}
                    </div>
                `;
            }
            
            analysisContainer.appendChild(sectionDiv);
        }
    });
}

// Add CSS for the new analysis display
const style = document.createElement('style');
style.textContent = `
    .analysis-section {
        margin-bottom: 2rem;
        padding: 1.5rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .analysis-section h3 {
        color: #2c3e50;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        font-weight: 600;
    }

    .section-content {
        margin-left: 1rem;
    }

    .bullet-point {
        margin: 0.5rem 0;
        padding-left: 1.5rem;
        position: relative;
        line-height: 1.5;
    }

    .bullet-point:before {
        content: "•";
        position: absolute;
        left: 0;
        top: 0;
        color: rgb(0, 0, 0);
        font-size: 2.5rem;
        line-height: 1;
        transform: translateY(-0.75rem);
    }

    .match-score {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 1rem 0;
    }

    .score-circle {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: conic-gradient(
            #3498db calc(var(--score) * 1%),
            #e0e0e0 calc(var(--score) * 1%)
        );
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }

    .score-circle:before {
        content: '';
        position: absolute;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: white;
    }

    .score-circle span {
        position: relative;
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
    }

    .match-score p {
        margin-top: 0.5rem;
        color: #666;
        font-size: 0.9rem;
    }

    .assessment-strong {
        color: #16a34a;
        font-weight: 500;
    }

    .assessment-moderate {
        color: #ca8a04;
        font-weight: 500;
    }

    .assessment-weak {
        color: #dc2626;
        font-weight: 500;
    }
`;
document.head.appendChild(style);