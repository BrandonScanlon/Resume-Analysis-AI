try {
    // Use the deployed backend URL
    const response = await fetch('https://resume-analysis-ai.onrender.com/api/enhance-resume', {
        method: 'POST',
        body: formData,
        headers: {
            'Accept': 'application/json',
            'Origin': window.location.origin
        },
        mode: 'cors',
        credentials: 'omit'  // Don't send credentials for cross-origin requests
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        console.error('Server response:', errorText);
        try {
            const errorData = JSON.parse(errorText);
            throw new Error(errorData.detail || 'Error processing resume');
        } catch (e) {
            if (response.status === 404) {
                throw new Error('Backend service not found. Please check if the service is running.');
            } else if (response.status === 502) {
                throw new Error('Backend service is currently deploying or restarting. Please try again in a few minutes.');
            } else if (response.status === 0) {
                throw new Error('CORS error: Unable to connect to the backend service.');
            } else {
                throw new Error('Server error: ' + errorText);
            }
        }
    }
} catch (e) {
    console.error('Error:', e.message);
    throw e;
} 