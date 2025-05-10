const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
    console.log('Request URL:', req.url);
    
    // Handle root URL by redirecting to src/pages
    if (req.url === '/') {
        res.writeHead(302, { 'Location': '/src/pages/' });
        res.end();
        return;
    }
    
    let filePath = '.' + req.url;
    
    // Special handling for favicon.ico
    if (filePath === './favicon.ico') {
        filePath = './src/pages/images/favicon.ico';
    }

    console.log('Looking for file at:', filePath);

    const extname = path.extname(filePath);
    let contentType = 'text/html';
    
    switch (extname) {
        case '.js':
            contentType = 'text/javascript';
            break;
        case '.css':
            contentType = 'text/css';
            break;
        case '.json':
            contentType = 'application/json';
            break;
        case '.png':
            contentType = 'image/png';
            break;
        case '.jpg':
            contentType = 'image/jpg';
            break;
        case '.ico':
            contentType = 'image/x-icon';
            break;
    }

    fs.readFile(filePath, (error, content) => {
        if (error) {
            console.log('Error reading file:', error);
            if(error.code === 'ENOENT') {
                console.log(`File not found: ${filePath}`);
                res.writeHead(404);
                res.end('File not found');
            } else {
                res.writeHead(500);
                res.end('Server Error: '+error.code);
            }
        } else {
            console.log('Serving file:', filePath, 'with content type:', contentType);
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
    console.log('Current working directory:', process.cwd());
}); 