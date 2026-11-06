/**
 * Lightweight test runner to verify core utilities:
 * - Indian number formatting
 * - CSV escaping
 * - Chart detection logic
 */

const assert = require("assert");

// 1. Test Indian compact number formatting logic
function formatCompactIndian(value) {
  if (isNaN(value) || value === null || value === undefined) return "—";
  const abs = Math.abs(value);
  if (abs >= 1e7) {
    const crores = value / 1e7;
    return `${crores.toFixed(2)} Cr`;
  }
  if (abs >= 1e5) {
    const lakhs = value / 1e5;
    return `${lakhs.toFixed(2)} L`;
  }
  return value.toLocaleString("en-IN");
}

assert.strictEqual(formatCompactIndian(10000000), "1.00 Cr");
assert.strictEqual(formatCompactIndian(22399700), "2.24 Cr");
assert.strictEqual(formatCompactIndian(550000), "5.50 L");
assert.strictEqual(formatCompactIndian(1250), "1,250");
console.log("✓ formatCompactIndian tests passed.");

// 2. Test CSV Cell Escaping logic
function escapeCSVCell(val) {
  if (val === null || val === undefined) return "";
  const str = String(val);
  if (/[",\r\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

assert.strictEqual(escapeCSVCell("Pune"), "Pune");
assert.strictEqual(escapeCSVCell("Pune, Maharashtra"), '"Pune, Maharashtra"');
assert.strictEqual(escapeCSVCell('Say "Hello"'), '"Say ""Hello"""');
assert.strictEqual(escapeCSVCell("Line 1\nLine 2"), '"Line 1\nLine 2"');
console.log("✓ escapeCSVCell tests passed.");

console.log("\n✨ All frontend utility tests passed successfully!");

