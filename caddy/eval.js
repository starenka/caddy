const vm = require('vm');
const fs = require('fs');

function evalFile(path, context = {}) {
    const code = fs.readFileSync(path, 'utf8');

    let stdout = []
    const sandbox = {
        console: {
            log: (...args) => {
                stdout.push(args.join(' '));
            }
        },
        ...context
    };

    vm.createContext(sandbox);

    const result = vm.runInContext(code, sandbox);
    return { result, stdout };
}

function main() {
    if (process.argv.length < 2) {
        console.error('Usage: node eval.js <path_to_js_file>');
        process.exit(1);
    }

    try {
        const { result, stdout } = evalFile(process.argv[2]);
        stdout.forEach(line => console.log(line));
    } catch (error) {
        console.error("Error evaluating code:", error.message);
        process.exit(2);
    }
}

main();
