const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = 8080;
const BACKEND = 'http://localhost:8000';

const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
    const parsedUrl = new URL(req.url, `http://localhost:${PORT}`);
    const pathname = parsedUrl.pathname;

    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // Proxy API requests to backend (only API paths, not static files)
    const API_PATTERNS = [
        '/upload', '/api/', '/jobs/', '/job/', '/generate', '/extract/',
        '/user-profile', '/tracker', '/payment', '/session', '/cover-letter',
        '/fetch-job', '/resumes/', '/beta/', '/templates/', '/letter-evolution/',
        '/salary/', '/industries/', '/ats/', '/auth/', '/health', '/analyze',
        '/polish', '/translate', '/match', '/learning/', '/extract/', '/ai/'
    ];
    
    const shouldProxy = API_PATTERNS.some(p => pathname.startsWith(p));
    
    if (shouldProxy) {
        const backendUrl = BACKEND + pathname + (parsedUrl.search || '');
        
        const options = {
            hostname: 'localhost',
            port: 8000,
            path: pathname + (parsedUrl.search || ''),
            method: req.method,
            headers: req.headers
        };

        const proxyReq = http.request(options, (proxyRes) => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(res);
        });

        req.pipe(proxyReq);
        return;
    }

    // Serve static files
    let filePath = pathname === '/' ? '/index-zh.html' : pathname;
    filePath = path.join(__dirname, filePath);

    const ext = path.extname(filePath);
    const contentType = mimeTypes[ext] || 'text/plain';

    fs.readFile(filePath, (err, data) => {
        if (err) {
            res.writeHead(404, { 'Content-Type': 'text/plain' });
            res.end('File not found: ' + pathname);
            return;
        }
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(data);
    });
});

server.listen(PORT, () => {
    console.log(`Frontend server running at http://localhost:${PORT}`);
    console.log(`API proxy to ${BACKEND}`);
});
