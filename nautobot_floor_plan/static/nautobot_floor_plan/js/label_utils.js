// Label converter classes mirroring Python implementation
// Corresponding Python implementations can be found in:
// - utils/label_converters.py for LabelConverter and its subclasses

/**
 * Base class for label converters.
 * This class defines the interface for converting labels to and from numeric values.
 */
class LabelConverter {
    constructor() {
        this._incrementPrefix = false; // Flag to indicate if the prefix should be incremented
    }

    toNumeric(label) { throw new Error("Not implemented"); } // Converts a label to a numeric value
    fromNumeric(number) { throw new Error("Not implemented"); } // Converts a numeric value back to a label
    setIncrementPrefix(incrementPrefix) { this._incrementPrefix = incrementPrefix; } // Sets the increment prefix flag
}

/**
 * Converter for binary labels.
 * Corresponding Python implementation: utils/label_converters.py
 */
class BinaryConverter extends LabelConverter {
    constructor(minDigits = 4) {
        super();
        this.minDigits = minDigits; // Minimum number of digits for binary representation
    }

    toNumeric(label) {
        if (typeof label === 'string' && label.startsWith('0b')) {
            return parseInt(label.slice(2), 2); // Convert binary string to number
        }
        return parseInt(label); // Convert decimal string to number
    }

    fromNumeric(number) {
        if (number < 0) throw new Error("Binary conversion requires positive numbers");
        const binary = number.toString(2).padStart(this.minDigits, '0'); // Convert number to binary string
        return `0b${binary}`; // Return binary string with '0b' prefix
    }
}

/**
 * Converter for hexadecimal labels.
 * Corresponding Python implementation: utils/label_converters.py
 */
class HexConverter extends LabelConverter {
    constructor(minDigits = 4) {
        super();
        this.minDigits = minDigits; // Minimum number of digits for hexadecimal representation
    }

    toNumeric(label) {
        if (typeof label === 'string' && label.startsWith('0x')) {
            return parseInt(label.slice(2), 16); // Convert hexadecimal string to number
        }
        return parseInt(label); // Convert decimal string to number
    }

    fromNumeric(number) {
        if (number < 0) throw new Error("Hex conversion requires positive numbers");
        const hex = number.toString(16).toUpperCase().padStart(this.minDigits, '0'); // Convert number to hex string
        return `0x${hex}`; // Return hex string with '0x' prefix
    }
}

/**
 * Converter for Roman numeral labels.
 * Corresponding Python implementation: utils/label_converters.py
 */
class RomanConverter extends LabelConverter {
    constructor() {
        super();
        this.romanValues = [
            ['M', 1000], ['CM', 900], ['D', 500], ['CD', 400],
            ['C', 100], ['XC', 90], ['L', 50], ['XL', 40],
            ['X', 10], ['IX', 9], ['V', 5], ['IV', 4], ['I', 1]
        ];
    }

    toNumeric(label) {
        if (!label) throw new Error("Roman numeral cannot be empty");

        let result = 0;
        let index = 0;
        label = label.toUpperCase();

        while (index < label.length) {
            // Try two-character combinations first
            if (index + 1 < label.length) {
                const doubleChar = label.slice(index, index + 2);
                const doubleValue = this.romanValues.find(([r]) => r === doubleChar);
                if (doubleValue) {
                    result += doubleValue[1];
                    index += 2;
                    continue;
                }
            }

            // Try single character
            const singleChar = label[index];
            const singleValue = this.romanValues.find(([r]) => r === singleChar);
            if (!singleValue) {
                throw new Error(`Invalid Roman numeral character at position ${index}`);
            }
            result += singleValue[1];
            index += 1;
        }

        return result; // Return the numeric value of the Roman numeral
    }

    fromNumeric(number) {
        if (number < 1 || number > 3999) {
            throw new Error("Number must be between 1 and 3999 for Roman numerals");
        }

        let result = '';
        let remaining = number;

        for (const [roman, value] of this.romanValues) {
            while (remaining >= value) {
                result += roman;
                remaining -= value;
            }
        }

        return result; // Return the Roman numeral representation
    }
}

/**
 * Converter for Greek letter labels.
 * Corresponding Python implementation: utils/label_converters.py
 */
class GreekConverter extends LabelConverter {
    constructor() {
        super();
        this.greekLetters = 'αβγδεζηθικλμνξοπρστυφχψω'; // Greek letters
    }

    toNumeric(label) {
        if (!label) throw new Error("Greek letter cannot be empty");

        const greekPart = label.toLowerCase();
        const index = this.greekLetters.indexOf(greekPart);

        if (index === -1) {
            throw new Error(`Invalid Greek letter: ${label}`);
        }

        return index + 1; // Return the numeric position of the Greek letter
    }

    fromNumeric(number) {
        if (number < 1 || number > this.greekLetters.length) {
            throw new Error(`Number must be between 1 and ${this.greekLetters.length}`);
        }
        return this.greekLetters[number - 1]; // Return the Greek letter corresponding to the numeric value
    }
}

/**
 * Converter for numalpha labels (alphanumeric with letters).
 * Corresponding Python implementation: utils/label_converters.py
 */
class NumalphaConverter extends LabelConverter {
    constructor() {
        super();
        this._prefix = "";
        this._start_label = "";
        this._increment_prefix = false;
    }

    toNumeric(label) {
        this._start_label = label;
        const [prefix, letters] = extractPrefixAndLetter(label);
        if (!letters) throw new Error(`Invalid numalpha label: ${label}`);
        this._prefix = prefix;

        if (this._increment_prefix) {
            // When incrementing last letter only, convert just the last letter
            const lastLetter = letters[letters.length - 1];
            return gridLetterToNumber(lastLetter);
        } else {
            // When not incrementing, convert the first letter since all letters will be the same
            return gridLetterToNumber(letters[0]);
        }
    }

    fromNumeric(number) {
        if (number < 1) throw new Error("Number must be positive");

        const [_, startLetters] = extractPrefixAndLetter(this._start_label);

        let letters;
        if (this._increment_prefix) {
            // Keep all but last letter from start label, only increment last letter
            const baseLetters = startLetters.slice(0, -1);
            const newLetter = gridNumberToLetter(number);
            letters = baseLetters + newLetter;
        } else {
            // When not incrementing prefix, use the same letter for all positions
            const letter = gridNumberToLetter(number);
            // Use the length from the start label
            letters = letter.repeat(startLetters.length);
        }

        return `${this._prefix}${letters}`;
    }

    setIncrementPrefix(value) {
        this._increment_prefix = value;
        // Reset the start label when changing increment mode
        if (this._start_label) {
            const [prefix, letters] = extractPrefixAndLetter(this._start_label);
            this._prefix = prefix;
        }
    }
}

/**
 * Converter for alphanumeric labels.
 * Corresponding Python implementation: utils/label_converters.py
 */
class AlphanumericConverter extends LabelConverter {
    constructor() {
        super();
        this._prefix = ""; // Prefix for the label
        this._numberOnly = false; // Flag to indicate if the label is purely numeric
        this._useLeadingZeros = false; // Flag to indicate if leading zeros should be used
        this._incrementPrefix = false; // Flag to indicate if the prefix should be incremented
        this._number = ""; // Store the numeric part of the label
    }

    toNumeric(label) {
        if (this._numberOnly) {
            // For numbers-only, check if the input has leading zeros
            if (!/^\d+$/.test(label)) {
                throw new Error(`Invalid number format: ${label}`);
            }
            this._useLeadingZeros = label.length > 1 && label[0] === "0"; // Check for leading zeros
            this._number = label;
            return parseInt(label, 10); // Convert to numeric value
        }

        // For alphanumeric, extract prefix and number parts
        const [prefix, number] = extractPrefixAndNumber(label);
        if (!/^\d+$/.test(number)) {
            throw new Error(`Invalid alphanumeric label: ${label}. Must have a numeric part.`);
        }

        this._prefix = prefix;
        this._number = number;
        this._useLeadingZeros = number.length > 1 && number[0] === "0"; // Check for leading zeros

        // If incrementing prefix, return the letter value, otherwise return the number
        return this._incrementPrefix ?
            gridLetterToNumber(prefix || "A") :
            parseInt(number, 10);
    }

    fromNumeric(number) {
        console.log(`Converting number: ${number}, incrementPrefix: ${this._incrementPrefix}, useLeadingZeros: ${this._useLeadingZeros}, number: ${this._number}`);

        if (this._numberOnly) {
            return this._useLeadingZeros ?
                number.toString().padStart(2, '0') :
                number.toString(); // Return formatted number
        }

        if (this._incrementPrefix) {
            // When incrementing prefix, keep the original number part
            const prefix = gridNumberToLetter(number);
            const numericPart = this._useLeadingZeros ?
                this._number :
                parseInt(this._number, 10).toString();
            return prefix + numericPart; // Return incremented label
        }

        // When not incrementing prefix, keep the original prefix
        return this._prefix + (this._useLeadingZeros ?
            number.toString().padStart(2, '0') :
            number.toString()); // Return formatted label
    }

    setNumberOnly(isNumberOnly) {
        this._numberOnly = isNumberOnly; // Set the number-only flag
    }

    setIncrementPrefix(incrementPrefix) {
        this._incrementPrefix = incrementPrefix; // Set the increment prefix flag
    }
}

/**
 * Converter for letter labels.
 * Corresponding Python implementation: utils/label_converters.py
 */
class LettersConverter extends LabelConverter {
    constructor() {
        super();
        this._currentValue = null; // Current value for the label
        this.MAX_VALUE = 18278; // Maximum value for letter labels (ZZZ)
    }

    toNumeric(label) {
        if (!label) {
            throw new Error("Label must be a non-empty string");
        }

        // Convert to uppercase before validation
        const upperLabel = label.toUpperCase();

        if (!/^[A-Z]+$/.test(upperLabel)) {
            throw new Error("Label must contain only letters");
        }

        return gridLetterToNumber(upperLabel); // Convert letter label to numeric value
    }

    fromNumeric(number) {
        // Ensure we're working with a positive number within range
        while (number < 1) {
            number += this.MAX_VALUE;
        }
        number = ((number - 1) % this.MAX_VALUE) + 1;

        return gridNumberToLetter(number); // Convert numeric value back to letter label
    }
}

// Utility functions mirroring Python implementation
// Corresponding Python implementations can be found in:
// - utils/general.py

function gridNumberToLetter(number) {
    let result = "";
    while (number > 0) {
        let remainder = number % 26;
        if (remainder === 0) remainder = 26; // Adjust for 0 remainder
        result = String.fromCharCode(64 + remainder) + result; // Convert to letter
        number = Math.floor((number - 1) / 26); // Update number for next iteration
    }
    return result; // Return the resulting letter string
}

function gridLetterToNumber(letter) {
    let result = 0;
    for (let i = 0; i < letter.length; i++) {
        result = result * 26 + (letter.charCodeAt(i) - 64); // Convert letter to numeric value
    }
    return result; // Return the numeric value
}

function extractPrefixAndLetter(label) {
    let prefix = "", letters = label;
    for (let i = 0; i < label.length; i++) {
        if (/[A-Za-z]/.test(label[i])) {
            prefix = label.substring(0, i); // Extract prefix
            letters = label.substring(i); // Extract letters
            break;
        }
    }
    return [prefix, letters]; // Return prefix and letters
}

function extractPrefixAndNumber(label) {
    let prefix = "", numbers = label;
    for (let i = 0; i < label.length; i++) {
        if (/[0-9]/.test(label[i])) {
            prefix = label.substring(0, i); // Extract prefix
            numbers = label.substring(i); // Extract numbers
            break;
        }
    }
    return [prefix, numbers]; // Return prefix and numbers
}

// Updated main label generation function
function generateLabels(start, end, step = 1, labelType, incrementLetter = false) {
    const converterMap = {
        'numalpha': NumalphaConverter,
        'alphanumeric': AlphanumericConverter,
        'numbers': AlphanumericConverter,
        'binary': BinaryConverter,
        'hex': HexConverter,
        'roman': RomanConverter,
        'greek': GreekConverter,
        'letters': LettersConverter
    };

    const ConverterClass = converterMap[labelType];
    if (!ConverterClass) {
        throw new Error(`Unsupported label type: ${labelType}`);
    }

    const converter = new ConverterClass();
    converter.setIncrementPrefix(incrementLetter);

    if (labelType === 'numbers') {
        converter.setNumberOnly(true);
    }

    try {
        // Validate start and end labels before conversion
        if (labelType === 'roman') {
            if (!isValidRoman(start) || !isValidRoman(end)) {
                throw new Error("Invalid input: Please enter valid Roman numerals.");
            }
        } else if (labelType === 'greek') {
            if (!isValidGreek(start) || !isValidGreek(end)) {
                throw new Error("Invalid input: Please enter valid Greek letters.");
            }
        } else if (labelType === 'numalpha' || labelType === 'alphanumeric') {
            if (!isValidNumAlpha(start) || !isValidNumAlpha(end)) {
                throw new Error("Invalid input: Please enter valid alphanumeric labels.");
            }
        }

        let startNum = converter.toNumeric(start);
        let endNum = converter.toNumeric(end);

        // Special range validation for numalpha when increment_letter is true
        if (labelType === 'numalpha' && incrementLetter) {
            // When incrementing letters in numalpha (e.g., 02AA to 02AJ),
            // we only care about the last letter's range
            const [startPrefix, startLetters] = extractPrefixAndLetter(start);
            const [endPrefix, endLetters] = extractPrefixAndLetter(end);

            if (startPrefix !== endPrefix) {
                throw new Error(`Prefix mismatch: ${startPrefix} != ${endPrefix}`);
            }
        } else {
            // For all other cases, perform the normal range validation
            const range = Math.abs(endNum - startNum);
            if (Math.abs(step) > range) {
                throw new Error(`Step value ${step} cannot be greater than the range between start (${start}) and end (${end}).`);
            }
        }

        const labels = [];

        // Special handling for letters with negative steps
        if (labelType === 'letters') {
            // If going backwards and end is less than start, we need to add MAX_VALUE to end
            if (step < 0 && endNum < startNum) {
                // No adjustment needed
            } else if (step < 0 && endNum > startNum) {
                endNum = endNum - converter.MAX_VALUE;
            } else if (step > 0 && endNum < startNum) {
                endNum = endNum + converter.MAX_VALUE;
            }

            let current = startNum;
            const condition = step > 0 ?
                () => current <= endNum :
                () => current >= endNum;

            while (condition()) {
                labels.push(converter.fromNumeric(current));
                current += step;
            }
            return labels;
        }

        // Handle positive and negative steps
        if (step > 0 && startNum > endNum) {
            throw new Error("With positive step, start value must be less than end value");
        }
        if (step < 0 && startNum < endNum) {
            throw new Error("With negative step, start value must be greater than end value");
        }

        // Validate ranges for specific types
        if (labelType === 'roman' && (startNum < 1 || endNum > 3999)) {
            throw new Error("Roman numerals must be between 1 and 3999");
        }
        if (labelType === 'greek' && (startNum < 1 || endNum > 24)) {
            throw new Error("Greek labels must be between 1 and 24");
        }
        if ((labelType === 'binary' || labelType === 'hex') && (startNum < 0 || endNum < 0)) {
            throw new Error(`${labelType.toUpperCase()} labels must be positive numbers`);
        }
        if (labelType === 'letters' && (startNum < 1 || endNum > 18278)) {
            throw new Error("Letters must be between A and ZZZ");
        }

        for (
            let i = startNum;
            step > 0 ? i <= endNum : i >= endNum;
            i += step
        ) {
            labels.push(converter.fromNumeric(i));
        }

        return labels;
    } catch (error) {
        console.error("Error generating labels:", error);
        return [`Error: ${error.message}`]; // Return the error message to display to the user
    }
}

// Validation functions
function isValidRoman(label) {
    // Implement logic to check if the label is a valid Roman numeral
    return /^[IVXLCDM]+$/.test(label); // Simple regex for Roman numerals
}

function isValidGreek(label) {
    // Implement logic to check if the label is a valid Greek letter
    const greekLetters = 'αβγδεζηθικλμνξοπρστυφχψω';
    return greekLetters.includes(label.toLowerCase());
}

function isValidNumAlpha(label) {
    // Implement logic to check if the label is a valid alphanumeric label
    return /^[A-Z0-9]+$/.test(label); // Example regex for alphanumeric
}

// Export for use in other files
export { generateLabels };
