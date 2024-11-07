const fs = require('fs');
const parser = require('@babel/parser');

if (process.argv.length < 3) {
    console.error('Usage: node jsrip.js <path-to-js-file> <function_prefix>');
    process.exit(1);
}

const filePath = process.argv[2];
const prefix = process.argv[3] || '';

try {
    const jsCode = fs.readFileSync(filePath, 'utf-8');
    const ast = parser.parse(jsCode, {
        sourceType: 'module',
        plugins: ['jsx', 'typescript'],
    });

    const functions = [];

    function findFunctions(node) {
        if (['FunctionDeclaration'].includes(node.type) && node.id.name.startsWith(prefix)) {
            const functionBody = jsCode.substring(node.body.start+1, node.body.end-1);
            functions.push({
                name: node.id.name,
                body: functionBody,
                len: functionBody.length,
            });
        }
        for (const key in node) {
            if (Array.isArray(node[key])) {
                node[key].forEach((childNode) => findFunctions(childNode));
            } else if (node[key] instanceof Object && node[key] !== null) {
                findFunctions(node[key]);
            }
        }
    }

    findFunctions(ast);

    console.log(JSON.stringify(functions, null, 2));
} catch (e) {
    console.error('Error reading or parsing the file:', e.message);
    process.exit(1);
}
