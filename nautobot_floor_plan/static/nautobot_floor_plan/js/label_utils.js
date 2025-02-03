function generateLabels(start, end, step, labelType, incrementLetter) {
    let labels = [];
    
    if (labelType === "numbers") {
        // Numeric labels
        let startNum = parseInt(start, 10);
        let endNum = parseInt(end, 10);
        for (let i = startNum; i <= endNum; i += step) {
            labels.push(i.toString().padStart(2, '0')); // Pad with leading zeros if necessary
        }
    } else if (labelType === "letters") {
        // Letter labels
        let currentCharCode = start.charCodeAt(0);
        let endCharCode = end.charCodeAt(0);
        while (currentCharCode <= endCharCode) {
            labels.push(String.fromCharCode(currentCharCode));
            currentCharCode += step;
        }
    } else if (labelType === "alphanumeric" || labelType === "numalpha") {
        // Alphanumeric or Numalpha labels
        let numericPart = start.match(/\d+/)[0]; // Extract the numeric part
        let startLetters = start.match(/[A-Za-z]+/)[0]; // Extract the letter part
        let endLetters = end.match(/[A-Za-z]+/)[0]; // Extract the end letter part

        let currentLetters = startLetters;
        while (true) {
            labels.push(`${numericPart}${currentLetters}`);
            if (incrementLetter) {
                currentLetters = incrementString(currentLetters, step);
                if (currentLetters > endLetters) break;
            } else {
                currentLetters = incrementWholeString(currentLetters, step);
                if (currentLetters > endLetters) break;
            }
        }
    } else if (labelType === "roman") {
        // Roman numeral labels
        let startNum = romanToInt(start);
        let endNum = romanToInt(end);
        for (let i = startNum; i <= endNum; i += step) {
            labels.push(intToRoman(i));
        }
    } else if (labelType === "greek") {
        // Greek letter labels
        let startNum = greekToInt(start);
        let endNum = greekToInt(end);
        for (let i = startNum; i <= endNum; i += step) {
            labels.push(intToGreek(i));
        }
    } else if (labelType === "binary") {
        // Binary labels
        let startNum = parseInt(start, 10);
        let endNum = parseInt(end, 10);
        for (let i = startNum; i <= endNum; i += step) {
            labels.push(intToBinary(i));
        }
    } else if (labelType === "hex") {
        // Hexadecimal labels
        let startNum = parseInt(start, 16);
        let endNum = parseInt(end, 16);
        for (let i = startNum; i <= endNum; i += step) {
            labels.push(intToHex(i));
        }
    }

    return labels;
}

function incrementString(str, step) {
    let lastChar = str.slice(-1);
    let rest = str.slice(0, -1);
    let newChar = String.fromCharCode(lastChar.charCodeAt(0) + step);

    if (newChar > 'Z') {
        newChar = 'A';
        rest = incrementString(rest, 1);
    }

    return rest + newChar;
}

function incrementWholeString(str, step) {
    let newStr = '';
    for (let i = 0; i < str.length; i++) {
        let newChar = String.fromCharCode(str.charCodeAt(i) + step);
        if (newChar > 'Z') {
            newChar = 'A';
        }
        newStr += newChar;
    }
    return newStr;
}

function romanToInt(roman) {
    const romanMap = {I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000};
    let num = 0;
    for (let i = 0; i < roman.length; i++) {
        const current = romanMap[roman[i]];
        const next = romanMap[roman[i + 1]];
        if (next && current < next) {
            num -= current;
        } else {
            num += current;
        }
    }
    return num;
}

function intToRoman(num) {
    const romanMap = [
        [1000, 'M'], [900, 'CM'], [500, 'D'], [400, 'CD'],
        [100, 'C'], [90, 'XC'], [50, 'L'], [40, 'XL'],
        [10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'],
        [1, 'I']
    ];
    let roman = '';
    for (const [value, symbol] of romanMap) {
        while (num >= value) {
            roman += symbol;
            num -= value;
        }
    }
    return roman;
}

function greekToInt(greek) {
    const greekLetters = "αβγδεζηθικλμνξοπρστυφχψω";
    return greekLetters.indexOf(greek) + 1;
}

function intToGreek(num) {
    const greekLetters = "αβγδεζηθικλμνξοπρστυφχψω";
    return greekLetters[num - 1];
}

function intToBinary(num) {
    return '0b' + num.toString(2).padStart(4, '0');
}

function intToHex(num) {
    return '0x' + num.toString(16).toUpperCase().padStart(4, '0');
}

// Export the function for use in other modules
export { generateLabels };
